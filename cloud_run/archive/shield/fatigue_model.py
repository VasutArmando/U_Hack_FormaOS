class FatigueModel:
    @staticmethod
    def calculate(player_data_window):
        if not player_data_window:
            return 0.0
        avg_hr = sum(d.get('heart_rate', 0) for d in player_data_window) / len(player_data_window)
        max_accel = max(d.get('accel', 0) for d in player_data_window)
        base_fatigue = (avg_hr / 200.0) * 100 
        spike_fatigue = (max_accel / 10.0) * 20
        return min(base_fatigue + spike_fatigue, 100.0)

    @staticmethod
    def predict_fatigue(current_fatigue: float, match_minute: int, player_role: str = "WINGER"):
        """
        Modul Predictiv: Calculează curba de degradare în timp real.
        Evităm rupturile musculare acționând PRE-EMPTIV.
        """
        rates = {
            "WINGER": 0.55,     # Extremele depun efort exploziv constant
            "MIDFIELDER": 0.35, # Efort constant, dar mai puțin exploziv
            "DEFENDER": 0.15    # Efort de anduranță
        }
        
        # Cât % din performanța musculară pierde pe minut
        degradation_rate = rates.get(player_role, 0.25)
        
        # Proiecția pe fereastra tactică de 10 minute
        predicted_fatigue_10m = current_fatigue + (degradation_rate * 10)
        
        minutes_to_critical = 0
        if current_fatigue < 80.0:
            minutes_to_critical = (80.0 - current_fatigue) / degradation_rate
            
        # Alerta se activează dacă va atinge pragul roșu (>80%) în următoarele 10 minute, 
        # chiar dacă ACUM este pe galben (ex: 75%).
        is_warning = predicted_fatigue_10m >= 80.0 and current_fatigue < 80.0
        
        return {
            "predicted_fatigue_10m": min(predicted_fatigue_10m, 100.0),
            "minutes_to_critical": int(minutes_to_critical),
            "preemptive_warning": is_warning
        }
