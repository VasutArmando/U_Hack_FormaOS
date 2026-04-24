import os
from celery import Celery

# URL-ul Broker-ului de Mesaje (Memorie In-Memory de Înaltă Performanță)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Inițializare instanță Celery pentru microserviciul de Heavy Computation (ML/AI)
# Acest worker se poate scala independent de FastAPI, adăugând 10-100 de instanțe în Kubernetes la nevoie.
celery_app = Celery(
    "forma_os_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks"]
)

# Standarde Enterprise pentru siguranța rulării AI-ului
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Bucharest",
    enable_utc=True,
    task_track_started=True,
    # FAANG Standard: Dacă algoritmul VertexAI se blochează, omorâm task-ul după 60s
    task_time_limit=60, 
    worker_prefetch_multiplier=1 # Procesare 1:1 pt resurse mari consumatoare de CPU
)
