import firebase_admin
from firebase_admin import firestore

def validate_presentation_data():
    print("=" * 60)
    print("🔍 RULARE SCRIPT DE VALIDARE PENTRU PREZENTARE (PRE-FLIGHT CHECK)")
    print("=" * 60)
    
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        db = firestore.client()
    except Exception as e:
        print(f"❌ EROARE CRITICĂ: Nu se poate conecta la Firebase: {e}")
        print("Asigură-te că GOOGLE_APPLICATION_CREDENTIALS este setată.")
        return

    errors = 0

    # 1. Verificare MatchState
    match_doc = db.collection('matches').document('current_match').get()
    if not match_doc.exists:
        print("❌ EROARE: Documentul 'current_match' lipsește complet!")
        errors += 1
    else:
        data = match_doc.to_dict()
        required_fields = ['minute', 'home_score', 'away_score', 'home_positions', 'away_positions']
        for field in required_fields:
            if field not in data:
                print(f"❌ EROARE: Câmpul '{field}' lipsește din MatchState!")
                errors += 1
        
        if data.get('minute') != 67:
            print(f"⚠️ AVERTISMENT: Minutul meciului nu este 67'. (Este setat pe: {data.get('minute')})")

    # 2. Verificare Alerte Critice
    alerts = db.collection('alerts').where('minute', '==', 67).get()
    if len(alerts) < 2:
        print(f"❌ EROARE: Nu există suficiente alerte injectate pentru 'Wow Moment'. S-au găsit: {len(alerts)}")
        errors += 1
    else:
        has_tactical = False
        has_biomechanical = False
        for a in alerts:
            ad = a.to_dict()
            if ad.get('type') == 'TACTICAL': has_tactical = True
            if ad.get('type') == 'BIOMECHANICAL': has_biomechanical = True
        
        if not has_tactical:
            print("❌ EROARE: Lipsește alerta TACTICAL (Gap 14m).")
            errors += 1
        if not has_biomechanical:
            print("❌ EROARE: Lipsește alerta BIOMECHANICAL (4.2° genunchi).")
            errors += 1

    print("-" * 60)
    if errors == 0:
        print("✅ VALIDARE REUȘITĂ: Baza de date este complet populată și stabilă pentru pitch-ul de 3 minute!")
    else:
        print(f"🚨 VALIDARE EȘUATĂ: Au fost găsite {errors} probleme. Rulează `python demo_seed.py` pentru a le repara automat.")
    print("=" * 60)

if __name__ == "__main__":
    validate_presentation_data()
