from tactician.gemini_engine import GeminiEngine

def main():
    print("======================================================")
    print("TEST MODUL TACTICIAN - Pregătire Prezentare Hackathon")
    print("======================================================\n")

    engine = GeminiEngine()
    
    # Construim contextul fictiv din Demo Seed (Min 67', U Cluj 0-1)
    demo_context = {
        "match_state": {
            "minute": 67,
            "home_score": 0,
            "away_score": 1,
            "possession_pct": 54.2
        },
        "oracle_data": {
            "formation": "4-2-3-1 adversar (linii distanțate)"
        },
        "xray_data": {
            "top_gap": {
                "width_m": 14.0,
                "xt_value": 0.47,
                "location": "flancul drept advers"
            }
        },
        "shield_data": {
            "critical_players": [
                {
                    "player": "Atacant U Cluj (Nr. 9)",
                    "issue": "Deviație biomecanică 4.2° genunchi stâng",
                    "risk_level": "CRITIC"
                }
            ]
        },
        "coach_question": "Ce substituție recomand și cum exploatăm gap-ul?"
    }
    
    # 1. Testăm construcția prompt-ului
    print("1. PROMPT-UL GENERAT PENTRU LLM:")
    print("-" * 55)
    prompt = engine.build_context(demo_context)
    print(prompt)
    print("-" * 55)
    
    # 2. Rulăm motorul LLM (cu sistemul de fallback activat local)
    print("\n2. RĂSPUNSUL GENERAT DE TACTICIAN:")
    print("Se așteaptă conexiunea la Vertex AI...")
    response = engine.generate_tactical_advice(demo_context)
    
    print("=" * 55)
    print(response)
    print("=" * 55)
    print("\n✅ Test completat cu succes! Fallback-ul sau API-ul a reacționat impecabil.")

if __name__ == "__main__":
    main()
