from openai import OpenAI
from app.core.config import settings
from pydub import AudioSegment
import subprocess
from logs.loggers.logger import logger_config
logger = logger_config(__name__)
import os, sys
from math import exp
import numpy as np
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class OpenAIService:
    @staticmethod
    async def speech_to_text(audio_data):
        with open(audio_data, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                response_format="text",
                file=audio_file
            )
        return transcript

    @staticmethod
    async def text_to_speech(input_text: str, webm_file_path: str, wav_file_path: str):
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=input_text
        )
        with open(webm_file_path, "wb") as f:
            response.stream_to_file(webm_file_path)
        # convert webm to wav
        try:
            # Load the WebM file
            audio = AudioSegment.from_file(webm_file_path, format="webm")
            # Export as WAV file
            audio.export(wav_file_path, format="wav")
        except Exception as e:
            logger.error(f"Failed to convert {webm_file_path} to WAV: {e}")
            # Optionally, run ffmpeg manually to debug
            command = [
                'ffmpeg',
                '-i', webm_file_path,
                wav_file_path
            ]
            try:
                subprocess.run(command, check=True, capture_output=True, text=True)
                logger.info(f"ffmpeg command executed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"ffmpeg command failed: {e.stderr}")
        return wav_file_path
    
    @staticmethod
    async def get_completion(
        messages: list[dict[str, str]],
        model: str = settings.MODEL,
        max_tokens=500,
        temperature=0,
        stop=None,
        seed=123,
        tools=None,
        logprobs=None,
        top_logprobs=None,
    ) -> str:
        '''
        params: 

        messages: list of dictionaries with keys 'role' and 'content'.
        model: the model to use for completion. Defaults to 'davinci'.
        max_tokens: max tokens to use for each prompt completion.
        temperature: the higher the temperature, the crazier the text
        stop: token at which text generation is stopped
        seed: random seed for text generation
        tools: list of tools to use for post-processing the output.
        logprobs: whether to return log probabilities of the output tokens or not. 
        '''
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stop": stop,
            "seed": seed,
            "logprobs": logprobs,
            "top_logprobs": top_logprobs,
        }
        if tools:
            params["tools"] = tools

        completion = client.chat.completions.create(**params)
        logger.info(f"Completion Generated!")
        return completion
    
    @staticmethod
    async def respond(query: str, payload: str, flag: str) -> str:
        try:
            if flag == 'problem':
                PROMPT_PATH=os.path.join(settings.PROMPT_DIR, "admin_response/problem_template.txt")
            elif flag == 'cause':
                PROMPT_PATH=os.path.join(settings.PROMPT_DIR, "admin_response/cause_template.txt")
            elif flag == 'fix':
                PROMPT_PATH=os.path.join(settings.PROMPT_DIR, "admin_response/fix_template.txt")
            else:
                PROMPT_PATH=os.path.join(settings.PROMPT_DIR, "admin_response.txt")
            with open(PROMPT_PATH, "r") as file:
                PROMPT = file.read()
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise FileNotFoundError(f"File not found: {e}")
        API_RESPONSE = await OpenAIService.get_completion(
            [{"role": "system", "content": PROMPT.format(question=query, payload=payload)}],
            model=settings.MODEL
        )
        system_msg = str(API_RESPONSE.choices[0].message.content)
        return system_msg
    
    
    @staticmethod
    async def classify(user_message: str) -> str:
        try:
            PROMPT_PATH=os.path.join(settings.PROMPT_DIR, "classification_template.txt")
            with open(PROMPT_PATH, "r") as file:
                PROMPT = file.read()
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise FileNotFoundError(f"File not found: {e}")
        API_RESPONSE = await OpenAIService.get_completion(
            [{"role": "user", "content": PROMPT.format(user_message=user_message)}],
            model=settings.MODEL,
            logprobs=True,
            top_logprobs=1
        )
        top_three_logprobs = API_RESPONSE.choices[0].logprobs.content[0].top_logprobs
        content = ""
        system_msg = str(API_RESPONSE.choices[0].message.content)

        for i, logprob in enumerate(top_three_logprobs, start=1):
            linear_probability = np.round(np.exp(logprob.logprob) * 100, 2)
            if logprob.token in ["problem", "cause", "fix"] and linear_probability >= 95.00:
                content += (
                    f"\n"
                    f"output token {i}: {system_msg},\n"
                    f"logprobs: {logprob.logprob}, \n"
                    f"linear probability: {linear_probability} \n"
                )
                logger.debug(f"{content} \nclassification: {logprob.token}")
                classification = str(system_msg)
            else:
                classification = ""
                logger.warning(f"classification: {classification}, logprobs confidence is less than 95%.")
        return classification
    
    