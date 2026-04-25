import asyncio
import json
from data_manager import db_provider

opponent_name = "CFR Cluj"

teams = db_provider.get_teams()
opponent_id = next((t["id"] for t in teams if t["name"] == opponent_name), None)

data = db_provider.get_opponent_weaknesses(opponent_id, opponent_name)
print(json.dumps(data, indent=2))
