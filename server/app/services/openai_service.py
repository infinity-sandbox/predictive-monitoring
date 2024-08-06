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
    async def chatbot(username: str, query: str) -> str:
        try:
            PROMPT_PATH=os.path.join(settings.PROMPT_DIR, "chatbot_prompt.txt")
            with open(PROMPT_PATH, "r") as file:
                PROMPT = file.read()
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise FileNotFoundError(f"File not found: {e}")
        API_RESPONSE = await OpenAIService.get_completion(
            [{"role": "system", "content": PROMPT.format(username=username, query=query)}],
            model=settings.MODEL
        )
        system_msg = str(API_RESPONSE.choices[0].message.content)
        return system_msg
    
    