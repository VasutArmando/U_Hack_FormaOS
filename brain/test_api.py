import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')
r=urllib.request.urlopen('http://localhost:8000/api/v1/pregame/opponent-weakness?opponent_id=t6', timeout=120)
data=json.loads(r.read().decode())
print('Players returned:', len(data))
for p in data[:10]:
    name=p.get('name','?')
    score=p.get('overall_weakness_score','?')
    print(f'  {name} | score={score}')
