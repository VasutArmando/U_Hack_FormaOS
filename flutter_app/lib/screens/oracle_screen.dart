import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class OracleScreen extends StatefulWidget {
  const OracleScreen({super.key});

  @override
  State<OracleScreen> createState() => _OracleScreenState();
}

class _OracleScreenState extends State<OracleScreen> {
  late Future<Map<String, dynamic>> _networkData;

  @override
  void initState() {
    super.initState();
    _networkData = _fetchNetworkData();
  }

  Future<Map<String, dynamic>> _fetchNetworkData() async {
    // Apel către backend-ul de FastAPI (Oracle Data Factory)
    final response = await http.get(Uri.parse('http://127.0.0.1:8000/api/oracle/passing-network'));

    if (response.statusCode == 200) {
      final jsonResponse = json.decode(response.body);
      return jsonResponse['data'] as Map<String, dynamic>;
    } else {
      throw Exception('Failed to load passing network data');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Theme.of(context).scaffoldBackgroundColor, // Integrare nativă cu Dark Mode
      padding: const EdgeInsets.all(32.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.hub, color: Color(0xFF00FFCC), size: 36),
              const SizedBox(width: 16),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text(
                    "ORACLE: PASSING NETWORKS",
                    style: TextStyle(fontSize: 32, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.2),
                  ),
                  SizedBox(height: 4),
                  Text(
                    "Detecting Opponent Hubs & Passing Flow Patterns",
                    style: TextStyle(fontSize: 14, color: Colors.white54, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              const Spacer(),
              ElevatedButton.icon(
                onPressed: () {
                  setState(() {
                    _networkData = _fetchNetworkData();
                  });
                },
                icon: const Icon(Icons.sync),
                label: const Text("Load Latest Analysis"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00FFCC).withOpacity(0.2),
                  foregroundColor: const Color(0xFF00FFCC),
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                ),
              ),
            ],
          ),
          const SizedBox(height: 32),
          Expanded(
            child: FutureBuilder<Map<String, dynamic>>(
              future: _networkData,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(
                    child: CircularProgressIndicator(color: Color(0xFF00FFCC)),
                  );
                } else if (snapshot.hasError) {
                  return Center(
                    child: Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: Colors.redAccent.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.redAccent),
                      ),
                      child: Text(
                        'Eroare de conexiune la serverul AI: \${snapshot.error}',
                        style: const TextStyle(color: Colors.redAccent, fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                    ),
                  );
                } else if (snapshot.hasData) {
                  final data = snapshot.data!;
                  return Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFF1E1E1E),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white12),
                      boxShadow: const [
                        BoxShadow(color: Colors.black26, blurRadius: 20, offset: Offset(0, 10)),
                      ],
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(16),
                      child: Padding(
                        padding: const EdgeInsets.all(40.0),
                        child: LayoutBuilder(
                          builder: (context, constraints) {
                            return CustomPaint(
                              size: Size(constraints.maxWidth, constraints.maxHeight),
                              painter: NetworkPainter(data: data),
                            );
                          },
                        ),
                      ),
                    ),
                  );
                } else {
                  return const Center(child: Text("Nu există date.", style: TextStyle(color: Colors.white)));
                }
              },
            ),
          ),
        ],
      ),
    );
  }
}

class NetworkPainter extends CustomPainter {
  final Map<String, dynamic> data;

  NetworkPainter({required this.data});

  @override
  void paint(Canvas canvas, Size size) {
    final nodes = data['nodes'] as List<dynamic>;
    final edges = data['edges'] as List<dynamic>;

    // Păstrăm un grid logic: presupunem că datele vin pentru un teren de 120 x 80
    const double gridWidth = 120.0;
    const double gridHeight = 80.0;

    // Convertim coordonatele matematice la dimensiunea actuală a canvas-ului
    Offset getCanvasPosition(double x, double y) {
      final dx = (x / gridWidth) * size.width;
      final dy = (y / gridHeight) * size.height;
      return Offset(dx, dy);
    }

    // Mapare rapidă a nodurilor
    final Map<String, dynamic> nodeMap = {
      for (var node in nodes) node['id']: node
    };

    // 1. DESENARE EDGES (Conexiunile de pase)
    for (var edge in edges) {
      final source = nodeMap[edge['source']];
      final target = nodeMap[edge['target']];
      if (source == null || target == null) continue;

      final startOffset = getCanvasPosition(source['x'], source['y']);
      final endOffset = getCanvasPosition(target['x'], target['y']);

      final weight = (edge['weight'] as num).toDouble();
      
      // Grosimea și opacitatea calculate pe baza greutății liniei (numărul de pase)
      final paintEdge = Paint()
        ..color = Colors.white.withOpacity((weight / 30).clamp(0.1, 0.6))
        ..strokeWidth = (weight / 4).clamp(1.0, 10.0)
        ..style = PaintingStyle.stroke;

      canvas.drawLine(startOffset, endOffset, paintEdge);
    }

    // 2. DESENARE NODES (Jucătorii)
    for (var node in nodes) {
      final isHub = node['is_hub'] == true;
      final centrality = (node['centrality'] as num).toDouble();
      
      final offset = getCanvasPosition(node['x'], node['y']);
      
      // Radius dinamic bazat pe importanța în rețea
      final radius = 12.0 + (centrality * 30.0); 

      // Culoare Neon Magenta pt HUB (Playmaker) și Neon Cyan pt jucători normali
      final nodeColor = isHub ? const Color(0xFFFF00FF) : const Color(0xFF00FFCC);

      // Efect vizual de Glow (Strălucire) pentru hub-ul central
      if (isHub) {
         final shadowPaint = Paint()
          ..color = nodeColor.withOpacity(0.5)
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 20);
         canvas.drawCircle(offset, radius + 10, shadowPaint);
      }

      // Corpul nodului
      final paintNode = Paint()
        ..color = nodeColor
        ..style = PaintingStyle.fill;
      canvas.drawCircle(offset, radius, paintNode);

      // Margine / Stroke
      final paintBorder = Paint()
        ..color = Colors.white
        ..strokeWidth = 3.0
        ..style = PaintingStyle.stroke;
      canvas.drawCircle(offset, radius, paintBorder);

      // 3. DESENARE TEXT (Numele)
      final textSpan = TextSpan(
        text: node['name'],
        style: TextStyle(
          color: Colors.white,
          fontSize: 14 + (centrality * 6), // Mărim fontul pt Playmaker
          fontWeight: isHub ? FontWeight.w900 : FontWeight.w600,
          shadows: const [Shadow(color: Colors.black87, blurRadius: 6, offset: Offset(0, 2))],
        ),
      );
      final textPainter = TextPainter(
        text: textSpan,
        textDirection: TextDirection.ltr,
        textAlign: TextAlign.center,
      );
      textPainter.layout();
      textPainter.paint(
        canvas,
        Offset(offset.dx - (textPainter.width / 2), offset.dy + radius + 8),
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
