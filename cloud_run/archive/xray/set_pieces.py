import numpy as np
import logging
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import cdist

logger = logging.getLogger("forma_os_celery")

class SetPiecesAnalyzer:
    """
    Sistem MLOps de izolare și analiză a 'Fazelor Fixe' (Dead Balls).
    Analizează clustering-ul de jucători pentru a deduce tipurile de marcaj.
    """
    def __init__(self):
        # Definim Y-ul Careului: Lățimea standard e 40.32m. Pe Y(0-68), careul e între 13.84 și 54.16.
        self.y_min = 13.84
        self.y_max = 54.16

    def _is_in_box(self, p):
        if not p or len(p) < 2: return False
        
        # Careul din Stânga (0 -> 16.5m)
        in_left_box = (0.0 <= p[0] <= 16.5) and (self.y_min <= p[1] <= self.y_max)
        # Careul din Dreapta (88.5 -> 105.0m)
        in_right_box = (88.5 <= p[0] <= 105.0) and (self.y_min <= p[1] <= self.y_max)
        
        return in_left_box or in_right_box

    def analyze(self, home_positions, away_positions):
        """
        Input: Coordonatele celor 22 de jucători
        Output: Tiparul de marcaj advers și identificarea breșelor.
        """
        home_in_box = [p for p in home_positions if self._is_in_box(p)]
        away_in_box = [p for p in away_positions if self._is_in_box(p)]
        
        total_in_box = len(home_in_box) + len(away_in_box)
        
        # 1. TRIGGER: Dacă sunt sub 8 jucători în careu, este Open Play, ignorăm logica.
        if total_in_box < 8:
            return {"is_set_piece": False, "alerts": []}
            
        logger.info(f"🚩 X-RAY: 'Minge Moartă' Detectată! {total_in_box} jucători comasați în careu.")
        
        # 2. CLUSTERING SPATIAL (DBSCAN)
        all_players = np.array(home_in_box + away_in_box)
        
        # Parametrul epsilon=2.5m grupează un atacant și un fundaș într-un singur "duel" 
        # dacă stau la distanță de contact fizic.
        clustering = DBSCAN(eps=2.5, min_samples=2).fit(all_players)
        
        # Numărăm cluster-ele ignorând zgomotul (eticheta -1)
        n_clusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
        
        # Deducție AI: Multe perechi strânse = Om la Om. Câteva blocuri mari = Zonă.
        marking_type = "OM_LA_OM" if n_clusters >= 4 else "ÎN_ZONĂ"
        logger.info(f"🧠 X-RAY: Modelul advers de apărare este {marking_type}.")

        # 3. BREACH DETECTION (Găsirea Omului Liber)
        alerts = []
        if home_in_box and away_in_box:
            # Matricea Distanțelor Euclidiene: Fiecare atacant U Cluj vs fiecare fundaș advers
            distances = cdist(home_in_box, away_in_box, metric='euclidean')
            
            for i, home_player in enumerate(home_in_box):
                min_dist_to_defender = np.min(distances[i])
                
                # Regula X-RAY: Un jucător alfabetic demarcat la peste 2.5m înseamnă Ocazie de Gol!
                if min_dist_to_defender > 2.5:
                    alert_msg = (f"🎯 OPORTUNITATE CORNER: Jucătorul nostru de la X={round(home_player[0],1)}, Y={round(home_player[1],1)} "
                                 f"este COMPLET DEMARCAT (Cel mai apropiat adversar e la {round(min_dist_to_defender,1)}m distanță). "
                                 f"Executați rapid schema izolând fundașii pe zonă scurtă!")
                    alerts.append({
                        "type": "SET_PIECE_GHOST",
                        "severity": "CRITICAL",
                        "message": alert_msg
                    })
                    
        return {
            "is_set_piece": True,
            "marking_system": marking_type,
            "alerts": alerts
        }
