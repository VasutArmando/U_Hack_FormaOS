import json
import logging

class GcpJsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if hasattr(record, 'drift_metrics'):
            log_record['drift_metrics'] = record.drift_metrics
        return json.dumps(log_record)

logger = logging.getLogger("mlops_drift")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(GcpJsonFormatter())
logger.addHandler(handler)

def check_data_drift(current_stats: dict, baseline_stats: dict):
    """
    MLOps: Compară distribuțiile de date din meciul live cu cele pe care 
    a fost antrenat modelul BigQuery ML. Emite avertismente dacă apare Data Drift.
    """
    drift_detected = False
    drift_metrics = []

    for metric, current_val in current_stats.items():
        if metric in baseline_stats:
            baseline_val = baseline_stats[metric]
            if baseline_val == 0: continue
            
            # Calculăm varianța absolută
            variance = abs((current_val - baseline_val) / baseline_val)
            
            if variance > 0.20:  # Threshold setat la 20%
                drift_detected = True
                drift_metrics.append({
                    "metric": metric,
                    "baseline_bq_val": baseline_val,
                    "live_current_val": current_val,
                    "variance_pct": round(variance * 100, 2)
                })

    if drift_detected:
        logger.warning(
            f"DATA DRIFT DETECTAT: {len(drift_metrics)} metrici depășesc threshold-ul de 20%. Predicțiile ML pot fi degradate.",
            extra={"drift_metrics": drift_metrics}
        )
    else:
        logger.info("Validare MLOps OK: Distribuția datelor live corespunde baseline-ului de antrenament.")

if __name__ == "__main__":
    # Scenariu Simulat pentru Demonstrație
    
    # Acestea ar fi mediile statistice salvate din modelul BigQuery ML (Antrenament)
    baseline_bq_data = {
        "avg_sprint_speed_kmh": 32.5,
        "knee_flexion_angle_deg": 45.0,
        "heart_rate_variability": 55.0
    }
    
    # Acestea sunt datele intrate în minutul 67 (Jucătorul este obosit și are deviație articulară)
    current_match_data = {
        "avg_sprint_speed_kmh": 24.1,  # Viteză scăzută semnificativ -> Drift!
        "knee_flexion_angle_deg": 32.0, # Unghi modificat brusc -> Drift!
        "heart_rate_variability": 53.0  # Constant -> Ok
    }
    
    logger.info("MLOps: Inițiere verificare Data Drift pe Pipeline-ul SHIELD.")
    check_data_drift(current_match_data, baseline_bq_data)
