import numpy as np
from collections import Counter

def simulate_match(home_xg: float, away_xg: float, n: int = 1000) -> dict:
    """
    Distribuție Poisson pentru goluri bazată pe xG (Expected Goals).
    xG-ul vine din StatsBomb data sau estimat din statistici istorice.
    """
    home_goals = np.random.poisson(home_xg, n)
    away_goals = np.random.poisson(away_xg, n)
    
    results = {
        "home_win_pct": round(np.mean(home_goals > away_goals) * 100, 1),
        "draw_pct": round(np.mean(home_goals == away_goals) * 100, 1),
        "away_win_pct": round(np.mean(home_goals < away_goals) * 100, 1),
    }
    
    scores = Counter(zip(home_goals.tolist(), away_goals.tolist()))
    top_score, top_count = scores.most_common(1)[0]
    results["most_likely_score"] = f"{top_score[0]}-{top_score[1]}"
    results["most_likely_pct"] = round(top_count / n * 100, 1)
    
    return results
