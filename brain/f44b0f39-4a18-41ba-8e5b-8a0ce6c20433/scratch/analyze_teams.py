import json
from pathlib import Path
from collections import Counter

def analyze_teams():
    players_file = Path("cloud_run/data/raw_json/Date - meciuri/players (1).json")
    if not players_file.exists():
        print("File not found.")
        return

    with open(players_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    players = data.get("players", []) if isinstance(data, dict) else data
    
    team_counts = Counter()
    for p in players:
        tid = p.get("currentTeamId")
        team_counts[tid] += 1
    
    print("Top Team IDs by player count:")
    for tid, count in team_counts.most_common(30):
        # Find a sample player name for this team
        sample_player = next((p.get("shortName") for p in players if p.get("currentTeamId") == tid), "Unknown")
        # Clean name for safe printing
        safe_name = sample_player.encode('ascii', 'ignore').decode('ascii')
        print(f"Team ID: {tid}, Players: {count}, Sample: {safe_name}")

if __name__ == "__main__":
    analyze_teams()
