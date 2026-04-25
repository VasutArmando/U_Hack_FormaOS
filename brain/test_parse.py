import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
d=r'E:\U_Hack_FormaOS-1\Data_Fixed\Date - meciuri'
files=[f for f in os.listdir(d) if f.endswith('.json') and 'players_stats' in f]
matches_dict={}
for filename in files:
    filepath=os.path.join(d,filename)
    try:
        with open(filepath,'r',encoding='utf-8') as f:
            data=json.load(f)
    except: continue
    if not isinstance(data,dict) or 'players' not in data or not data['players']: continue
    match_id=str(data['players'][0].get('matchId'))
    if not match_id or match_id=='None': continue
    name_part=filename.split(',')[0]
    teams_split=name_part.split(' - ')
    if len(teams_split)==2:
        team1,team2=teams_split[0].strip(),teams_split[1].strip()
    else:
        team1,team2='Unknown','Unknown'
    data['team1']=team1
    data['team2']=team2
    matches_dict[match_id]=data

print('Total matches in cache:', len(matches_dict))
# Show all unique team1 values
team1s=set(md.get('team1','?') for md in matches_dict.values())
team2s=set(md.get('team2','?') for md in matches_dict.values())
all_teams=team1s|team2s
print('All team names in cache:')
for t in sorted(all_teams):
    print(' ', repr(t))

opponent_name='FCS Bucure\u015fti'
print('\nSearching for:', repr(opponent_name))
fcs_matches=[md for md in matches_dict.values() if md.get('team1')==opponent_name or md.get('team2')==opponent_name]
print('FCS matches found:', len(fcs_matches))
