import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
d=r'E:\U_Hack_FormaOS-1\Data_Fixed\Date - meciuri'
pf=os.path.join(d,'players (1).json')
players_data=json.load(open(pf,'r',encoding='utf-8'))['players']
mapping={str(p['wyId']): p.get('shortName') or (p.get('firstName','') + ' ' + p.get('lastName','')).strip() for p in players_data}
team_cache={str(p['wyId']): p.get('teamname','Unknown') for p in players_data}
role_cache={str(p['wyId']): p.get('role',{}).get('name','') for p in players_data}

opponent_name='FCS Bucure\u015fti'
files=[f for f in os.listdir(d) if 'players_stats' in f]
player_stats_agg={}
match_count=0
for f in files:
    data=json.load(open(os.path.join(d,f),'r',encoding='utf-8'))
    name_part=f.split(',')[0]
    parts=name_part.split(' - ')
    if len(parts)!=2: continue
    t1,t2=parts[0].strip(),parts[1].strip()
    if t1!=opponent_name and t2!=opponent_name: continue
    match_count+=1
    for p in data['players']:
        pid=str(p.get('playerId',''))
        if team_cache.get(pid)!=opponent_name: continue
        if pid not in player_stats_agg:
            new_p=p.copy()
            new_p['aggregated_minutes']=0
            new_p['aggregated_duels']=0
            new_p['aggregated_duels_won']=0
            player_stats_agg[pid]=new_p
        totals=p.get('total',{})
        player_stats_agg[pid]['aggregated_minutes']+=totals.get('minutesOnField',0)
        player_stats_agg[pid]['aggregated_duels']+=totals.get('duels',0)
        player_stats_agg[pid]['aggregated_duels_won']+=totals.get('duelsWon',0)

print('Matches found:', match_count)
print('Players aggregated:', len(player_stats_agg))
for pid,p in list(player_stats_agg.items())[:10]:
    name=mapping.get(pid,'UNMAPPED')
    role=role_cache.get(pid,'')
    mins=p['aggregated_minutes']
    print(f'  {pid} -> {name} | {role} | {mins} min')
