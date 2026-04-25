import json
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path

def count_docs():
    cred_path = Path("cloud_run/firebase_credentials.json")
    if not cred_path.exists(): return
    with open(cred_path, 'r', encoding='utf-8') as f:
        cred_dict = json.load(f)
    if 'private_key' in cred_dict:
        cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(cred_dict))
    
    db = firestore.client()
    
    # Approx count using stream and limit (or just metadata if possible)
    # Since we can't get count directly without aggregation queries (which might not be enabled),
    # we just take a snapshot of a few.
    docs = list(db.collection('match_player_stats').limit(1).stream())
    if docs:
        print(f"Collection 'match_player_stats' exists and has documents.")
    else:
        print("Collection 'match_player_stats' is empty.")

if __name__ == "__main__":
    count_docs()
