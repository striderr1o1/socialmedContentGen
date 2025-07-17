import time
from firebase_utils import get_job, update_job_status
from redis_utils import r

def fake_script_generator(topic):
    # Simulate GPT-5 style emotional script
    return f"Discipline is doing what needs to be done even when you don't feel like it. {topic} can change your life."

def process_script_jobs():
    print("Script worker started. Listening for jobs...")
    while True:
        try:
            job_id = r.brpop("script_queue", timeout=5)  # blocking pop
            if job_id:
                job_id = job_id[1].decode()
                print(f"Picked up job: {job_id}")
                
                job_data = get_job(job_id)
                if not job_data:
                    print("Job not found in Firebase")
                    continue
                
                topic = job_data.get("topic")
                script = fake_script_generator(topic)

                # Update Firebase
                update_job_status(job_id, {
                    "script": script,
                    "status": "script_done"
                })

                # Push to voice queue
                r.lpush("voice_queue", job_id)
                print(f"Job {job_id} processed and sent to voice_queue")

        except Exception as e:
            print("Error:", e)
            time.sleep(2)  # retry delay

if __name__ == "__main__":
    process_script_jobs()
