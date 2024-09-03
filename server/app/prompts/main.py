import os, re
from logs.loggers.logger import logger_config
logger = logger_config(__name__)

class Prompt:
    BASE_PATH = 'app/prompts/tx'
    
    @staticmethod
    def read_prompt(prompt_name) -> str:
        try:
            PROMPT_PATH = os.path.join(Prompt.BASE_PATH, f'{prompt_name}.txt')
            with open(PROMPT_PATH, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logger.error(f"File {PROMPT_PATH} not found.")
        except Exception as e:
            logger.error(f"An error occurred while reading {PROMPT_PATH}: {e}")
    
    @staticmethod
    def read_prompt_full(prompt_name: str, **kwargs) -> str:
        prompt_text = Prompt.read_prompt(prompt_name)
        if prompt_text:  # Proceed only if the prompt was successfully read
            try:
                return prompt_text.format(**kwargs)
            except KeyError as e:
                logger.error(f"Error: Missing key {e} in formatting arguments.")
                return ""
            except Exception as e:
                logger.error(f"An error occurred during formatting: {e}")
                return ""
        return ""
    
    @staticmethod
    def update_prompt(prompt_name, prompt_text) -> None:
        try:
            PROMPT_PATH = os.path.join(Prompt.BASE_PATH, f'{prompt_name}.txt')
            with open(PROMPT_PATH, 'w', encoding='utf-8') as file:
                file.write(prompt_text)
        except FileNotFoundError:
            logger.error(f"File {PROMPT_PATH} not found.")
        except Exception as e:
            logger.error(f"An error occurred while updating {PROMPT_PATH}: {e}")
    
    @staticmethod
    def save_prompt(prompt_name, prompt_text) -> None:
        try:
            PROMPT_PATH = os.path.join(Prompt.BASE_PATH, f'{prompt_name}.txt')
            with open(PROMPT_PATH, 'w', encoding='utf-8') as file:
                file.write(prompt_text)
        except FileNotFoundError:
            logger.error(f"File {PROMPT_PATH} not found.")
        except Exception as e:
            logger.error(f"An error occurred while saving {PROMPT_PATH}: {e}")
            
    @staticmethod
    def get_prompt(prompt_name) -> str:
        try:
            PROMPT_PATH = os.path.join(Prompt.BASE_PATH, f'{prompt_name}.txt')
            return PROMPT_PATH
        except Exception as e:
            logger.error(f"An error occurred while getting {PROMPT_PATH} path: {e}")
    
    @staticmethod
    def delete_prompt(prompt_name) -> None:
        try:
            PROMPT_PATH = os.path.join(Prompt.BASE_PATH, f'{prompt_name}.txt')
            os.remove(PROMPT_PATH)
        except FileNotFoundError:
            logger.error(f"File {PROMPT_PATH} not found.")
        except Exception as e:
            logger.error(f"An error occurred while deleting {PROMPT_PATH}: {e}")
            
    @staticmethod
    def create_prompt(prompt_name, prompt_text) -> None:
        try:
            PROMPT_PATH = os.path.join(Prompt.BASE_PATH, f'{prompt_name}.txt')
            # Create the directory path if it doesn't exist
            os.makedirs(os.path.dirname(PROMPT_PATH), exist_ok=True)
            with open(PROMPT_PATH, 'w', encoding='utf-8') as file:
                file.write(prompt_text)
        except FileNotFoundError:
            logger.error(f"File {PROMPT_PATH} not found.")
        except Exception as e:
            logger.error(f"An error occurred while creating and writting {PROMPT_PATH}: {e}")
            
    @staticmethod
    def list_prompts() -> list:
        try:
            return os.listdir(Prompt.BASE_PATH)
        except FileNotFoundError:
            logger.error(f"Directory {Prompt.BASE_PATH} not found.")
        except Exception as e:
            logger.error(f"An error occurred while listing {Prompt.BASE_PATH}: {e}")
            
    @staticmethod
    def search_prompts(prompt_name) -> list:
        # Compile regex pattern to match prompt_name anywhere in the name and optionally end with .txt
        pattern = re.compile(rf'.*{re.escape(prompt_name)}.*(?:\.txt)?', re.IGNORECASE)
        
        matches = []
        try:
            # Traverse directory recursively
            for root, dirs, files in os.walk(Prompt.BASE_PATH):
                # Search in directories
                matches.extend([os.path.join(root, dir) for dir in dirs if pattern.match(dir)])
                # Search in files
                matches.extend([os.path.join(root, file) for file in files if pattern.match(file)])
                
        except FileNotFoundError:
            print(f"Directory {Prompt.BASE_PATH} not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
        
        return matches
            
    
    

            
 
            
            
            
            
            
            

    
    '''
    UPGRADE: GET PROMPT BY ID
    UPGRADE: GET PROMPT BY NAME
    UPGRADE: GET PROMPT BY CATEGORY
    UPGRADE: GET PROMPT BY TYPE
    UPGRADE: GET PROMPT BY LANGUAGE
    UPGRADE: GET PROMPT BY VERSION
    UPGRADE: GET PROMPT BY RATING
    UPGRADE: GET PROMPT BY LIKES
    UPGRADE: GET PROMPT BY DISLIKES
    UPGRADE: GET PROMPT BY URL
    UPGRADE: GET PROMPT BY PATH
    '''
    