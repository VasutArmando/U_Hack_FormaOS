import numpy as np

# Configurații teren (standard FIFA)
PITCH_L = 105
PITCH_W = 68
GRID_X = 12
GRID_Y = 8

def build_xt_from_statsbomb(events: list) -> np.ndarray:
    """Generează matricea de Expected Threat (xT) bazată pe date istorice"""
    zone_count = np.zeros((GRID_Y, GRID_X))
    shoot_count = np.zeros((GRID_Y, GRID_X))
    goal_count = np.zeros((GRID_Y, GRID_X))
    
    for ev in events:
        loc = ev.get("location")
        if not loc: continue
        xi = min(int(loc[0] / PITCH_L * GRID_X), GRID_X - 1)
        yi = min(int(loc[1] / PITCH_W * GRID_Y), GRID_Y - 1)
        zone_count[yi, xi] += 1
        if ev["type"] == "Shot":
            shoot_count[yi, xi] += 1
            if ev.get("shot_outcome") == "Goal":
                goal_count[yi, xi] += 1
                
    S = shoot_count / (zone_count + 1e-9)
    G = np.where(shoot_count > 0, goal_count / (shoot_count + 1e-9), 0)
    xT = S * G
    return xT

def point_xt(x: float, y: float, xt_model: np.ndarray):
    xi = min(int(x / PITCH_L * GRID_X), GRID_X - 1)
    yi = min(int(y / PITCH_W * GRID_Y), GRID_Y - 1)
    return round(float(xt_model[yi, xi]), 4)

def calculate_pass_probability(start_x, start_y, target_x, target_y, away_positions):
    """
    Mecanică Fizică: Evaluează cât de fezabilă este o pasă.
    Nu ajută să identificăm un spațiu dacă pasa până acolo va fi interceptată garantat!
    """
    dist_pass = np.sqrt((target_x - start_x)**2 + (target_y - start_y)**2)
    if dist_pass == 0: return 0.0
    
    # Baseline kinematic: o pasă de 10m are șanse 95%. O diagonală de 70m scade tehnic la 35%.
    base_prob = max(0.95 - (dist_pass / 100.0), 0.35)
    
    interception_penalty = 0.0
    pass_vector = np.array([target_x - start_x, target_y - start_y])
    pass_vector_norm = pass_vector / dist_pass
    
    # Verificăm densitatea tuturor fundașilor adverși pe vectorul pasei
    for p in away_positions:
        v_opp = np.array([p[0] - start_x, p[1] - start_y])
        # Proiecția ortogonală a adversarului pe axa pasei
        proj_len = np.dot(v_opp, pass_vector_norm)
        
        # Dacă adversarul stă fix între trimițător și receptor
        if 0 < proj_len < dist_pass:
            # Calculăm distanța perpendiculară de la el la minge (Cât trebuie să întindă piciorul)
            perp_dist = np.linalg.norm(v_opp - proj_len * pass_vector_norm)
            
            # O intercepție este critică dacă raza de tăiere e sub 2.5m
            if perp_dist < 2.5:
                # Penalty de xT (scade grav probabilitatea)
                interception_penalty += 0.5 * (1.0 - (perp_dist / 2.5))
                
    final_prob = max(base_prob - interception_penalty, 0.01)
    return min(final_prob, 0.99)

def detect_gaps(
    away_positions: list[tuple],
    home_passer_pos: tuple,
    xt_model: np.ndarray,
    threshold_m: float = 12.0
) -> list[dict]:
    """Detectează Gaps (Breșe Defensiv) dar le filtrează inteligent prin filtrul de Pass Probability."""
    sorted_away = sorted(away_positions, key=lambda p: p[0])
    gaps = []
    
    for i in range(len(sorted_away) - 1):
        p1, p2 = sorted_away[i], sorted_away[i + 1]
        d = np.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
        if d >= threshold_m:
            cx, cy = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
            xt = point_xt(cx, cy, xt_model)
            
            # De la cine pleacă decizia tactică (mijlocaș central by default)
            start_x, start_y = home_passer_pos if home_passer_pos else (50.0, 34.0)
            
            # 💡 Magic Touch: Simulăm traiectoria mingii
            pass_prob = calculate_pass_probability(start_x, start_y, cx, cy, away_positions)
            
            gaps.append({
                "center": (round(cx, 1), round(cy, 1)),
                "width_m": round(d, 1),
                "xt_value": xt,
                "pass_probability": round(pass_prob * 100, 1),
                "alert": f"Gap {d:.0f}m la ({cx:.0f}m, {cy:.0f}m)",
                "action": f"Pasă filtrată - xT={xt:.3f}"
            })
            
    # Ignorăm spațiile frumoase matematic dar irealizabile faptic (intercepție sigură < 50%)
    viable_gaps = [g for g in gaps if g["pass_probability"] > 50.0]
    return sorted(viable_gaps, key=lambda g: g["xt_value"], reverse=True)
