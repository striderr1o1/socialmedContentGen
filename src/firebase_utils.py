import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

load_dotenv()

cred_path = "../firebase_creds.json"
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

db = firestore.client()

def save_job_to_firestore(job_id, job_data):
    db.collection("jobs").document(job_id).set(job_data)

# def update_job_status(job_id, updates: dict):
#     db.collection("jobs").document(job_id).update(updates)
def update_job_status(job_id, update_dict):
    try:
        print(f"Updating job {job_id} with {update_dict}")  # Debug print
        # Assuming Firestore:
        db.collection("jobs").document(job_id).update(update_dict)
        print(f"Update successful for job {job_id}")
    except Exception as e:
        print(f"Error updating job {job_id}: {e}")
        
def get_job(job_id):
    return db.collection("jobs").document(job_id).get().to_dict()
