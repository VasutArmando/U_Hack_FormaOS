import urllib.request, json, sys
sys.stdout.reconfigure(encoding="utf-8")

url = "http://127.0.0.1:8000/api/v1/pregame/opponent-weakness?opponent_id=t3&opponent_name=CFR+Cluj"
print("Testing:", url)

try:
    with urllib.request.urlopen(url, timeout=90) as r:
        data = json.loads(r.read().decode("utf-8"))
        print("Response type:", type(data))
        if isinstance(data, list):
            print(f"Got {len(data)} player intelligence items")
            for p in data[:3]:
                name = p.get("name", "?")
                score = p.get("overall_weakness_score", "?")
                phys = str(p.get("physical_state", ""))[:120]
                exploit = str(p.get("exploit_recommendation", ""))[:120]
                print(f"\n  [{name}] score={score}")
                print(f"  Physical: {phys}")
                print(f"  Exploit:  {exploit}")
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2)[:600])
except Exception as e:
    print("Error:", e)
