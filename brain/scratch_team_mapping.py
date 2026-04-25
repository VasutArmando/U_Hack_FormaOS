import os
import json
import collections
import sys

sys.stdout.reconfigure(encoding='utf-8')

data_dir = r"E:\U_Hack_FormaOS-1\Data\Date - meciuri"

# Step 1: Find intersections to determine player -> Team Name
player_teams = collections.defaultdict(list)

for filename in os.listdir(data_dir):
    if not filename.endswith("players_stats.json"):
        continue
    name_part = filename.split(',')[0]
    teams_split = name_part.split(' - ')
    if len(teams_split) != 2:
        continue
    team1 = teams_split[0].strip()
    team2 = teams_split[1].strip()
    
    filepath = os.path.join(data_dir, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'players' in data:
                for p in data['players']:
                    pid = str(p.get('playerId'))
                    player_teams[pid].append({team1, team2})
    except Exception as e:
        pass

player_to_teamname = {}
for pid, match_teams_list in player_teams.items():
    possible_teams = set.intersection(*match_teams_list) if match_teams_list else set()
    if len(possible_teams) == 1:
        player_to_teamname[pid] = list(possible_teams)[0]

# Step 2: Correlate player -> Team Name with currentTeamId in players(1).json
players_json_path = os.path.join(data_dir, "players (1).json")
teamid_to_teamname = collections.defaultdict(list)

with open(players_json_path, 'r', encoding='utf-8') as f:
    players_data = json.load(f)
    for p in players_data.get('players', []):
        pid = str(p.get('wyId'))
        tid = str(p.get('currentTeamId'))
        
        if pid in player_to_teamname and tid and tid != 'None':
            teamid_to_teamname[tid].append(player_to_teamname[pid])

final_teamid_mapping = {}
for tid, names in teamid_to_teamname.items():
    # Most common team name for this ID
    most_common = collections.Counter(names).most_common(1)[0][0]
    final_teamid_mapping[tid] = most_common

print("Resolved Team ID to Team Name Mapping:")
for tid, name in final_teamid_mapping.items():
    print(f"Team ID {tid} -> {name}")

# Inject teamname into the players dataset
for p in players_data.get('players', []):
    tid = str(p.get('currentTeamId'))
    if tid in final_teamid_mapping:
        p['teamname'] = final_teamid_mapping[tid]

# Write back to Data directory
with open(players_json_path, 'w', encoding='utf-8') as f:
    json.dump(players_data, f, ensure_ascii=False, indent=2)

print(f"Injected teamname into {players_json_path}")

# Also inject into Data_Fixed directory
data_fixed_dir = r"E:\U_Hack_FormaOS-1\Data_Fixed\Date - meciuri"
players_fixed_path = os.path.join(data_fixed_dir, "players (1).json")
if os.path.exists(players_fixed_path):
    with open(players_fixed_path, 'r', encoding='utf-8') as f:
        fixed_data = json.load(f)
    for p in fixed_data.get('players', []):
        tid = str(p.get('currentTeamId'))
        if tid in final_teamid_mapping:
            p['teamname'] = final_teamid_mapping[tid]
    with open(players_fixed_path, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
    print(f"Injected teamname into {players_fixed_path}")
