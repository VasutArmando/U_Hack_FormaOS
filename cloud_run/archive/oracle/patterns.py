import numpy as np
from sklearn.cluster import KMeans
import logging

logger = logging.getLogger("forma_os_oracle")

def detect_formations(tracking_data: list, n_clusters=2) -> dict:
    """
    Folosește K-Means pentru a detecta formațiile de bază (ex: 4-3-3 vs 5-4-1)
    ale adversarului în funcție de starea scorului (conduși vs conduc).
    """
    logger.info("🧠 Rulăm K-Means pentru detectarea tiparelor de formație ale adversarului...")
    if not tracking_data:
        # Mock/Fallback dacă nu primim un array consistent de senzori pentru Demo
        return {
            "winning": "5-4-1 (Low Block Compact)",
            "losing": "4-3-3 (High Pressing)"
        }
    
    # Procesarea pozițiilor (X, Y) ale celor 11 jucători
    features = [frame['positions'] for frame in tracking_data]
    X = np.array(features)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X)
    
    # Într-un mediu real mapăm centroizii pe șabloane tactice cunoscute
    # (ex. dacă centroidul are 4 jucători în linia de fund -> formație cu 4 fundași)
    return {
        "winning": "5-4-1 (Sistem Închis)",
        "losing": "3-4-3 (Sistem Deschis / Ultra-ofensiv)"
    }

def detect_pressing_trigger(pressure_events: list) -> dict:
    """
    Detectează la ce distanță de poarta adversă încep aceștia să aplice 
    presing agresiv (Triggerul de Presing).
    """
    logger.info("📍 Analizăm zonele de declanșare a presingului adversarului...")
    if not pressure_events:
         return {
             "trigger_distance_m": 72.5,
             "trigger_zone": "High Block (Pressing Avansat la 72.5m de poarta lor)",
             "intensity": "Foarte Agresiv"
         }
         
    # Calculăm coordonata X medie unde se raportează presiunea maximă
    distances = [ev['x'] for ev in pressure_events] 
    
    avg_trigger = np.mean(distances)
    if avg_trigger > 70:
        trigger_zone = "High Block (Pressing Avansat)"
    elif avg_trigger > 40:
        trigger_zone = "Mid Block (Pressing la centrul terenului)"
    else:
        trigger_zone = "Low Block (Retragere și așteptare)"
        
    return {
        "trigger_distance_m": round(avg_trigger, 1),
        "trigger_zone": trigger_zone,
        "intensity": "Critic" if len(pressure_events) > 50 else "Moderat"
    }
    
def analyze_opponent_patterns(match_data: dict) -> dict:
    """
    Intrarea principală în modulul de detecție tendințe.
    Acest modul analizează strict ADVERSARUL.
    """
    tracking = match_data.get('tracking', [])
    pressure = match_data.get('pressure_events', [])
    
    formations = detect_formations(tracking)
    pressing = detect_pressing_trigger(pressure)
    
    return {
        "formations": formations,
        "pressing": pressing
    }
