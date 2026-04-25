import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class XrayScreen extends StatefulWidget {
  const XrayScreen({super.key});

  @override
  State<XrayScreen> createState() => _XrayScreenState();
}

class _XrayScreenState extends State<XrayScreen> {
  late Future<List<dynamic>> _threatData;

  @override
  void initState() {
    super.initState();
    _threatData = _fetchThreatData();
  }

  Future<List<dynamic>> _fetchThreatData() async {
    final response =
        await http.get(Uri.parse('http://127.0.0.1:8000/api/xray/threat-map'));
    if (response.statusCode == 200) {
      final jsonResponse = json.decode(response.body);
      return jsonResponse['vulnerability_zones'] as List<dynamic>;
    } else {
      throw Exception('Eroare la încărcarea hărții de Threat (X-RAY)');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Theme.of(context).scaffoldBackgroundColor,
      padding: const EdgeInsets.all(32.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.radar, color: Colors.redAccent, size: 36),
              const SizedBox(width: 16),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text(
                    "X-RAY: VULNERABILITY MAP",
                    style: TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.w900,
                        color: Colors.white,
                        letterSpacing: 1.2),
                  ),
                  SizedBox(height: 4),
                  Text(
                    "Identificarea Spațiilor Libere (Expected Threat)",
                    style: TextStyle(
                        fontSize: 14,
                        color: Colors.white54,
                        fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              const Spacer(),
              ElevatedButton.icon(
                onPressed: () {
                  setState(() {
                    _threatData = _fetchThreatData();
                  });
                },
                icon: const Icon(Icons.sync),
                label: const Text("Load Latest Analysis"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.redAccent.withOpacity(0.2),
                  foregroundColor: Colors.redAccent,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                ),
              ),
            ],
          ),
          const SizedBox(height: 32),
          Expanded(
            child: FutureBuilder<List<dynamic>>(
              future: _threatData,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(
                      child:
                          CircularProgressIndicator(color: Colors.redAccent));
                } else if (snapshot.hasError) {
                  return Center(
                    child: Text('Conexiune AI eșuată: \${snapshot.error}',
                        style: const TextStyle(
                            color: Colors.redAccent,
                            fontSize: 16,
                            fontWeight: FontWeight.bold)),
                  );
                } else if (snapshot.hasData) {
                  final zones = snapshot.data!;
                  return Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFF1E1E1E),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white10),
                      boxShadow: const [
                        BoxShadow(
                            color: Colors.black26,
                            blurRadius: 20,
                            offset: Offset(0, 10)),
                      ],
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(16),
                      child: Padding(
                        padding: const EdgeInsets.all(40.0),
                        child: LayoutBuilder(
                          builder: (context, constraints) {
                            return CustomPaint(
                              size: Size(
                                  constraints.maxWidth, constraints.maxHeight),
                              painter: XRayPainter(zones: zones),
                            );
                          },
                        ),
                      ),
                    ),
                  );
                } else {
                  return const Center(
                      child: Text("Nu s-au detectat vulnerabilități.",
                          style: TextStyle(color: Colors.white)));
                }
              },
            ),
          ),
        ],
      ),
    );
  }
}

class XRayPainter extends CustomPainter {
  final List<dynamic> zones;

  XRayPainter({required this.zones});

  @override
  void paint(Canvas canvas, Size size) {
    // 1. DESENARE TEREN (Minimal Pitch) cu opacitate de 10%
    final pitchPaint = Paint()
      ..color = Colors.white.withOpacity(0.1)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    // Contur Teren
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), pitchPaint);
    // Linia de Mijloc
    canvas.drawLine(Offset(size.width / 2, 0),
        Offset(size.width / 2, size.height), pitchPaint);
    // Cercul de la Mijloc
    canvas.drawCircle(Offset(size.width / 2, size.height / 2),
        size.height * 0.15, pitchPaint);
    // Careul de 16m (Stânga - Apărarea adversă)
    canvas.drawRect(
        Rect.fromLTWH(
            0, size.height * 0.2, size.width * 0.18, size.height * 0.6),
        pitchPaint);
    // Careul de 16m (Dreapta - Apărarea noastră)
    canvas.drawRect(
        Rect.fromLTWH(size.width * 0.82, size.height * 0.2, size.width * 0.18,
            size.height * 0.6),
        pitchPaint);

    // 2. DESENARE VULNERABILITY ZONES (Gradient Map)
    const double gridWidth = 100.0;
    const double gridHeight = 100.0;

    for (var zone in zones) {
      final double x = (zone['x'] as num).toDouble();
      final double y = (zone['y'] as num).toDouble();
      final double radiusData = (zone['radius'] as num).toDouble();
      final double threat = (zone['threat_score'] as num).toDouble();

      // Conversie în coordonate pixel
      final cx = (x / gridWidth) * size.width;
      final cy = (y / gridHeight) * size.height;
      final radius = (radiusData / 100.0) *
          size.width; // Transformare bazată pe grid-ul procentual

      // Logica de culori (Neon Danger vs Safe)
      Color centerColor;
      if (threat >= 0.8) {
        centerColor = const Color(0xFFFF1E1E); // Roșu Aprins Neon
      } else if (threat > 0.5) {
        centerColor = const Color(0xFFFF8C00); // Portocaliu Intens
      } else {
        centerColor = const Color(0xFF00FFCC); // Verde/Cyan
      }

      // Heatmap effect cu RadialGradient
      final gradient = RadialGradient(
        colors: [
          centerColor.withOpacity(0.8), // Centrul foarte dens
          centerColor.withOpacity(0.4),
          centerColor.withOpacity(0.0), // Marginile disipate
        ],
        stops: const [0.0, 0.4, 1.0],
      );

      final paint = Paint()
        ..shader = gradient.createShader(
            Rect.fromCircle(center: Offset(cx, cy), radius: radius));

      canvas.drawCircle(Offset(cx, cy), radius, paint);

      // Indicator vizual al "Epicentrului" golului lăsat liber
      final centerDot = Paint()
        ..color = Colors.white.withOpacity(0.9)
        ..style = PaintingStyle.fill;
      canvas.drawCircle(Offset(cx, cy), 3.0, centerDot);

      // Scor text deasupra epicentrului (pentru extra precizie)
      final textSpan = TextSpan(
        text: threat.toStringAsFixed(2),
        style: TextStyle(
          color: Colors.white,
          fontSize: 12,
          fontWeight: FontWeight.bold,
          shadows: [Shadow(color: centerColor, blurRadius: 4)],
        ),
      );
      final textPainter = TextPainter(
        text: textSpan,
        textDirection: TextDirection.ltr,
      );
      textPainter.layout();
      textPainter.paint(canvas, Offset(cx - textPainter.width / 2, cy - 18));
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
