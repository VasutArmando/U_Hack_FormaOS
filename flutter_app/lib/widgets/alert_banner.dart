import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/match_cubit.dart';

class AlertBanner extends StatelessWidget {
  const AlertBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<MatchCubit, MatchState>(
      builder: (context, state) {
        if (state is MatchLoaded) {
          final analysisData = state.matchData['analysis_data'] ?? {};
          final xray = analysisData['xray_analysis'] ?? {};
          
          final String? warning = xray['compactness_warning'];
          final double? gapWidth = xray['top_gap_m'];
          final double? xtThreat = xray['xt_threat'];
          final double? passProb = xray['pass_probability'];
          
          List<Widget> banners = [];
          
          // 1. Banner Filosofie Tactica (Compactness)
          if (warning != null && warning.isNotEmpty) {
            banners.add(_buildBanner(
              color: Colors.amberAccent,
              icon: Icons.warning_amber_rounded,
              title: "AVERTISMENT TACTIC: RUPERE DE RITM",
              message: warning,
            ));
          }
          
          // 2. Banner X-RAY Gap Exploitable (Pass Probability)
          if (gapWidth != null && passProb != null && passProb > 60.0) {
            banners.add(_buildBanner(
              color: Colors.greenAccent,
              icon: Icons.filter_center_focus,
              title: "X-RAY: GAP EXPLOATABIL DETECTAT",
              message: "Spațiu liber: \${gapWidth.toStringAsFixed(1)}m.\nProbabilitate de pasă reușită: \${passProb.toStringAsFixed(0)}% (xT: \${xtThreat?.toStringAsFixed(2)})",
            ));
          }
          
          // 3. Banner SHIELD: Predictor de Ruptură Musculară
          final shield = analysisData['shield_analysis'] ?? {};
          final List alerts = shield['alerts'] ?? [];
          for (var alert in alerts) {
            if (alert['type'] == 'PREDICTIVE') {
              banners.add(_buildBanner(
                color: Colors.redAccent,
                icon: Icons.monitor_heart,
                title: "SHIELD: ALARMĂ PRE-EMPTIVĂ OBOSEALĂ",
                message: alert['message'],
              ));
            }
          }
          
          if (banners.isNotEmpty) {
            return SafeArea(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: banners,
              ),
            );
          }
        }
        
        return const SizedBox.shrink();
      },
    );
  }

  Widget _buildBanner({required Color color, required IconData icon, required String title, required String message}) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 500),
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: color.withOpacity(0.9),
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(color: color.withOpacity(0.4), blurRadius: 15, spreadRadius: 2)
        ],
        border: Border.all(color: Colors.white, width: 1.5)
      ),
      child: Row(
        children: [
          Icon(icon, color: Colors.black, size: 36),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title, 
                  style: const TextStyle(color: Colors.black, fontWeight: FontWeight.w900, fontSize: 12, letterSpacing: 1.5)
                ),
                const SizedBox(height: 4),
                Text(
                  message,
                  style: const TextStyle(color: Colors.black87, fontWeight: FontWeight.bold, fontSize: 16),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
