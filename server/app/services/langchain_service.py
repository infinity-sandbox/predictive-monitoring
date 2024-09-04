from datetime import datetime
from langchain_community.utilities import SQLDatabase
import langchain_core
import pandas as pd
from app.core.config import settings
from app.services.openai_service import OpenAIService
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
import os
from logs.loggers.logger import logger_config
logger = logger_config(__name__)
import tiktoken

llm = ChatOpenAI(openai_api_key=settings.OPENAI_API_KEY)

class LangchainAIService(OpenAIService):
    @staticmethod
    def connection():
        mysql_uri = f'mysql+mysqlconnector://' \
        f'{settings.MYSQL_DB_USER}' \
        f':{settings.MYSQL_DB_PASSWORD}' \
        f'@{settings.MYSQL_DB_HOST}' \
        f':{settings.MYSQL_DB_PORT}' \
        f'/{settings.MYSQL_DB}'
        db = SQLDatabase.from_uri(mysql_uri)
        return db
        
    @staticmethod
    def get_schema():
        db = LangchainAIService.connection()
        if hasattr(db, 'get_table_info'):
            schema = db.get_table_info(table_names=['synth_txn',
                                                    'alert_queue', 
                                                    'eum_summary_day', 
                                                    'eum_visits', 
                                                    'http_errors',
                                                    'oshistory_detail'])
        else:
            raise TypeError("The provided 'db' object does not have the 'get_table_info' method.")
        schema = LangchainAIService.truncate_response(schema, 90000)
        logger.warning(f'SCHEMA: {schema}')
        return schema
    
    @staticmethod
    async def problem_detection():
        logger.info("Detecting problems...")
        from app.services.multivariate_timeseries import MultivariateTimeSeries
        df = MultivariateTimeSeries.connect_db()
        # Sort the DataFrame by the 'rl' column in descending order
        sorted_df = df.sort_values(by='rl', ascending=False)
        
        # Get the last 3 rows of the sorted DataFrame
        last_three_rows = sorted_df.head(3)
        issues = await MultivariateTimeSeries.send_signal(last_three_rows)
        logger.info(f"Issues detected: {issues}")
        return issues
    
    @staticmethod
    async def if_anomaly():
        # Check if the dictionary itself is empty
        data_dict = await LangchainAIService.problem_detection()
        if not data_dict:
            logger.debug("The dictionary is empty.")
            return False, data_dict

        # Check if all the lists inside the dictionary are empty
        all_lists_empty = all(not value for value in data_dict.values())

        if all_lists_empty:
            logger.warning("All lists in the dictionary are empty. (no issues detected)")
            return False, data_dict
        else:
            logger.warning("The dictionary is not empty and not all lists are empty. " \
                           "(Problem detected)")
            return True, data_dict
        
    @staticmethod
    async def if_cause():
        # Check if the dictionary itself is empty
        data_dict = await LangchainAIService.problem_detection()
        if not data_dict:
            logger.debug("The dictionary is empty.")
            return False, data_dict

        # Check if all the lists inside the dictionary are empty
        all_lists_empty = all(not value for value in data_dict.values())

        if all_lists_empty:
            logger.warning("All lists in the dictionary are empty. (no issues detected)")
            return False, data_dict
        else:
            logger.warning("The dictionary is not empty and not all lists are empty. " \
                           "(Problem detected)")
            return True, data_dict
        
    @staticmethod
    def get_prompts_chain(query_template, response_template, error_query_template):
        query_prompt = ChatPromptTemplate.from_template(query_template)
        response_prompt = ChatPromptTemplate.from_template(response_template)
        error_prompt = ChatPromptTemplate.from_template(error_query_template)
        # Create the SQL chain
        schema = LangchainAIService.get_schema()
        sql_chain = (
            RunnablePassthrough.assign(schema=lambda _: schema)
            | query_prompt
            | llm.bind(stop=["\nSQLResult:"])
            | StrOutputParser()
        )

        # Create the SQL chain
        error_sql_chain = (
            RunnablePassthrough.assign(schema=lambda _: schema)
            | error_prompt
            | llm.bind(stop=["\nSQLResult:"])
            | StrOutputParser()
        )

        # Create the SQL chain
        response_sql_chain = (
            RunnablePassthrough.assign(schema=lambda _: schema)
            | response_prompt
            | llm.bind(stop=["\nSQLResult:"])
            | StrOutputParser()
        )
        return sql_chain, error_sql_chain, response_sql_chain

    @staticmethod
    def run_query(query):
        db = LangchainAIService.connection()
        return db.run(query)
    
    @staticmethod
    def read_prompt(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logger.error(f"File {file_path} not found.")
        except Exception as e:
            logger.error(f"An error occurred while reading {file_path}: {e}")
            
    def get_chains():
        PROMPT_PATH_ERROR=os.path.join(settings.PROMPT_DIR, "error_query_template.txt")
        PROMPT_PATH_QUERY=os.path.join(settings.PROMPT_DIR, "query_template.txt")
        PROMPT_PATH_RESPONSE=os.path.join(settings.PROMPT_DIR, "response_template.txt")
        #
        query_template = LangchainAIService.read_prompt(PROMPT_PATH_QUERY)
        response_template = LangchainAIService.read_prompt(PROMPT_PATH_RESPONSE)
        error_query_template = LangchainAIService.read_prompt(PROMPT_PATH_ERROR)
        #
        (sql_chain, 
         error_sql_chain, 
         response_sql_chain) = LangchainAIService.get_prompts_chain(query_template,
                                                                    response_template, 
                                                                    error_query_template)
        return sql_chain, error_sql_chain, response_sql_chain

    @staticmethod
    def run_query_with_retries(query, question, max_retries=5):
        attempt = 0
        sql_chain, error_sql_chain, response_sql_chain = LangchainAIService.get_chains()
        while attempt < max_retries:
            try:
                response = LangchainAIService.run_query(query)
                return response, query # Exit the loop if the query succeeds
            except Exception as e:
                logger.error(f"Error running query: {e}")
                if attempt >= max_retries - 1:
                    raise  # Raise the exception if the maximum retries have been reached
                attempt += 1
                if attempt == 5:
                    logger.error(f"Maximum retries reached. Exiting...")
                    return "I don't know the answer or answer not found", "None"
                # Generate a new query based on the error
                query = error_sql_chain.invoke({"question": question, 
                                                "response": query, "error": str(e)})
                logger.warning(f"Retrying query... Attempt {attempt + 1} of {max_retries}")
                
    @staticmethod
    def truncate_response(response: str, max_tokens: int = 100) -> str:
        # Initialize the tokenizer
        tokenizer = tiktoken.get_encoding("cl100k_base")

        # Tokenize the response
        tokens = tokenizer.encode(response)

        # Truncate tokens if necessary
        if len(tokens) > max_tokens:
            logger.warning(f"Truncating response from {len(tokens)} tokens to {max_tokens} tokens.")
            tokens = tokens[:max_tokens]
            # Decode tokens back to a string
            response = tokenizer.decode(tokens)
        return response
    
    @staticmethod
    async def full_chain(question: str, username: str) -> str:
        #TODO: async process for dashboard, chat, and anomaly detection (from the frontend)
        #FIXME: don't only run the loop when the home page is clicked, run it when the user logs in
        #TODO: add demoable features to the chat
        if await OpenAIService.classify(question) == "problem":
            try:
                is_anomaly, issues = await LangchainAIService.if_anomaly()
                if is_anomaly:
                    non_empty_issues = {key: value for key, value in issues.items() if value}
                    
                    def convert_unix_timestamps(values):
                        return [
                            datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') 
                            for ts in values]
                    formatted_issues = {key for key, value in non_empty_issues.items()}
                    return await OpenAIService.respond(question, formatted_issues, 'problem')
                else:
                    return f"No issues have been detected so far, {username}."
            except Exception as e:
                logger.error(f"Error getting response: {e}")
                return f"Error getting response: {e}"
        elif await OpenAIService.classify(question) == "cause":
            try:
                is_anomaly, issues = await LangchainAIService.if_anomaly()
                if is_anomaly:
                    non_empty_keys = [key for key, value in issues.items() if value]
                    from app.services.multivariate_timeseries import MultivariateTimeSeries
                    feature_importances_dict = await MultivariateTimeSeries._feature_selection(
                        non_empty_keys[0])
                    return await OpenAIService.respond(
                        question, feature_importances_dict['features'][:3], 'cause')
                else:
                    return f"No causes have been detected so far, {username}."
            except Exception as e:
                logger.error(f"Error getting response: {e}")
                return f"Error getting response: {e}"
        elif await OpenAIService.classify(question) == "fix":
            try:
                is_anomaly, issues = await LangchainAIService.if_anomaly()
                if is_anomaly:
                    non_empty_issues = {key: value for key, value in issues.items() if value}
                    formatted_issues = {key for key, value in non_empty_issues.items()}
                    return await OpenAIService.respond(question, formatted_issues, 'fix')
                else:
                    return f"No issues have been detected so far, {username}."
            except Exception as e:
                logger.error(f"Error getting response: {e}")
                return f"Error getting response: {e}"
        else:
            sql_chain, error_sql_chain, response_sql_chain = LangchainAIService.get_chains()
            
            # Generate the SQL query from the question
            query = sql_chain.invoke({"question": question})
            
            # Run the generated SQL query with retries
            try:
                response, query = LangchainAIService.run_query_with_retries(query, question)
                logger.info(f"response: {response}\ntype: {type(response)}")
                logger.debug(f"SQL Response: {response}\nNew Query: {query}")
                response = LangchainAIService.truncate_response(response)
                result = response_sql_chain.invoke({"question": question, "query": query, 
                                                    "response": response, "username": username})
                result = str(result)
                logger.debug(f"Natural Language Response: {result}")
                return result
            # Generate the natural language response using the response_prompt
            except Exception as e:
                logger.error(f"Error getting response: {e}")
                return f"Error getting response: {e}"
            
if __name__ == "__main__":
    # Example user question
    user_question = "When does the minimum cpu connection occured?"
    logger.debug(LangchainAIService.full_chain(user_question))
