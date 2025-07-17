
from fastapi import FastAPI
from job_schema import JobRequest, generate_job
from redis_utils import push_to_queue
from firebase_utils import save_job_to_firestore


app = FastAPI()

@app.post("/submit_job")
def submit_job(job: JobRequest):
    job_id, job_data = generate_job(job.niche, job.topic)
    save_job_to_firestore(job_id, job_data)
    push_to_queue("script_queue", job_id)
    return {"message": "Job submitted", "job_id": job_id}


