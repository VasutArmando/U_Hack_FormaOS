import time
import random
import logging

logger = logging.getLogger("chaos_monkey")
logging.basicConfig(level=logging.INFO)

class ChaosMonkey:
    """
    Testare FAANG: Chaos Engineering (inspirat de Netflix Chaos Monkey).
    Degeaba un produs funcționează perfect în laborator dacă crapă
    când stadionul Cluj Arena e plin și rețelele celulare sunt paralizate.
    """
    def __init__(self, failure_rate=0.4, latency_s=3.0):
        # 40% șanse să omoare conexiunea instantaneu
        self.failure_rate = failure_rate
        # Restul de 60% vor suferi un 'lag' masiv
        self.latency_s = latency_s

    def strike_api(self) -> bool:
        """
        Simulează mediul ostil.
        Returnează True dacă apelul trebuie distrus (503 Service Unavailable).
        """
        if random.random() < self.failure_rate:
            logger.error("🐒 [CHAOS MONKEY] Packet Loss Massive! Distrug complet conexiunea cu Cloud-ul.")
            return True 
            
        logger.warning(f"🐒 [CHAOS MONKEY] Injectez o latență de {self.latency_s} secunde. Testez Timeout-ul Clientului Flutter.")
        time.sleep(self.latency_s)
        return False
