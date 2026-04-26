import json

def sync_teams():
    # Load players to get team names
    with open(r'c:\Users\vasut\Desktop\FormaOS\U_Hack_FormaOS\flutter_app\assets\mock_data\players.json', encoding='utf-8') as f:
        players_data = json.load(f)
    
    player_teams = sorted(list(set(p['teamname'] for p in players_data['players'] if p.get('teamname'))))

    # Teams from teams.json
    with open(r'c:\Users\vasut\Desktop\FormaOS\U_Hack_FormaOS\flutter_app\assets\mock_data\teams.json', encoding='utf-8') as f:
        current_teams = json.load(f)
    
    # We want to match names or add missing ones
    # Common mappings
    # players.json names vs UI names
    # "Dinamo Bucureşti" (with accents)
    # "Oţelul"
    # "Petrolul 52"
    # "FCS Bucureşti"
    # "Farul Constanţa"
    
    sync_results = []
    for i, name in enumerate(player_teams):
        sync_results.append({"id": f"t{i+1}", "name": name})
    
    with open(r'c:\Users\vasut\Desktop\FormaOS\U_Hack_FormaOS\flutter_app\assets\mock_data\teams_synced.json', 'w', encoding='utf-8') as f:
        json.dump(sync_results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    sync_teams()
