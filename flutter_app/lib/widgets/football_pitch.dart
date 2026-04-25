import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../models/match_data.dart';

class FootballPitch extends StatelessWidget {
  final List<TacticalGap> gaps;

  const FootballPitch({super.key, required this.gaps});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: double.infinity,
      decoration: BoxDecoration(
        color: const Color(0xFF1B4332), // Deep grass green
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white24, width: 2),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final double width = constraints.maxWidth;
          final double height = constraints.maxHeight;

          return Stack(
            fit: StackFit.expand,
            children: [
              CustomPaint(
                painter: _PitchPainter(),
              ),
              ...gaps.map((gap) => _buildGapOverlay(gap, width, height)),
            ],
          );
        },
      ),
    );
  }

  Widget _buildGapOverlay(TacticalGap gap, double pitchWidth, double pitchHeight) {
    // Assume pitch coordinates range from -100 to 100 for both X and Y
    // X: -100 (left) to 100 (right)
    // Y: -100 (top) to 100 (bottom)
    
    // Size of the gap bounding box
    final double pixelWidth = (gap.w / 200) * pitchWidth;
    final double pixelHeight = (gap.h / 200) * pitchHeight;

    // Convert gap center coordinates to pixels
    // Subtract half width/height so the gap is perfectly centered at (gap.x, gap.y)
    final double left = ((gap.x + 100) / 200 * pitchWidth) - (pixelWidth / 2);
    final double top = ((gap.y + 100) / 200 * pitchHeight) - (pixelHeight / 2);

    final Color severityColor = gap.severity.toLowerCase() == 'critical' 
        ? const Color(0xFFFF3366) 
        : const Color(0xFFFFD166);

    return Positioned(
      left: left,
      top: top,
      child: Container(
        width: pixelWidth,
        height: pixelHeight,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(100), // Ellipse like appearance
          gradient: RadialGradient(
            colors: [
              severityColor.withValues(alpha: 0.5),
              severityColor.withValues(alpha: 0.1),
              Colors.transparent,
            ],
            stops: const [0.0, 0.6, 1.0],
          ),
        ),
        child: Center(
          child: OverflowBox(
            maxWidth: double.infinity,
            maxHeight: double.infinity,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFF181818),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: severityColor, width: 1.5),
                boxShadow: [
                  BoxShadow(
                    color: severityColor.withValues(alpha: 0.3),
                    blurRadius: 8,
                    spreadRadius: 2,
                  )
                ]
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    gap.severity.toLowerCase() == 'critical' ? Icons.warning_amber_rounded : Icons.info_outline,
                    color: severityColor,
                    size: 14,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    gap.location.toUpperCase(),
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.5,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _PitchPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withValues(alpha: 0.4)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    final double width = size.width;
    final double height = size.height;

    // Field boundaries
    canvas.drawRect(Rect.fromLTWH(0, 0, width, height), paint);

    // Halfway line
    canvas.drawLine(Offset(width / 2, 0), Offset(width / 2, height), paint);

    // Center circle
    final center = Offset(width / 2, height / 2);
    canvas.drawCircle(center, height * 0.15, paint);

    // Center spot
    final spotPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.6)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, 4, spotPaint);

    // Left Penalty Box
    canvas.drawRect(Rect.fromLTWH(0, height * 0.25, width * 0.18, height * 0.5), paint);
    // Left Goal Box
    canvas.drawRect(Rect.fromLTWH(0, height * 0.38, width * 0.06, height * 0.24), paint);
    // Left Penalty Arc
    canvas.drawArc(
      Rect.fromCenter(center: Offset(width * 0.18, height / 2), width: height * 0.15, height: height * 0.15),
      -math.pi / 3,
      2 * math.pi / 3,
      false,
      paint,
    );

    // Right Penalty Box
    canvas.drawRect(Rect.fromLTWH(width - (width * 0.18), height * 0.25, width * 0.18, height * 0.5), paint);
    // Right Goal Box
    canvas.drawRect(Rect.fromLTWH(width - (width * 0.06), height * 0.38, width * 0.06, height * 0.24), paint);
    // Right Penalty Arc
    canvas.drawArc(
      Rect.fromCenter(center: Offset(width - (width * 0.18), height / 2), width: height * 0.15, height: height * 0.15),
      2 * math.pi / 3,
      2 * math.pi / 3,
      false,
      paint,
    );

    // Corner Arcs
    final cornerRadius = height * 0.03;
    canvas.drawArc(Rect.fromCircle(center: const Offset(0, 0), radius: cornerRadius), 0, math.pi / 2, false, paint);
    canvas.drawArc(Rect.fromCircle(center: Offset(width, 0), radius: cornerRadius), math.pi / 2, math.pi / 2, false, paint);
    canvas.drawArc(Rect.fromCircle(center: Offset(0, height), radius: cornerRadius), -math.pi / 2, math.pi / 2, false, paint);
    canvas.drawArc(Rect.fromCircle(center: Offset(width, height), radius: cornerRadius), -math.pi, math.pi / 2, false, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
