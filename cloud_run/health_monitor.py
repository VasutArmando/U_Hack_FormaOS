import time
import requests
import logging

# Configurăm logging-ul pentru a fi scris atât pe consolă cât și salvat în fișier (Audit Trail)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("forma_os_uptime.log"),
        logging.StreamHandler()
    ]
)

# Endpoint-ul curent (poate fi suprascris cu URL-ul de la Cloud Run)
API_URL = "http://127.0.0.1:8080/health" 
CHECK_INTERVAL = 10  # Secunde între ping-uri

def run_health_monitor():
    logging.info(f"🚀 FORMA OS SRE Monitor pornit. Urmărim endpoint-ul: {API_URL}")
    consecutive_failures = 0

    while True:
        try:
            start_time = time.time()
            response = requests.get(API_URL, timeout=3) # Timeout agresiv
            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "N/A")
                modules = len(data.get("modules", []))
                
                logging.info(f"✅ OK [200] | Latență: {latency_ms}ms | Stare: {status} | Module Active: {modules}")
                consecutive_failures = 0  # Reset la succes
            else:
                logging.warning(f"⚠️ DEGRADARE SERVICIU: Cod {response.status_code} primit!")
                consecutive_failures += 1

        except requests.exceptions.RequestException as e:
            consecutive_failures += 1
            logging.error(f"🚨 DOWNTIME DETECTAT: Nu s-a putut stabili conexiunea. ({str(e).split(':')[-1].strip()})")
            
            # Sistem de escaladare
            if consecutive_failures == 3:
                logging.critical("🔥 ALERTĂ MAJORĂ (PAGERDUTY): Sistemul e picat de 3 cicluri consecutive. Echipa de DevOps trebuie alertată ACUM!")
                # În producție, aici am rula un POST către un Webhook de Slack sau Twilio SMS.

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        run_health_monitor()
    except KeyboardInterrupt:
        logging.info("🛑 Procesul de SRE Monitor a fost oprit de utilizator.")
