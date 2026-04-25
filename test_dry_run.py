import asyncio
import json
from cloud_run.main import (
    get_teams, get_stadiums, pregame_chronic_gaps, pregame_opponent_weakness,
    ingame_live_gaps, ingame_opponent_status, halftime_tactical_gaps,
    halftime_predicted_changes, context_weather, ingame_assistant, AssistantRequest
)

class MockRequest:
    pass

async def run_tests():
    print("=== INCEPERE AUDIT QA: FORMA OS BACKEND ===")
    
    req = MockRequest()
    all_passed = True
    
    endpoints = [
        ("GET /api/v1/settings/teams", get_teams),
        ("GET /api/v1/settings/stadiums", get_stadiums),
        ("GET /api/v1/pregame/chronic-gaps", pregame_chronic_gaps),
        ("GET /api/v1/pregame/opponent-weakness", pregame_opponent_weakness),
        ("GET /api/v1/ingame/live-gaps", ingame_live_gaps),
        ("GET /api/v1/ingame/opponent-status", ingame_opponent_status),
        ("GET /api/v1/halftime/tactical-gaps", halftime_tactical_gaps),
        ("GET /api/v1/halftime/predicted-changes", halftime_predicted_changes),
        ("GET /api/v1/context/weather", context_weather),
    ]

    for name, func in endpoints:
        print(f"\nTestare: {name}")
        try:
            data = await func(req)
            print(f"[OK] Returnat: {len(data) if isinstance(data, list) else 1} intrari.")
            if "opponent-weakness" in name:
                if data and "physical_state" in data[0]:
                    print(f"   Sample physical_state: {data[0]['physical_state']}")
            elif "opponent-status" in name:
                if data and "live_remark" in data[0]:
                    print(f"   Sample live_remark: {data[0]['live_remark']}")
            elif "predicted-changes" in name:
                if data:
                    print(f"   Sample category: {data[0].get('category')} | Likelihood: {data[0].get('likelihood')}")
                    print(f"   Sample detail: {data[0].get('detail', 'N/A')}")
        except Exception as e:
            print(f"[ERROR]: {e}")
            all_passed = False

    print("\nTestare: POST /api/v1/ingame/assistant")
    try:
        resp_ast = await ingame_assistant(req, AssistantRequest(query="unde sunt spații libere?"))
        print(f"[OK] STT Assistant Gaps: {resp_ast.get('advice')}")
    except Exception as e:
        print(f"[ERROR] POST Assistant: {e}")
        all_passed = False

    try:
        resp_ast2 = await ingame_assistant(req, AssistantRequest(query="cine are oboseală mare?"))
        print(f"[OK] STT Assistant Fatigue: {resp_ast2.get('advice')}")
    except Exception as e:
        print(f"[ERROR] POST Assistant: {e}")
        all_passed = False

    print(f"\n=== REZULTAT FINAL: {'TOATE TESTELE AU TRECUT' if all_passed else 'EXISTA ERORI!'} ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
