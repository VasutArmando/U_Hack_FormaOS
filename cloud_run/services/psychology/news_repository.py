from typing import List, Dict
from datetime import datetime, timedelta

class NewsRepository:
    """
    Gestionarea surselor de știri (Mock implementation).
    Decuplată pentru a permite în viitor integrarea cu un scraper real (ex: Gazeta Sporturilor, Fanatik).
    """
    def __init__(self):
        now = datetime.now()
        self.mock_news = [
            {
                "source": "Gazeta Sporturilor",
                "title": "Scandal în vestiarul adversarilor!",
                "content": "Jucătorii străini s-au plâns de întârzieri salariale de peste 3 luni. Antrenorul principal a părăsit antrenamentul de ieri nervos, refuzând să dea declarații.",
                "timestamp": (now - timedelta(days=1)).isoformat()
            },
            {
                "source": "Fanatik",
                "title": "Presiune uriașă din partea conducerii",
                "content": "Finanțatorul echipei le-a dat un ultimatum jucătorilor. Dacă nu câștigă acest meci, vor intra în cantonament prelungit pe termen nelimitat.",
                "timestamp": (now - timedelta(hours=12)).isoformat()
            },
            {
                "source": "DigiSport",
                "title": "Declarații belicoase înainte de meci",
                "content": "Căpitanul echipei adverse: 'Ieșim pe teren să dăm totul. Nu ne interesează cum jucăm, trebuie să luăm cele 3 puncte chiar dacă va fi nevoie de joc dur.'",
                "timestamp": (now - timedelta(hours=5)).isoformat()
            }
        ]

    def get_latest_news(self, opponent_name: str = "Adversar") -> List[Dict]:
        """ Returnează ultimele știri relevante despre adversar """
        return self.mock_news
