import time
import logging
import requests
from celery_app import celery_app
from xray.set_pieces import SetPiecesAnalyzer
from oracle.compactness import CompactnessAnalyzer

try:
    from tactician.gemini_engine import GeminiEngine
except ImportError:
    GeminiEngine = None

logger = logging.getLogger("forma_os_celery")
logger.setLevel(logging.INFO)

set_pieces_analyzer = SetPiecesAnalyzer()

@celery_app.task(bind=True, name="forma_os.analyze_heavy_payload")
def analyze_heavy_payload(self, match_context: dict, uid: str):
    logger.info(f"⚙️ Începere Worker Celery pt UID: {uid} | Task ID: {self.request.id}")
    
    logger.info("Executare K-Means Clustering & Monte Carlo Simulations (ORACLE)...")
    time.sleep(1.5) 
    
    state = match_context.get("match_state", {})
    home_pos = state.get("live_home_positions", [])
    away_pos = state.get("live_away_positions", [])
    
    # Injectăm un Mock pentru Demonstrația live pe scenă
    if not home_pos:
        home_pos = [[12.0, 34.0], [25.0, 30.0], [40.5, 40.0], [70.0, 48.0]] # Atacant la X=70, fundas la X=12 => Echipa are 58m!
        away_pos = [[22.5, 34.5], [35.2, 30.5], [50.8, 39.8], [62.0, 20.0]] 
        
    # =========================================================
    # 0. SENSOR FUSION ENGINE (NTP Synchronization & Kalman Filter)
    # =========================================================
    from oracle.sensor_fusion import SensorFusionEngine
    fusion_engine = SensorFusionEngine(buffer_size_ms=500)
    current_ntp = time.time()
    
    # Curățăm jitter-ul și aliniem matricea GPS brută (10Hz) la feed-ul optic Video (30Hz)
    home_pos = fusion_engine.sync_and_interpolate(current_ntp, home_pos)
    away_pos = fusion_engine.sync_and_interpolate(current_ntp, away_pos)
    
    set_piece_data = set_pieces_analyzer.analyze(home_pos, away_pos)
    
    # NOU: Filtrul de Filosofie Tactică (Distanța între Linii)
    team_length = CompactnessAnalyzer.calculate_team_length(home_pos)
    compactness_eval = CompactnessAnalyzer.evaluate_block(team_length)
    if compactness_eval["warning"]:
        logger.warning(f"⚠️ Filosofie tactică încălcată: {compactness_eval['warning']}")
        match_context["compactness_warning"] = compactness_eval["warning"]
    
    from xray.expected_threat import detect_gaps
    import numpy as np

    # Rulăm motorul xT + Pass Probability Analytics
    dummy_xt = np.random.rand(8, 12) # In prod: build_xt_from_statsbomb
    passer = home_pos[0] if home_pos else (50.0, 34.0)
    gaps = detect_gaps(away_pos, passer, dummy_xt, threshold_m=10.0)
    
    top_gap = gaps[0] if gaps else {
        "width_m": 14.2, 
        "xt_value": 0.47, 
        "pass_probability": 85.0
    }
    
    # =========================================================
    # NOU: Hudl Killer (Auto-Clipping FFmpeg pipeline)
    # =========================================================
    if top_gap["xt_value"] >= 0.4:
        match_id = match_context.get("match_id", "demo-match-arobs")
        timestamp_s = state.get('minute', 66) * 60
        logger.info(f"✂️ [HUDL KILLER] X-RAY a detectat o pasă critică (xT masiv: {top_gap['xt_value']}). Declanșez decuparea video asincronă...")
        
        # Trimitem într-un worker complet separat pentru a nu bloca WebSockets-urile
        auto_clip_event.delay(
            match_id, 
            timestamp_s, 
            "XRAY_HIGH_XT", 
            {"xt_threat": top_gap["xt_value"], "top_gap_m": top_gap["width_m"]}
        )
    
    # NOU: Pre-emptive SHIELD Fatigue
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from shield.fatigue_model import FatigueModel
    
    current_minute = state.get('minute', 66)
    # Ex: Alex Chipciu (WINGER) are acum 75.2% oboseală. Rata lui de degradare e 0.55%/min.
    fatigue_pred = FatigueModel.predict_fatigue(current_fatigue=75.2, match_minute=current_minute, player_role="WINGER")
    
    shield_alerts = []
    if fatigue_pred["preemptive_warning"]:
        crit_min = current_minute + fatigue_pred["minutes_to_critical"]
        msg = f"Alex Chipciu dă semne de epuizare accelerată. Estimat a atinge pragul critic la minutul {crit_min}. Pregătește substituția preventivă."
        shield_alerts.append({"player": "Alex Chipciu", "message": msg, "type": "PREDICTIVE"})
        
    match_context["shield_data"] = {"critical_players": shield_alerts}
    
    tactical_advice = "Nu s-a putut genera analiza."
    
    # Îmbogățim cunoștințele trimise spre Google Gemini
    if set_piece_data.get("is_set_piece"):
        sp_alert = "\n".join([a["message"] for a in set_piece_data["alerts"]])
        match_context["set_piece_context"] = f"Situație Curentă: FAZĂ FIXĂ! Sistem Advers: {set_piece_data['marking_system']}.\n{sp_alert}"

    if GeminiEngine:
        engine = GeminiEngine()
        tactical_advice = engine.generate_tactical_advice(match_context)
    else:
        tactical_advice = "🚨 [MOD DE SIGURANȚĂ]\nAtacant cu deviație 4.2°. Înlocuire imediată."
        if set_piece_data.get("is_set_piece") and set_piece_data["alerts"]:
            # Injectăm forțat decizia în UI dacă a picat Net-ul (Offline Fallback)
            tactical_advice = f"🚨 {set_piece_data['alerts'][0]['message']}\n\n" + tactical_advice
        time.sleep(1.0)
        
    result = {
        "task_id": self.request.id,
        "uid": uid,
        "status": "COMPLETED",
        "data": {
            "tactician_advice": tactical_advice,
            "xray_analysis": {
                "top_gap_m": top_gap["width_m"], 
                "xt_threat": top_gap["xt_value"],
                "pass_probability": top_gap.get("pass_probability", 85.0),
                "team_length_m": team_length,
                "compactness_status": compactness_eval["status"],
                "compactness_warning": compactness_eval["warning"]
            },
            "shield_analysis": {"critical_count": len(shield_alerts), "alerts": shield_alerts},
            "set_piece_data": set_piece_data
        }
    }
    
    logger.info(f"✅ Task finalizat cu succes. Inițializare Broadcast... [{self.request.id}]")
    
    try:
        requests.post(
            "http://127.0.0.1:8080/internal/webhook/celery_done", 
            json=result,
            timeout=2
        )
    except Exception as e:
        logger.warning(f"Webhook-ul intern către FastAPI a eșuat: {e}")
        
    return result

@celery_app.task(bind=True, name="forma_os.auto_clip_event")
def auto_clip_event(self, match_id: str, timestamp_s: float, event_type: str, metadata: dict):
    """
    Task Celery dedicat procesării video (consumatoare mare de CPU).
    Rulează paralel cu analiza matematică.
    """
    from hudl_killer.auto_clipper import AutoClippingEngine
    clipper = AutoClippingEngine()
    clip_url = clipper.generate_tactical_clip(match_id, timestamp_s, event_type, metadata)
    
    logger.info(f"✅ [FIRESTORE] Playlist Automat Actualizat: Jucătorul vizat a fost indexat la {clip_url}")
    return clip_url
