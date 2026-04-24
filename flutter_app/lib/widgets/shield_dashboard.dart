import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class ShieldDashboard extends StatelessWidget {
  const ShieldDashboard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      color: const Color(0xFF0D0D0D),
      child: Row(
        children: [
          Expanded(
            flex: 1,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text("SHIELD MEDICAL", style: TextStyle(fontSize: 28, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5)),
                const SizedBox(height: 8),
                const Text("Analiză biomecanică live vs Baseline", style: TextStyle(color: Colors.grey, fontSize: 16)),
                const SizedBox(height: 48),
                _buildPlayerCard("Atacant Central (Nr. 9)", "Risc: CRITIC (>80% LIA)", Colors.redAccent),
                const SizedBox(height: 16),
                _buildPlayerCard("Mijlocaș Defensiv (Nr. 5)", "Risc: SCĂZUT", Colors.greenAccent),
              ],
            ),
          ),
          Expanded(
            flex: 2,
            child: Padding(
              padding: const EdgeInsets.all(32.0),
              child: _buildRadarChart(),
            ),
          )
        ],
      ),
    );
  }

  Widget _buildPlayerCard(String name, String status, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(8),
        border: Border(left: BorderSide(color: color, width: 4)),
        boxShadow: [
          BoxShadow(color: color.withOpacity(0.1), blurRadius: 10, offset: const Offset(0, 4))
        ]
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 6),
          Text(status, style: TextStyle(color: color, fontWeight: FontWeight.w900)),
        ],
      ),
    );
  }

  Widget _buildRadarChart() {
    return RadarChart(
      RadarChartData(
        dataSets: [
          RadarDataSet(
            fillColor: Colors.blueAccent.withOpacity(0.15),
            borderColor: Colors.blueAccent,
            entryRadius: 4,
            dataEntries: const [
              RadarEntry(value: 100), // Viteza sprint baseline
              RadarEntry(value: 100), // Acceleratie baseline
              RadarEntry(value: 100), // Integritate genunchi
              RadarEntry(value: 100), // Agilitate
              RadarEntry(value: 100), // Rezistenta
            ],
          ),
          RadarDataSet(
            fillColor: Colors.redAccent.withOpacity(0.35),
            borderColor: Colors.redAccent,
            entryRadius: 4,
            dataEntries: const [
              RadarEntry(value: 70), // Viteză curentă (scădere 30%)
              RadarEntry(value: 65), // Accelerație
              RadarEntry(value: 20), // Integritate Genunchi (Deviație 4.2 grade)
              RadarEntry(value: 50), // Agilitate
              RadarEntry(value: 45), // Rezistență cardio
            ],
          ),
        ],
        radarBackgroundColor: Colors.transparent,
        borderData: FlBorderData(show: false),
        radarBorderData: const BorderSide(color: Colors.white24, width: 1.5),
        tickBorderData: const BorderSide(color: Colors.white12, width: 1),
        tickCount: 4,
        ticksTextStyle: const TextStyle(color: Colors.transparent),
        getTitle: (index, angle) {
          switch (index) {
            case 0: return const RadarChartTitle(text: 'Viteză Max', positionPercentageOffset: 0.1);
            case 1: return const RadarChartTitle(text: 'Accelerație', positionPercentageOffset: 0.1);
            case 2: return const RadarChartTitle(text: 'Integritate Articulară', positionPercentageOffset: 0.1);
            case 3: return const RadarChartTitle(text: 'Agilitate', positionPercentageOffset: 0.1);
            case 4: return const RadarChartTitle(text: 'Rezistență', positionPercentageOffset: 0.1);
            default: return const RadarChartTitle(text: '');
          }
        },
        titleTextStyle: const TextStyle(color: Colors.white70, fontWeight: FontWeight.bold, fontSize: 12),
      ),
      swapAnimationDuration: const Duration(milliseconds: 600),
      swapAnimationCurve: Curves.easeOutBack,
    );
  }
}
