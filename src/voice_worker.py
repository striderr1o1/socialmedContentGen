import os
import requests
import time
from firebase_utils import get_job, update_job_status
from redis_utils import r
from dotenv import load_dotenv
from elevenlabs import play
load_dotenv()

API_KEY = os.getenv("ELEVEN_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")
OUTPUT_DIR = "audio_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
        
    return audio_path  # You can later upload to S3 or Firebase Storage

def process_voice_jobs():
    print("Voice worker started...")
    while True:
        try:
            job_id = r.brpop("voice_queue", timeout=5)
            if job_id:
                job_id = job_id[1].decode()
                print(f"Processing voice for job: {job_id}")

                job_data = get_job(job_id)
                if not job_data or not job_data.get("script"):
                    print(f"Missing job/script for {job_id}")
                    continue

                script = job_data["script"]
                audio_path = generate_voice(script, job_id)

                update_job_status(job_id, {
                    "voice_url": audio_path,
                    "status": "voice_done"
                })

                r.lpush("video_queue", job_id)
                print(f"Voice done for {job_id}, pushed to video_queue")

        except Exception as e:
            print("Error in voice worker:", e)
            time.sleep(2)

if __name__ == "__main__":
    process_voice_jobs()
