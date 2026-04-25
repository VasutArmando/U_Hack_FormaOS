import 'package:flutter/material.dart';

class ScoutingReportDashboard extends StatelessWidget {
  const ScoutingReportDashboard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.grey[200],
      padding: const EdgeInsets.all(24.0),
      child: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 850),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: const [
              BoxShadow(
                color: Colors.black12,
                blurRadius: 15,
                offset: Offset(0, 5),
              ),
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
                      const Text(
                        "U CLUJ - SCOUTING REPORT",
                        style: TextStyle(fontSize: 28, fontWeight: FontWeight.w900, color: Colors.black87),
                      ),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.redAccent.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(color: Colors.redAccent),
                        ),
                        child: const Text(
                          "CONFIDENTIAL | MATCH PREPARATION",
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.redAccent),
                        ),
                      ),
                    ],
                  ),
                  Icon(Icons.shield, size: 60, color: Colors.grey[300]),
                ],
              ),
              const SizedBox(height: 20),
              const Divider(height: 1, thickness: 2),
              const SizedBox(height: 30),
              
              _buildSection(
                title: "🔴 KEY THREAT",
                icon: Icons.warning_amber_rounded,
                content: "Playmaker-ul lor principal dictează jocul (din Passing Networks, are scorul maxim de Betweenness Centrality). Trebuie să-l blocăm aplicând marcaj om la om agresiv, tăind liniile de pasă către el dinspre fundașii centrali.",
                color: Colors.redAccent,
              ),
              const SizedBox(height: 30),
              
              _buildSection(
                title: "🎯 EXPLOITABLE WEAKNESS",
                icon: Icons.radar,
                content: "Adversarul devine vulnerabil pe flancul drept defensiv în minutele 70-85. Aripa lor stângă suferă o cădere de ritm masivă, lăsând un 'gap' de 14 metri exploatabil (identificat de modulul Temporal Vulnerabilities).",
                color: Colors.orangeAccent,
              ),
              const SizedBox(height: 30),
              
              _buildSection(
                title: "🧠 SABĂU STRATEGY",
                icon: Icons.lightbulb_outline,
                content: "Menținem 'blocul defensiv compact' la 35 de metri de poartă. La recuperare (tranziție pozitivă rapidă), folosim pe cineva proaspăt (rezervă) pentru o 'intrare în adâncime' direct pe culoarul eliberat de pe flancul lor.",
                color: Colors.blueAccent,
              ),
              
              const SizedBox(height: 40),
              Center(
                child: Text(
                  "Generat automat de TACTICIAN Engine (Multi-Agent AI)",
                  style: TextStyle(color: Colors.grey[500], fontStyle: FontStyle.italic),
                ),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSection({required String title, required IconData icon, required String content, required Color color}) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.04),
        border: Border(left: BorderSide(color: color, width: 6)),
        borderRadius: const BorderRadius.only(topRight: Radius.circular(8), bottomRight: Radius.circular(8)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 28),
              const SizedBox(width: 12),
              Text(title, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
            ],
          ),
          const SizedBox(height: 16),
          Text(content, style: const TextStyle(fontSize: 16, height: 1.6, color: Colors.black87)),
        ],
      ),
    );
  }
}
