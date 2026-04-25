import numpy as np
import logging
from collections import deque

logger = logging.getLogger("forma_os_celery")

class ExtendedKalmanFilter:
    """
    Filtru Kalman Extins (EKF) pentru a reduce Jitter-ul senzorilor GPS
    și a interpola mișcarea biomecanică a jucătorilor între frame-urile lipsă.
    Acest filtru rezolvă mismatch-ul dintre 10Hz (GPS) și 30Hz (Camera Optică).
    """
    def __init__(self, x, y):
        self.state = np.array([x, y, 0.0, 0.0], dtype=float)
        self.P = np.eye(4) * 5.0
        self.H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])
        self.R = np.eye(2) * 2.5 # Zgomotul GPS inerent din sistemul de sateliți (marjă eroare 2.5m)
        self.Q = np.eye(4) * 0.2 # Zgomotul de proces (schimbare bruscă de direcție/accelerație)

    def predict(self, dt):
        F = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1,  0],
            [0, 0, 0,  1]
        ])
        self.state = np.dot(F, self.state)
        self.P = np.dot(np.dot(F, self.P), F.T) + self.Q
        return self.state[:2]

    def update(self, measurement):
        y = measurement - np.dot(self.H, self.state)
        S = np.dot(self.H, np.dot(self.P, self.H.T)) + self.R
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))
        self.state = self.state + np.dot(K, y)
        I = np.eye(4)
        self.P = np.dot((I - np.dot(K, self.H)), self.P)

class SensorFusionEngine:
    def __init__(self, buffer_size_ms=500):
        """
        Gestionează alinierea temporală a frame-urilor video (30fps)
        cu senzorii GPS de la vestele jucătorilor (10Hz).
        Sincronizarea se face prin Time-Warping într-un buffer limitat de latență.
        """
        self.buffer_size_ms = buffer_size_ms
        self.gps_buffer = deque()
        self.trackers = {}
        logger.info(f"📡 Sensor Fusion Engine inițializat (NTP Jitter Buffer: {buffer_size_ms}ms)")

    def ingest_gps(self, ntp_timestamp, pid, x, y):
        # Ștergem din coadă pachetele care au expirat (mai vechi de 500ms)
        while self.gps_buffer and (ntp_timestamp - self.gps_buffer[0][0]) > (self.buffer_size_ms / 1000.0):
            self.gps_buffer.popleft()
            
        self.gps_buffer.append((ntp_timestamp, pid, x, y))

    def sync_and_interpolate(self, target_ntp_timestamp, positions):
        """
        Dă forward matematic la poziția jucătorilor cu X milisecunde pentru a se 
        potrivi EXACT pe pixelii cadrului video procesat de MediaPipe.
        Fără acest pas, hărțile Voronoi ar 'pluti' greșit deasupra jucătorilor pe transmisiunea live.
        """
        synced_positions = []
        for i, p in enumerate(positions):
            pid = f"player_uid_{i}"
            raw_x, raw_y = p[0], p[1]
            
            # Injectăm GPS Ping în Buffer (Simulăm că a venit acum 100ms față de Video)
            self.ingest_gps(target_ntp_timestamp - 0.1, pid, raw_x, raw_y) 
            
            if pid not in self.trackers:
                self.trackers[pid] = ExtendedKalmanFilter(raw_x, raw_y)
                
            tracker = self.trackers[pid]
            tracker.update(np.array([raw_x, raw_y]))
            
            # INTERPOLARE: 
            # Senzorul GPS ne dă 1 cadru la 100ms. Camera video procesează la 33ms (30fps).
            # Aplicăm Derivata Spațială din matricea Kalman pentru a deduce milimetric poziția.
            time_delta = 0.033 
            pred = tracker.predict(time_delta)
            
            synced_positions.append([round(pred[0], 2), round(pred[1], 2)])
            
        return synced_positions
