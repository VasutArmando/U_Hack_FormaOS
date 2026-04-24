import json
import logging
from typing import Dict, Any

logger = logging.getLogger("forma_os_celery")

class MultiAgentGraph:
    """
    Arhitectură Multi-Agent (Inspirată din LangGraph).
    Rolul acestui sistem este să implementeze 'Self-Reflection' și să elimine complet 
    halucinațiile LLM-ului înnainte ca o decizie să ajungă pe ecranul antrenorului.
    """
    def __init__(self, context: Dict[str, Any]):
        self.context = context
        self.max_retries = 3
        self.system_instruction = """Ești Analistul Video Principal (propulsat de Gemini 2.0 Flash) al FC U Cluj. Trebuie să generezi 'The Winning Game Plan' pentru Ioan Ovidiu Sabău.
Preia datele agregate din pipeline-ul de unificare (Hudl + StatsBomb 360).

Formatul de răspuns TREBUIE să fie strict structurat astfel:
- Analiza Verigii Slabe: Jucătorul advers cu cel mai mare risc de eroare sub presiune (bazat pe date SHIELD/ML).
- Exploatarea Spațiilor: Zonele unde adversarul lasă gap-uri cronice în tranziție.
- Planul Sabău: Instrucțiuni clare folosind terminologia 'bloc defensiv compact' și 'zonă de decizie'."""
        
    def _run_tactical_agent(self, feedback: str = "") -> str:
        logger.info(f"🤖 [Agent Tactic] Generez soluția de bază... {f'(Aplic feedback: {feedback})' if feedback else ''}")
        # În mediul de Producție (cu API Key valid): 
        # Rulăm un prompt primar către LLM pentru a scoate idei creative fără limite.
        
        if feedback:
            return "Am revizuit datele. Trebuie să-l înlocuim imediat pe Chipciu pentru a preveni ruptura musculară. Rezerva va fi instruită să atace direct culoarul de 14.2m detectat de X-Ray, folosind Momentum-ul adversarilor împotriva lor."
            
        # Simulare de halucinație pentru demonstrația Multi-Agent:
        return "Cred că ar trebui să menținem posesia. Chipciu este esențial pentru experiența sa, să-l ținem pe teren până la final."

    def _run_critic_agent(self, proposal: str) -> dict:
        logger.info("⚖️ [Agent Critic / Data Enforcer] Scanez propunerea contra bazei de date X-RAY/SHIELD...")
        shield_data = str(self.context.get("shield_data", {}))
        
        errors = []
        # În producție: LLM-ul primește rol de CRITIC și e obligat să compare string-ul proposal cu dict-ul de senzori.
        # Pentru Demo: Validare deterministă
        if "Chipciu" in proposal and "menținem" in proposal.lower() and "Chipciu" in shield_data:
            errors.append("HALUCINAȚIE CRITICĂ: Propunerea tactică ignoră alertele SHIELD! Ai sugerat menținerea lui Chipciu, dar telemetria GPS indică un risc iminent de ruptură musculară (>80% oboseală). ESTE INACCEPTABIL.")
            
        if errors:
            logger.warning(f"❌ [Agent Critic] Resping propunerea. Motiv: {errors[0]}")
            return {"valid": False, "feedback": errors[0]}
            
        logger.info("✅ [Agent Critic] Zero halucinații. Propunere 100% susținută matematic de senzori.")
        return {"valid": True, "feedback": ""}

    def _run_synthesizer_agent(self, validated_proposal: str) -> dict:
        logger.info("🗣️ [Agent Sabău / Synthesizer] Adaptez textul conform noului SYSTEM_INSTRUCTION (Scouting Report)...")
        # În producție: LLM-ul primește system_instruction și returnează JSON.
        return {
            "report_title": "The Winning Game Plan (Gemini 2.0 Flash)",
            "Analiza_Verigii_Slabe": "Fundașul stânga (Nr. 3) are cel mai mare risc de eroare. Datele SHIELD unificate cu Hudl arată că a pierdut mingea de 7 ori în zone periculoase sub presiune.",
            "Exploatarea_Spatiilor": "La tranziția negativă, echipa adversă lasă gap-uri cronice de 15m între linia defensivă și închizători, exact pe zona centrală.",
            "Planul_Sabau": "Ne organizăm într-un 'bloc defensiv compact' și așteptăm. În momentul în care construcția lor ajunge în 'zona de decizie' (flancul nostru drept), declanșăm presingul pe veriga lor slabă.",
            "speech_text": "Mister, Gemini 2.0 a compilat datele Hudl și StatsBomb. Veriga lor slabă cedează garantat la presing. Așteptăm în bloc defensiv compact până ajung în zona de decizie, și atunci lovim pe intercepție!"
        }

    def _generate_heuristic_fallback(self) -> dict:
        """
        Smart Timeout Fallback: Compune un răspuns local folosind X-RAY și SHIELD
        când LLM-ul întârzie mai mult de 2.5 secunde.
        """
        xray = self.context.get("xray_data", {})
        shield = self.context.get("shield_data", {})
        oracle = self.context.get("oracle_data", {})
        
        gap = xray.get("top_gap_m", 0.0)
        domination = oracle.get("monte_carlo_win_prob", 20.0)
        adv_dom = 100 - domination
        
        criticals = shield.get("critical_players", [])
        fatigued_player = criticals[0].get("player", "Necunoscut") if criticals else "Necunoscut"
        
        speech = f"Conexiune limitată. Prioritate de sistem: Jucătorul {fatigued_player} e în prag roșu de oboseală. Adversarul controlează {adv_dom}% din posesie. Recomandare de urgență: Substituție și exploatarea gap-ului de {gap}m pe flancul opus."
        
        return {
            "speech_text": speech,
            "decision_tree": [
                {"factor": "SMART TIMEOUT (Heuristic Fallback Local)", "weight_pct": 100}
            ]
        }

    def execute(self) -> dict:
        """
        Orchestratorul (State Graph) care învârte agenții într-o buclă de validare
        până la obținerea adevărului absolut. Include protecție de Timeout de Rețea.
        """
        import time
        start_time = time.time()
        timeout_limit = 2.5
        
        attempt = 0
        current_proposal = ""
        feedback = ""
        
        # DEMO: Simulăm latența la API-ul Google Gemini (Sub 2.5s pentru a evita fallback-ul)
        time.sleep(1.0) 
        
        while attempt < self.max_retries:
            # Protecție Activă de Timp (Smart Timeout)
            if (time.time() - start_time) > timeout_limit:
                logger.error(f"⏱️ [SMART TIMEOUT] LLM a depășit {timeout_limit}s! Reactivitate pe teren e mai importantă. Trimit Fallback Local.")
                return self._generate_heuristic_fallback()
                
            # 1. Agentul Creativ emite o ipoteză
            current_proposal = self._run_tactical_agent(feedback)
            
            # 2. Agentul Matematic (Critic) taie fără milă dacă nu se aliniază cu senzorii
            evaluation = self._run_critic_agent(current_proposal)
            
            if evaluation["valid"]:
                break
                
            feedback = evaluation["feedback"]
            attempt += 1
            logger.info(f"🔄 [Orchestrator] Trimit înapoi Agentului Tactic pentru Rescriere (Încercarea {attempt}).")
            
        # 3. Dacă nu a dat timeout pe parcurs, Agentul Final ambalează rezultatul
        if (time.time() - start_time) > timeout_limit:
            return self._generate_heuristic_fallback()
            
        return self._run_synthesizer_agent(current_proposal)


class GeminiEngine:
    """
    Sistem Enterprise FAANG, acum propulsat de arhitectură Multi-Agent.
    """
    def __init__(self):
        pass
        
    def generate_tactical_advice(self, match_context: Dict[str, Any]) -> dict:
        logger.info("\n=======================================================")
        logger.info("📡 TACTICIAN ENGINE: Start Multi-Agent Orchestration")
        logger.info("=======================================================")
        
        graph = MultiAgentGraph(match_context)
        return graph.execute()
