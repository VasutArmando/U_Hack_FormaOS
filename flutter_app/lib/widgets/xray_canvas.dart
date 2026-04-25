import 'package:flutter/material.dart';
import 'dart:ui' as ui;

class XRayCanvas extends StatefulWidget {
  final List<List<double>> homePositions;
  final List<List<double>> awayPositions;
  final List<List<double>>? xtHeatmap;
  final Function(double x, double y)? onZoneMarked;

  const XRayCanvas({
    super.key,
    required this.homePositions,
    required this.awayPositions,
    this.xtHeatmap,
    this.onZoneMarked,
  });

  @override
  State<XRayCanvas> createState() => _XRayCanvasState();
}

class _XRayCanvasState extends State<XRayCanvas> {
  Offset? _markedZone;
  ui.FragmentShader? _voronoiShader;

  @override
  void initState() {
    super.initState();
    _loadShader();
  }

  Future<void> _loadShader() async {
    try {
      final program = await ui.FragmentProgram.fromAsset('shaders/voronoi.frag');
      setState(() {
        _voronoiShader = program.fragmentShader();
      });
    } catch (e) {
      debugPrint("Eroare la încărcarea shaderului GLSL GPU: \$e");
    }
  }

  void _handleTap(TapUpDetails details, Size size) {
    final double scaleX = 105.0 / size.width;
    final double scaleY = 68.0 / size.height;
    
    final x = details.localPosition.dx * scaleX;
    final y = details.localPosition.dy * scaleY;
    
    setState(() => _markedZone = Offset(x, y));
    if (widget.onZoneMarked != null) widget.onZoneMarked!(x, y);
  }

  @override
  Widget build(BuildContext context) {
    if (_voronoiShader == null) {
      // Afișăm un spinner premium în timp ce se compilează Shader-ul GPU
      return const Center(child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2));
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        final size = Size(constraints.maxWidth, constraints.maxWidth / (105 / 68));
        return GestureDetector(
          onTapUp: (details) => _handleTap(details, size),
          child: AspectRatio(
            aspectRatio: 105 / 68,
            child: CustomPaint(
              painter: PitchPainter(
                homePositions: widget.homePositions,
                awayPositions: widget.awayPositions,
                xtHeatmap: widget.xtHeatmap,
                markedZone: _markedZone,
                voronoiShader: _voronoiShader!,
              ),
            ),
          ),
        );
      }
    );
  }
}

class PitchPainter extends CustomPainter {
  final List<List<double>> homePositions;
  final List<List<double>> awayPositions;
  final List<List<double>>? xtHeatmap;
  final Offset? markedZone;
  final ui.FragmentShader voronoiShader;

