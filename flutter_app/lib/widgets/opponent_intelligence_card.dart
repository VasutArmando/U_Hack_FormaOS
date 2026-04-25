import 'package:flutter/material.dart';

class OpponentIntelligenceCard extends StatelessWidget {
  const OpponentIntelligenceCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF121212), // Temă dark-mode premium
      padding: const EdgeInsets.all(24.0),
      child: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 850),
          decoration: BoxDecoration(
            color: const Color(0xFF1E1E1E),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.amberAccent.withValues(alpha: 0.5), width: 1.5),
            boxShadow: [
              BoxShadow(color: Colors.amberAccent.withValues(alpha: 0.1), blurRadius: 30, offset: const Offset(0, 10)),
            ],
          ),
          child: ListView(
            padding: const EdgeInsets.all(40),
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.bolt, color: Colors.amberAccent, size: 28),
                          const SizedBox(width: 8),
                          const Text("GEMINI 2.0 FLASH", style: TextStyle(color: Colors.amberAccent, fontWeight: FontWeight.bold, letterSpacing: 1.5, fontSize: 14)),
                        ],
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        "THE WINNING GAME PLAN",
                        style: TextStyle(fontSize: 32, fontWeight: FontWeight.w900, color: Colors.white),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        "HUDL + STATSBOMB DATA FUSION",
                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white54, letterSpacing: 1.2),
                      ),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.amberAccent.withValues(alpha: 0.1),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.psychology, size: 48, color: Colors.amberAccent),
                  ),
                ],
              ),
              const SizedBox(height: 30),
              const Divider(color: Colors.white24, thickness: 1),
              const SizedBox(height: 30),
              
              _buildInteractiveCard(
                title: "ANALIZA VERIGII SLABE",
                icon: Icons.troubleshoot,
                content: "Fundașul stânga (Nr. 3) cedează sub presiune. În ultimele 5 meciuri, conform datelor SHIELD și unificării Hudl, a pierdut mingea de 7 ori în propria treime sub presing agresiv.",
                color: Colors.redAccent,
              ),
              const SizedBox(height: 24),
              
              _buildInteractiveCard(
                title: "EXPLOATAREA SPAȚIILOR",
                icon: Icons.zoom_out_map,
                content: "La tranziția negativă, adversarul lasă gap-uri cronice de 15m între linia defensivă și închizători pe zona centrală. Retragerea lor nu este sincronizată.",
                color: Colors.orangeAccent,
              ),
              const SizedBox(height: 24),
              
              _buildInteractiveCard(
                title: "PLANUL SABĂU",
                icon: Icons.sports_kabaddi,
                content: "Ne organizăm echipa într-un 'bloc defensiv compact'. Când construcția lor ajunge în 'zona de decizie' (flancul nostru drept), declanșăm presing sufocant exclusiv pe veriga lor slabă.",
                color: Colors.greenAccent,
              ),
              
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInteractiveCard({required String title, required IconData icon, required String content, required Color color}) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.2), width: 1.5),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: color, size: 28),
          ),
          const SizedBox(width: 24),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color, letterSpacing: 1.1)),
                const SizedBox(height: 12),
                Text(content, style: const TextStyle(fontSize: 16, height: 1.6, color: Colors.white70)),
              ],
            ),
          )
        ],
      ),
    );
  }
}
