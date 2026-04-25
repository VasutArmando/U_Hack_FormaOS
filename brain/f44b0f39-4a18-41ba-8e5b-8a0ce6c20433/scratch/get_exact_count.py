import json
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path

def get_exact_count():
    cred_path = Path("cloud_run/firebase_credentials.json")
    if not cred_path.exists(): return
    with open(cred_path, 'r', encoding='utf-8') as f:
        cred_dict = json.load(f)
    if 'private_key' in cred_dict:
        cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(cred_dict))
    
    db = firestore.client()
    
    # Using a simple aggregation query if supported, or just sampling
    coll_ref = db.collection('match_player_stats')
    
    # We'll just count how many we can get in 5 seconds
    count = 0
    docs = coll_ref.select([]).stream() # Only select ID to save bandwidth
    for _ in docs:
        count += 1
        if count % 1000 == 0:
            print(f"Counted so far: {count}")
    
    print(f"TOTAL COUNT: {count}")

if __name__ == "__main__":
    get_exact_count()