  PitchPainter({
    required this.homePositions,
    required this.awayPositions,
    this.xtHeatmap,
    this.markedZone,
    required this.voronoiShader,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final double scaleX = size.width / 105.0;
    final double scaleY = size.height / 68.0;

    _drawPitch(canvas, size, scaleX);
    _drawWatermark(canvas, size);

    // 1. HARDWARE ACCELERATION: Randăm Voronoi direct prin GPU Fragment Shader (Zero CPU Load)
    _drawVoronoiGPU(canvas, size);

    // 2. Efect Cinematografic: Heatmap-ul xT procesat cu Gaussian Blur Nativ
    if (xtHeatmap != null) _drawHeatmapFluid(canvas, size, xtHeatmap!);

    // 3. Randarea Obiectelor Solide
    _drawPlayers(canvas, scaleX, scaleY);
    if (markedZone != null) _drawMarkedZone(canvas, scaleX, scaleY, markedZone!);
  }

  void _drawVoronoiGPU(Canvas canvas, Size size) {
    voronoiShader.setFloat(0, size.width);
    voronoiShader.setFloat(1, size.height);
    
    int index = 2;
    // Pompăm coordonatele Home în Uniform-ul din GLSL
    for (int i = 0; i < 11; i++) {
      if (i < homePositions.length && homePositions[i].length >= 2) {
        voronoiShader.setFloat(index++, homePositions[i][0] / 105.0);
        voronoiShader.setFloat(index++, homePositions[i][1] / 68.0);
      } else {
        voronoiShader.setFloat(index++, -1.0);
        voronoiShader.setFloat(index++, -1.0);
      }
    }
    
    // Pompăm coordonatele Away
    for (int i = 0; i < 11; i++) {
      if (i < awayPositions.length && awayPositions[i].length >= 2) {
        voronoiShader.setFloat(index++, awayPositions[i][0] / 105.0);
        voronoiShader.setFloat(index++, awayPositions[i][1] / 68.0);
      } else {
        voronoiShader.setFloat(index++, -1.0);
        voronoiShader.setFloat(index++, -1.0);
      }
    }

    final paint = Paint()..shader = voronoiShader;
    // Un singur call către GPU desenează toate zonele
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), paint);
  }

  void _drawHeatmapFluid(Canvas canvas, Size size, List<List<double>> heatmap) {
    int rows = heatmap.length;
    if (rows == 0) return;
    int cols = heatmap[0].length;
    final cellWidth = size.width / cols;
    final cellHeight = size.height / rows;

    // Suprapunem un ImageFilter global pentru a topi punctele într-o imagine fluidă (Gaussian Blur 30px)
    final fluidPaint = Paint()
      ..imageFilter = ui.ImageFilter.blur(sigmaX: 30.0, sigmaY: 30.0)
      ..style = PaintingStyle.fill;
      
    canvas.saveLayer(Rect.fromLTWH(0, 0, size.width, size.height), fluidPaint);

    for (int y = 0; y < rows; y++) {
      for (int x = 0; x < cols; x++) {
        double val = heatmap[y][x]; 
        if (val <= 0.05) continue; 

        // MaskFilter la nivel de nod
        final nodePaint = Paint()
          ..color = HSVColor.fromAHSV(val * 0.9, (1.0 - val) * 120, 1.0, 1.0).toColor()
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 20.0);
          
        final center = Offset(x * cellWidth + cellWidth / 2, y * cellHeight + cellHeight / 2);
        canvas.drawCircle(center, cellWidth * 1.8, nodePaint);
      }
    }
    canvas.restore();
  }

  void _drawPitch(Canvas canvas, Size size, double scaleX) {
    final paint = Paint()..color = const Color(0xFF1B1B1B)..style = PaintingStyle.fill;
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), paint);
    
    final linePaint = Paint()..color = Colors.white.withValues(alpha: 0.5)..strokeWidth = 2.0..style = PaintingStyle.stroke;
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), linePaint);
    canvas.drawLine(Offset(size.width / 2, 0), Offset(size.width / 2, size.height), linePaint);
    canvas.drawCircle(Offset(size.width / 2, size.height / 2), 9.15 * scaleX, linePaint);
  }

  void _drawWatermark(Canvas canvas, Size size) {
    final textPainter = TextPainter(
      text: TextSpan(text: 'U', style: TextStyle(color: Colors.white.withValues(alpha: 0.03), fontSize: size.height * 0.7, fontWeight: FontWeight.w900, fontFamily: 'serif')),
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(canvas, Offset((size.width - textPainter.width) / 2, (size.height - textPainter.height) / 2));
  }

  void _drawPlayers(Canvas canvas, double scaleX, double scaleY) {
    final homePaint = Paint()..color = Colors.white..style = PaintingStyle.fill;
    final awayPaint = Paint()..color = const Color(0xFF8B0000)..style = PaintingStyle.fill;

    for (var p in homePositions) {
      if (p.length >= 2) canvas.drawCircle(Offset(p[0] * scaleX, p[1] * scaleY), 5.5, homePaint);
    }
    for (var p in awayPositions) {
      if (p.length >= 2) canvas.drawCircle(Offset(p[0] * scaleX, p[1] * scaleY), 5.5, awayPaint);
    }
  }

  void _drawMarkedZone(Canvas canvas, double scaleX, double scaleY, Offset zone) {
    final paint = Paint()..color = const Color(0xFFD4AF37)..style = PaintingStyle.stroke..strokeWidth = 3.0;
    final fillPaint = Paint()..color = const Color(0xFFD4AF37).withValues(alpha: 0.2)..style = PaintingStyle.fill;
    final center = Offset(zone.dx / scaleX, zone.dy / scaleY);
    
    canvas.drawCircle(center, 12.0 / scaleX, fillPaint);
    canvas.drawCircle(center, 12.0 / scaleX, paint);
    canvas.drawLine(Offset(center.dx - 10, center.dy), Offset(center.dx + 10, center.dy), paint);
    canvas.drawLine(Offset(center.dx, center.dy - 10), Offset(center.dx, center.dy + 10), paint);
  }

  @override
  bool shouldRepaint(covariant PitchPainter oldDelegate) => true;
}
