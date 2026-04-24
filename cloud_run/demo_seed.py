import firebase_admin
from firebase_admin import firestore
import time

def init_firebase():
    """Inițializează Firebase folosind ADC (Application Default Credentials)"""
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        return firestore.client()
    except Exception as e:
        print(f"Eroare Firebase: Asigură-te că ai setat GOOGLE_APPLICATION_CREDENTIALS. ({e})")
        return None

def run_demo_seed():
    db = init_firebase()
    if not db:
        print("Rulare simulată pentru demo_seed.py (fără conexiune BD)...")
        # Nu ne oprim, doar simulăm output-ul dorit pentru vizualizare cod
        
    print("==================================================")
    print("🚀 INIT: FORMA OS Demo Mode (Hackathon Final) ")
    print("==================================================")
    print("Se încarcă scenariul: Minutul 67' | U Cluj 0-1 CFR Cluj")
    
    if db:
        # 1. Update Match State
        db.collection('matches').document('current_match').set({
            "home_score": 0,
            "away_score": 1,
            "minute": 67,
            "possession_pct": 54.2,
            # Câteva coordonate mock pentru a randa ceva pe X-RAY canvas
            "home_positions": [[20.0, 30.0], [25.5, 45.1], [40.2, 50.0], [35.0, 20.0]],
            "away_positions": [[55.0, 34.0], [60.0, 50.0], [65.0, 20.0], [80.0, 34.0]]
        })
        
        alerts_ref = db.collection('alerts')
        
        # 2. Injectare Alertă X-RAY (Spațiu)
        alerts_ref.add({
            "type": "TACTICAL",
            "severity": "HIGH",
            "player": "N/A",
            "message": "Gap 14m identificat pe flancul drept! xT=0.47. Recomandare: Declanșare pasă filtrată pe poziție viitoare.",
            "minute": 67,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "acknowledged": False
        })
        
        # 3. Injectare Alertă SHIELD (Biomecanică)
        alerts_ref.add({
            "type": "BIOMECHANICAL",
            "severity": "CRITICAL",
            "player": "Atacant U Cluj (Nr. 9)",
            "message": "Deviație biomecanică: 4.2° la genunchiul stâng pe faza de aterizare. Risc critic LIA. Substituție imediată recomandată!",
            "minute": 67,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "acknowledged": False
        })

    print("✅ Datele de MatchState au fost suprascrise.")
    print("✅ Alerta 'Gap 14m (xT=0.47)' injectată.")
    print("✅ Alerta 'Biomecanică: Genunchi stâng 4.2°' injectată.")
    print("Aplicația Flutter (Frontend) și Backend-ul ar trebui să reacționeze în timp real!")

if __name__ == "__main__":
    run_demo_seed()
