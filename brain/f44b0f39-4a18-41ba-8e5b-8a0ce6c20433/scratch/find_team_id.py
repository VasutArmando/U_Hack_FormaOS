import json
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path

def get_ucluj_id():
    cred_path = Path("cloud_run/firebase_credentials.json")
    if not cred_path.exists(): return
    with open(cred_path, 'r', encoding='utf-8') as f:
        cred_dict = json.load(f)
    if 'private_key' in cred_dict:
        cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(cred_dict))
    
    db = firestore.client()
    
    # Search for a player from Universitatea Cluj
    # We know some player names like "Dancu" or "Nistor"
    docs = db.collection('players').limit(500).stream()
    
    teams = {}
    for doc in docs:
        p = doc.to_dict()
        tid = p.get('currentTeamId')
        # Check if current team is likely U Cluj based on player names
        # For example, Dan Nistor is at U Cluj (wyId 225338)
        if p.get('wyId') == 225338:
            print(f"Found Dan Nistor! Team ID: {tid}")
        
        # Collect team info
        if tid not in teams:
            teams[tid] = []
        teams[tid].append(p.get('shortName'))
        
    for tid, players in teams.items():
        if any("Nistor" in str(name) for name in players):
            print(f"Team {tid} contains Nistor. Players: {players[:5]}")

if __name__ == "__main__":
    get_ucluj_id()
