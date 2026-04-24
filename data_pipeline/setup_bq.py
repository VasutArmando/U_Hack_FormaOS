from google.cloud import bigquery
from typing import List, Dict, Any

# Clientul BigQuery (va folosi automat GOOGLE_APPLICATION_CREDENTIALS din environment)
client = bigquery.Client()

def setup_injury_model():
    """
    Creează (sau înlocuiește) modelul de Logistic Regression în BigQuery ML
    folosind datele istorice, conform blueprint-ului (Secțiunea V).
    Se rulează o singură dată (în faza de setup).
    """
    query = """
    CREATE OR REPLACE MODEL `forma_os.injury_risk_model`
    OPTIONS (
      model_type          = 'LOGISTIC_REG',
      input_label_cols    = ['injured_next_48h'],
      auto_class_weights  = TRUE,
      max_iterations      = 30
    ) AS
    SELECT
      minutes_last_3_matches,
      sprint_km_last_match,
      high_intensity_count,
      sleep_quality_score,
      subjective_fatigue_1_10,
      days_since_last_injury,
      age,
      injured_next_48h       -- label: 0 sau 1
    FROM `forma_os.historical_player_data`;
    """
    
    print("Începe antrenarea modelului LOGISTIC_REG în BigQuery...")
    job = client.query(query)
    job.result()  # Așteptăm finalizarea antrenării
    print("Modelul a fost creat cu succes!")

def predict_live_risk(live_players_data: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Rulează inferența ML.PREDICT folosind modelul antrenat.
    Dacă se primesc date noi (live_players_data), ideal se inserează
    în `forma_os.current_player_states` înainte de a rula interogarea, 
    sau se folosesc sisteme de streaming (Dataflow).
    
    Returnează rezultatele cu riscul procentual și categoriile (NORMAL, RIDICAT, CRITIC).
    """
    
    # Dacă sunt date live, într-un flux real de producție am face insert:
    if live_players_data:
        # client.insert_rows_json('forma_os.current_player_states', live_players_data)
        pass

    query = """
    SELECT
      player_name,
      player_number,
      ROUND(
        predicted_injured_next_48h_probs[OFFSET(1)].prob * 100, 1
      ) AS injury_risk_pct,
      CASE
        WHEN predicted_injured_next_48h_probs[OFFSET(1)].prob > 0.70 THEN '🔴 CRITIC'
        WHEN predicted_injured_next_48h_probs[OFFSET(1)].prob > 0.40 THEN '🟡 RIDICAT'
        ELSE '🟢 NORMAL'
      END AS risk_category
    FROM ML.PREDICT(
      MODEL `forma_os.injury_risk_model`,
      (SELECT * FROM `forma_os.current_player_states`)
    )
    ORDER BY injury_risk_pct DESC;
    """
    
    print("Rulare ML.PREDICT pentru extragerea riscului de accidentare...")
    job = client.query(query)
    results = job.result()
    
    predictions = []
    for row in results:
        predictions.append(dict(row.items()))
        
    return predictions

if __name__ == "__main__":
    # setup_injury_model()
    pass
