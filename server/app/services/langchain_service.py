from langchain_community.utilities import SQLDatabase
import langchain_core
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
        mysql_uri = f'mysql+mysqlconnector://{settings.MYSQL_DB_USER}:{settings.MYSQL_DB_PASSWORD}@{settings.MYSQL_DB_HOST}:{settings.MYSQL_DB_PORT}/{settings.MYSQL_DB}'
        db = SQLDatabase.from_uri(mysql_uri)
        return db
        
    @staticmethod
    def get_schema():
        db = LangchainAIService.connection()
        if hasattr(db, 'get_table_info'):
            schema = db.get_table_info(table_names=["service_snaps", "oshistory_detail"])
        else:
            raise TypeError("The provided 'db' object does not have the 'get_table_info' method.")
        return schema

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
        sql_chain, error_sql_chain, response_sql_chain = LangchainAIService.get_prompts_chain(query_template, 
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
                query = error_sql_chain.invoke({"question": question, "response": query, "error": str(e)})
                logger.warning(f"Retrying query... Attempt {attempt + 1} of {max_retries}")
                
    @staticmethod
    def truncate_response(response: str, max_tokens: int = 30) -> str:
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
        sql_chain, error_sql_chain, response_sql_chain = LangchainAIService.get_chains()
        
        # Generate the SQL query from the question
        query = sql_chain.invoke({"question": question})
        
        # Run the generated SQL query with retries
        try:
            response, query = LangchainAIService.run_query_with_retries(query, question)
            logger.info(f"response: {response}\ntype: {type(response)}")
            logger.debug(f"SQL Response: {response}\nNew Query: {query}")
            response = LangchainAIService.truncate_response(response)
            result = response_sql_chain.invoke({"question": question, "query": query, "response": response, "username": username})
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
