import os, re, json, unicodedata

def check_missing():
    files = os.listdir(r'c:\Users\vasut\Desktop\FormaOS\U_Hack_FormaOS\Data_Fixed\Date - meciuri')
    match_teams = set()
    for f in files:
        if 'players_stats' in f:
            # Argeș - FCS Bucures,ti, 1-0_players_stats.json
            name = f.replace('_players_stats.json', '')
            if ',' in name:
                teams_part = name.rsplit(',', 1)[0]
            else:
                teams_part = name
            ts = teams_part.split(' - ')
            for t in ts:
                match_teams.add(t.strip())
    
    with open(r'c:\Users\vasut\Desktop\FormaOS\U_Hack_FormaOS\cloud_run\data\teams.json', encoding='utf-8') as f:
        known_teams = json.load(f)
    
    known_names = {t['name'] for t in known_teams}
    
    missing = []
    for mt in match_teams:
        if mt not in known_names:
            missing.append(mt)
            
    with open(r'c:\Users\vasut\Desktop\FormaOS\U_Hack_FormaOS\scratch\missing_teams.json', 'w', encoding='utf-8') as f:
        json.dump(missing, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    check_missing()
