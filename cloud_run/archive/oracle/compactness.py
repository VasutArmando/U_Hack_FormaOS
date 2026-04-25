class CompactnessAnalyzer:
    """
    Sistem de validare a filosofiei tactice a clubului.
    Coach Sabău solicită un bloc defensiv ultra-compact pentru a preveni contraatacurile.
    """
    @staticmethod
    def calculate_team_length(home_positions):
        """
        Măsoară distanța (în metri) pe axa longitudinală (X) între:
        - Ultimul apărător (excluzând portarul)
        - Cel mai avansat atacant.
        """
        if not home_positions or len(home_positions) < 2:
            return 0.0
            
        # Excludem portarul (Presupunem că portarul e singurul cu X < 10.0m de poartă)
        field_players_x = [p[0] for p in home_positions if p[0] > 10.0]
        
        # Fallback dacă toți sunt atacanți/mijlocași (ex: corner)
        if not field_players_x:
            field_players_x = [p[0] for p in home_positions]
            
        min_x = min(field_players_x)
        max_x = max(field_players_x)
        
        return round(max_x - min_x, 1)

    @staticmethod
    def evaluate_block(team_length_m):
        """
        Dacă echipa se întinde pe mai mult de 40 de metri, spațiile dintre linii
        devin uriașe, riscând ca un decar advers să primească mingea între linii.
        """
        if team_length_m > 40.0:
            return {
                "status": "FRAGMENTAT",
                "warning": f"Echipa prea lungă ({team_length_m}m). Risc major de contraatac advers pe axul central."
            }
        elif team_length_m < 25.0:
            # Opțional, dacă e prea strânsă, adversarul poate schimba direcția pe flancuri
            return {
                "status": "PREA_COMPACT",
                "warning": f"Echipa stă pe un front prea strâns ({team_length_m}m). Vulnerabili la schimbări de direcție pe flancuri."
            }
        else:
            return {
                "status": "OPTIM",
                "warning": None
            }
