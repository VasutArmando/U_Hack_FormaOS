import json
import os
from collections import defaultdict

# Path to the matches data
matches_dir = r"c:\Users\vasut\Desktop\FormaOS\U_Hack_FormaOS\Data_Fixed\Date - meciuri"
players_file = r"c:\Users\vasut\Desktop\FormaOS\U_Hack_FormaOS\Data_Fixed\Date - meciuri\players (1).json"

# Load players database
with open(players_file, 'r', encoding='utf-8') as f:
    players_db = json.load(f)['players']

# wyId to Player Object mapping
player_map = {p['wyId']: p for p in players_db}

# Minutes counter: team -> player_id -> total_minutes
team_player_minutes = defaultdict(lambda: defaultdict(int))

# Iterate matches
for filename in os.listdir(matches_dir):
    if filename.endswith("_players_stats.json"):
        with open(os.path.join(matches_dir, filename), 'r', encoding='utf-8') as f:
            data = json.load(f)
            for p_stat in data.get('players', []):
                p_id = p_stat.get('playerId')
                minutes = p_stat.get('total', {}).get('minutesOnField', 0)
                
                # Find team from players_db
                p_info = player_map.get(p_id)
                if p_info:
                    team = p_info.get('teamname')
                    if team:
                        team_player_minutes[team][p_id] += minutes

# Generate Top 11 for the 6 target teams
target_teams = {
    "Oțelul Galați": ["Ot\u0327elul", "Otelul"],
    "Dinamo București": ["Dinamo Bucures\u0327ti", "Dinamo"],
    "Farul Constanța": ["Farul Constant\u0327a", "Farul"],
    "Universitatea Craiova": ["Universitatea Craiova", "Craiova"],
    "FCSB": ["FCS Bucures\u0327ti", "FCSB"],
    "Hermannstadt": ["Hermannstadt"]
}

refined_lineups = {}

for label, variants in target_teams.items():
    # Sum minutes for all variants of team name
    combined_minutes = defaultdict(int)
    for team_name, players in team_player_minutes.items():
        if any(v.lower() in team_name.lower() for v in variants):
            for pid, mins in players.items():
                combined_minutes[pid] += mins
    
    # Sort players by minutes
    sorted_players = sorted(combined_minutes.items(), key=lambda x: x[1], reverse=True)
    
    # Take top 11
    top_11 = []
    for pid, mins in sorted_players[:11]:
        p_info = player_map.get(pid)
        if p_info:
            top_11.append({
                "name": f"{p_info['firstName']} {p_info['lastName']}",
                "position": p_info['role']['name']
            })
    
    refined_lineups[label] = top_11

# Save to a new starting11_fixed.json
output_file = r"c:\Users\vasut\Desktop\FormaOS\U_Hack_FormaOS\flutter_app\assets\mock_data\starting11.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(refined_lineups, f, indent=2, ensure_ascii=False)

print("Refined starting11.json based on match minutes.")
