import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
d=r'E:\U_Hack_FormaOS-1\Data_Fixed\Date - meciuri'

fcs_files=[f for f in os.listdir(d) if 'FCS' in f and 'players_stats' in f]
fcs_ids={}
for f in fcs_files:
    data=json.load(open(os.path.join(d,f),'r',encoding='utf-8'))
    if data.get('players'):
        mid=str(data['players'][0].get('matchId'))
        fcs_ids[mid]=f

print('FCS unique match IDs:', len(fcs_ids))

all_files=[f for f in os.listdir(d) if 'players_stats' in f and 'FCS' not in f]
collisions=[]
for f in all_files:
    data=json.load(open(os.path.join(d,f),'r',encoding='utf-8'))
    if data.get('players'):
        mid=str(data['players'][0].get('matchId'))
        if mid in fcs_ids:
            collisions.append((mid, fcs_ids[mid], f))

print('Collisions:', len(collisions))
for c in collisions[:5]:
    print(' ', c)
