from sklearn.cluster import KMeans
import numpy as np

def detect_formation(positions_10_outfield: list[tuple]) -> dict:
    """
    Input: lista de (x, y) pentru cei 10 jucători de câmp (fără portar)
    Output: formație + trigger de presing + poziția liniei de mijloc
    """
    pos = np.array(positions_10_outfield)
    
    # 3 clustere = 3 linii tactice
    km = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels = km.fit_predict(pos)
    
    # Sortăm liniile după axa X (adâncimea pe teren)
    centers_x = [np.mean(pos[labels == i][:, 0]) for i in range(3)]
    sorted_lines = sorted(zip(centers_x, [np.sum(labels == i) for i in range(3)]))
    
    formation = "-".join(str(cnt) for _, cnt in sorted_lines)
    
    # Linia de presing = media liniei de mijloc
    midfield_x = sorted_lines[1][0]
    pressing_trigger = midfield_x > 55  # depășește jumătatea terenului
    
    return {
        "formation": formation,
        "pressing_trigger": pressing_trigger,
        "pressing_line_m": round(midfield_x, 1),
        "description": f"Formație {formation}, linie de presing la {midfield_x:.0f}m"
    }
