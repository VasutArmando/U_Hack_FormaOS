import networkx as nx
import random

def get_opponent_passing_network(opponent_name: str = "CFR Cluj") -> dict:
    """
    Simulează și procesează datele StatsBomb din ultimele 3 meciuri ale adversarului.
    Folosește networkx pentru a construi rețeaua și a calcula:
    - Betweenness Centrality (playmaker/inima echipei)
    - Degree Centrality (cel mai des vizat jucător cu pase)
    """
    
    # Roster simulat (focus pe CFR Cluj, cum a cerut antrenorul)
    if "cfr" in opponent_name.lower():
        players = [
            "Sava", "Manea", "Kresic", "Ilie", "Camora", 
            "Muhar", "Tachtsidis", "Avounou", "Deac", "Otele", "Birligea"
        ]
    else:
        players = [f"Player_{i}" for i in range(1, 12)]

    G = nx.DiGraph()

    for player in players:
        G.add_node(player)

    # Generăm graful de pase orientat cu weight (volumul de pase)
    for p1 in players:
        for p2 in players:
            if p1 != p2:
                # O șansă ca o pasă să fi avut loc (jucătorii apropiați pasează mai mult, folosim un random ponders)
                if random.random() > 0.6:
                    weight = random.randint(1, 20)
                    G.add_edge(p1, p2, weight=weight)

    # 1. Betweenness Centrality - Ne arată Playmaker-ul, cel prin care trec majoritatea atacurilor
    betweenness = nx.betweenness_centrality(G, weight='weight')
    playmaker = max(betweenness, key=betweenness.get)

    # 2. In-Degree Centrality - Ne arată Jucătorul care primește cele mai multe pase
    in_degree = nx.in_degree_centrality(G)
    most_targeted = max(in_degree, key=in_degree.get)

    # Pregătim JSON-ul pentru Flutter (noduri și edges)
    # Nodurile conțin coeficientul pentru mărirea cercului în UI
    nodes = []
    for p in players:
        nodes.append({
            "id": p,
            "label": p,
            "betweenness_score": round(betweenness[p], 3),
            "degree_score": round(in_degree[p], 3),
            "is_playmaker": (p == playmaker)
        })

    # Liniile conțin "volume" pentru grosimea (thickness) liniei dintre jucători în Flutter
    edges = []
    for u, v, d in G.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "volume": d['weight']
        })

    return {
        "opponent": opponent_name,
        "insights": {
            "playmaker": playmaker,
            "most_frequent_target": most_targeted,
            "tactical_advice": f"{playmaker} dictează jocul ({round(betweenness[playmaker] * 100, 1)}% control trafic). Blocarea lui va rupe liniile de pasare ale lui {opponent_name}."
        },
        "network": {
            "nodes": nodes,
            "edges": edges
        }
    }
