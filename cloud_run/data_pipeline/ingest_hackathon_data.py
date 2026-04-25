import os
import json
import zipfile
import sys
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

# Configurare Căi
ZIP_PATH = "c:/Users/vasut/Desktop/Date - meciuri-20250424T184517Z-001.zip"
LOCAL_DIR = Path("cloud_run/data/raw_json/Date - meciuri")

def init_firebase():
    cred_path = Path(__file__).parent.parent / "firebase_credentials.json"
    if not cred_path.exists():
        return None

    with open(cred_path, 'r', encoding='utf-8') as f:
        cred_dict = json.load(f)
    if 'private_key' in cred_dict:
        cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
    
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

def ingest_player_metadata(db):
    print("Ingesting player metadata...")
    players_file = LOCAL_DIR / "players (1).json"
    if not players_file.exists():
        return

    with open(players_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    players = data.get("players", []) if isinstance(data, dict) else data
    print(f"  Loaded {len(players)} players.")
    
    batch = db.batch()
    count = 0
    for player in players:
        if not isinstance(player, dict): continue
        pid = str(player.get("wyId"))
        doc_ref = db.collection('players').document(pid)
        batch.set(doc_ref, player)
        count += 1
        if count % 100 == 0:
            batch.commit()
            batch = db.batch()
            print(f"  Uploaded {count} profiles...")
    batch.commit()
    print(f"Done metadata: {count}")

def ingest_match_stats(db):
    print("Ingesting all match player statistics...")
    match_files = list(LOCAL_DIR.glob("*_players_stats.json"))
    print(f"Found {len(match_files)} match files.")

    batch = db.batch()
    total_count = 0
    
    for i, match_file in enumerate(match_files):
        try:
            with open(match_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                players = data.get("players", []) if isinstance(data, dict) else data
                    
                for p in players:
                    if not isinstance(p, dict): continue
                    mid = str(p.get("matchId"))
                    pid = str(p.get("playerId"))
                    doc_id = f"{mid}_{pid}"
                    
                    batch.set(db.collection('match_player_stats').document(doc_id), p)
                    total_count += 1
                    
                    if total_count % 100 == 0:
                        batch.commit()
                        batch = db.batch()
            
            if (i + 1) % 50 == 0:
                print(f"  Processed {i+1} / {len(match_files)} match files...")
                
        except Exception:
            pass
                
    batch.commit()
    print(f"Done match stats: {total_count}")

def main():
    db = init_firebase()
    if not db: 
        print("Firebase init failed.")
        return

    print("--- LITERALLY ALL DATA INGESTION ---")
    ingest_player_metadata(db)
    ingest_match_stats(db)
    print("SUCCESS.")

if __name__ == "__main__":
    main()
