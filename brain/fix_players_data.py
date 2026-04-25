import os
import json
import collections

data_dir = r"E:\U_Hack_FormaOS-1\Data_Fixed\Date - meciuri"

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
    most_common = collections.Counter(names).most_common(1)[0][0]
    final_teamid_mapping[tid] = most_common

# Step 3: Update players(1).json
resolved_count = 0
unresolved_count = 0

for p in players_data.get('players', []):
    pid = str(p.get('wyId'))
    tid = str(p.get('currentTeamId'))
    
    # Try exact intersection first
    teamname = player_to_teamname.get(pid)
    
    # Fallback to teamid mapping
    if not teamname and tid in final_teamid_mapping:
        teamname = final_teamid_mapping[tid]
        
    if teamname:
        p['teamname'] = teamname
        resolved_count += 1
    else:
        p['teamname'] = "Unknown"
        unresolved_count += 1

with open(players_json_path, 'w', encoding='utf-8') as f:
    json.dump(players_data, f, ensure_ascii=False, indent=2)

print(f"Successfully resolved and updated teamname for: {resolved_count} players.")
print(f"Unresolved players set to 'Unknown': {unresolved_count}")
