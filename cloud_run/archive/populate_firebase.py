import os
import json
import time
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase with Windows newline fix
cred_path = os.path.join(os.path.dirname(__file__), 'firebase_credentials.json')
with open(cred_path, 'r', encoding='utf-8') as f:
    cred_dict = json.load(f)
if 'private_key' in cred_dict:
    cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')

cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

data_dir = r"E:\U_Hack_FormaOS-1\Data\Date - meciuri"

# Track matches for each team
team_matches = {}
team_names = set()

files = [f for f in os.listdir(data_dir) if f.endswith('.json') and "players_stats" in f]
print(f"Found {len(files)} match files.")

# Helper to normalize team names for ID generation
def clean_id(name):
    clean = name.lower()
    clean = clean.replace('ș', 's').replace('ț', 't').replace('ş', 's').replace('ţ', 't')
    clean = "".join([c for c in clean if c.isalnum() or c == ' ']).strip()
    return clean.replace(' ', '_')

# Parse all matches
for filename in files:
    filepath = os.path.join(data_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"Failed to parse {filename}")
            continue
            
    if not isinstance(data, dict) or 'players' not in data or len(data['players']) == 0:
        continue
        
    match_id = str(data['players'][0].get('matchId'))
    if not match_id or match_id == 'None':
        continue
        
    # Extract teams from filename (e.g., "Argeș - Botoşani, 0-0_players_stats.json")
    name_part = filename.split(',')[0]
    teams_split = name_part.split(' - ')
    if len(teams_split) == 2:
        team1 = teams_split[0].strip()
        team2 = teams_split[1].strip()
    else:
        team1 = "Unknown"
        team2 = "Unknown"
        
    if team1 != "Unknown":
        team_names.add(team1)
        if team1 not in team_matches:
            team_matches[team1] = set()
        team_matches[team1].add(match_id)
        
    if team2 != "Unknown":
        team_names.add(team2)
        if team2 not in team_matches:
            team_matches[team2] = set()
        team_matches[team2].add(match_id)
    
    # Write match document
    doc_ref = db.collection('matches').document(match_id)
    # Adding extra context so we can query easily later
    data['team1'] = team1
    data['team2'] = team2
    doc_ref.set(data)
    print(f"Uploaded match {match_id} ({team1} vs {team2})")
    time.sleep(1) # Delay to avoid rate limit

# Read existing teams mapping if available
known_teams = {}
teams_json_path = 'data/teams.json'
if os.path.exists(teams_json_path):
    with open(teams_json_path, 'r', encoding='utf-8') as f:
        known_data = json.load(f)
        for t in known_data:
            known_teams[clean_id(t['name'])] = t['id']

# Upload teams collection
for team_name in team_names:
    matches = team_matches.get(team_name, set())
    
    c_name = clean_id(team_name)
    # Check if we have an ID for it
    if c_name in known_teams:
        team_id = known_teams[c_name]
    else:
        team_id = c_name
        
    # Also manual overrides for specific names that might not match perfectly
    if 'fcs' in c_name and 'fcsb' in known_teams:
        team_id = known_teams['fcsb']
    elif 'dinamo' in c_name and 'dinamo_bucuresti' in known_teams:
        team_id = known_teams['dinamo_bucuresti']
    elif 'rapid' in c_name and 'rapid_bucuresti' in known_teams:
        team_id = known_teams['rapid_bucuresti']
        
    team_ref = db.collection('teams').document(team_id)
    
    # We update or set the team document
    # We use merge=True so we don't overwrite if it already has 'name' that we prefer
    team_ref.set({
        'id': team_id,
        'name': team_name,
        'matchIds': list(matches)
    }, merge=True)
    
    print(f"Uploaded team {team_name} (ID: {team_id}) with {len(matches)} matches")
    time.sleep(1) # Delay to avoid rate limit

print("Database sync complete!")
