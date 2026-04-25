import json
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path

def check_firebase():
    cred_path = Path("cloud_run/firebase_credentials.json")
    if not cred_path.exists():
        print("Credentials not found!")
        return

    with open(cred_path, 'r', encoding='utf-8') as f:
        cred_dict = json.load(f)
    if 'private_key' in cred_dict:
        cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
    
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    
    print("--- COLLECTIONS ---")
    collections = db.collections()
    for coll in collections:
        print(f"Collection: {coll.id}")
        
        # Check document count (approx)
        docs = list(coll.limit(5).stream())
        print(f"  Found {len(docs)} documents (limited to 5 for preview)")
        for doc in docs:
            print(f"    Doc ID: {doc.id} => {doc.to_dict()}")
    
if __name__ == "__main__":
    check_firebase()
