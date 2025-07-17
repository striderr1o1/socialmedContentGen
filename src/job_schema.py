from pydantic import BaseModel
import uuid
from datetime import datetime

class JobRequest(BaseModel):
    niche: str
    topic: str

def generate_job(niche, topic):
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    return job_id, {
        "job_id": job_id,
        "niche": niche,
        "topic": topic,
        "script": None,
        "voice_url": None,
        "video_url": None,
        "status": "created",
        "created_at": datetime.utcnow().isoformat()
    }
