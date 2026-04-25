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

opponent_name='FCS Bucure\u015fti'
print('Searching opponent_name bytes:', [hex(ord(c)) for c in opponent_name])
print()

# Check each entry manually
for mid, md in list(matches_dict.items())[:5]:
    t1=md.get('team1','')
    t2=md.get('team2','')
    print(f'Match {mid}: t1={repr(t1)} t2={repr(t2)}')
    if 'FCS' in t1 or 'FCS' in t2:
        print('  -> FCS found!')
        print('  t2 bytes:', [hex(ord(c)) for c in t2])
        print('  eq check:', t1==opponent_name, t2==opponent_name)

# count how many have FCS
count=sum(1 for md in matches_dict.values() if 'FCS' in md.get('team1','') or 'FCS' in md.get('team2',''))
print(f'\nMatches with FCS in team name: {count}')
count2=sum(1 for md in matches_dict.values() if md.get('team1')==opponent_name or md.get('team2')==opponent_name)
print(f'Matches with FCS eq opponent_name: {count2}')
