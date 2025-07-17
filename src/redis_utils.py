import redis

r = redis.Redis(host='localhost', port=6379, db=0)

def push_to_queue(queue_name, job_id):
    r.lpush(queue_name, job_id)


