import numpy as np

def compute_pitch_control(
    home_positions: list[tuple],
    away_positions: list[tuple],
    grid_size: int = 100
) -> dict:
    """
    Returnează o matrice grid_size x grid_size:
    +1 = controlat de home, -1 = controlat de away, 0 = contestat
    """
    xs = np.linspace(0, 105, grid_size)
    ys = np.linspace(0, 68, grid_size)

    home = np.array(home_positions)
    away = np.array(away_positions)

    # Calculăm distanța minimă pentru fiecare punct din grid
    control = np.zeros((grid_size, grid_size))
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            pt = np.array([x, y])
            d_home = np.min(np.linalg.norm(home - pt, axis=1))
            d_away = np.min(np.linalg.norm(away - pt, axis=1))
            
            if abs(d_home - d_away) < 2.0:  # zonă contestată (±2m)
                control[j, i] = 0
            else:
                control[j, i] = 1 if d_home < d_away else -1
    
    home_pct = round(np.mean(control > 0) * 100, 1)
    away_pct = round(np.mean(control < 0) * 100, 1)

    return {
        "control_matrix": control.tolist(), # trimis la Flutter pentru Canvas
        "home_control_pct": home_pct,
        "away_control_pct": away_pct
    }
