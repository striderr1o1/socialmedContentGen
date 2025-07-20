import os
import openai
from openai import OpenAI
import requests
import time
from firebase_utils import get_job, update_job_status
from redis_utils import r
from dotenv import load_dotenv
from elevenlabs import play
import re
from tenacity import retry, stop_after_attempt, wait_fixed
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

API_KEY = os.getenv("ELEVEN_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")
OUTPUT_DIR = "audio_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# prompt = """Check the audio for errors in voice"""

def clean_script(text: str) -> str:
    """
    Removes punctuation such as commas, dashes, underscores, asterisks, quotes, etc. from the input text.
    """
    return re.sub(r'[\-,_\*"\'\'\(\)\[\]\{\}\:;\.!\?]', '', text)

# @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def generate_voice(script_text, job_id):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": script_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.75
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"ElevenLabs API failed: {response.text}")

    audio_path = f"{OUTPUT_DIR}/{job_id}.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.content)
    
    # text = send_audio_to_Transcriptor(audio_path)
    
    # audio_path2 = turn_to_voice_second(text+"Mein pakistan hun", job_id)  
    return audio_path  # You can later upload to S3 or Firebase Storage


# def send_audio_to_Transcriptor(audio_path):
#     client = OpenAI()
#     audio_file = open(audio_path, "rb")

#     transcription = client.audio.transcriptions.create(
#       file=audio_file,
#       model="whisper-1",
#       response_format="verbose_json",
#       timestamp_granularities=["word"]
#       )
#     generated_text = transcription.words
    
#     return generated_text

# def turn_to_voice_second(text, job_id):
#     url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

#     headers = {
#         "xi-api-key": API_KEY,
#         "Content-Type": "application/json"
#     }

#     payload = {
#         "text": text,
#         "model_id": "eleven_multilingual_v2",
#         "voice_settings": {
#             "stability": 0.4,
#             "similarity_boost": 0.75
#         }
#     }
#     response = requests.post(url, json=payload, headers=headers)

#     if response.status_code != 200:
#         raise Exception(f"ElevenLabs API failed: {response.text}")

#     audio_path = f"{OUTPUT_DIR}/{job_id}.mp3"
#     with open(audio_path, "wb") as f:
#         f.write(response.content)
#     return audio_path


def process_voice_jobs():
    logger.info("Voice worker started...")
    while True:
        try:
            job_id = r.brpop("voice_queue", timeout=5)
            if job_id:
                job_id = job_id[1].decode()
                logger.info(f"Processing voice for job: {job_id}")

                job_data = get_job(job_id)
                if not job_data or not job_data.get("script"):
                    logger.info(f"Missing job/script for {job_id}")
                    continue

                script = job_data["script"]
                cleaned_script = clean_script(script)
                audio_path= generate_voice(cleaned_script, job_id)
                
                update_job_status(job_id, {
                    "voice_url": audio_path,
                    "status": "voice_done"
                })

                r.lpush("video_queue", job_id)
                logger.info(f"Voice done for {job_id}, pushed to video_queue")

        except Exception as e:
            logger.error("Error in voice worker:", e)
            time.sleep(2)

if __name__ == "__main__":
    process_voice_jobs()
