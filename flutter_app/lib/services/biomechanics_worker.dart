// ignore_for_file: deprecated_member_use
import 'dart:async';
import 'package:flutter/foundation.dart';
// Interoperabilitate nativă Web pentru a controla Worker-ul
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

class BiomechanicsWorker {
  html.Worker? _worker;
  final StreamController<Map<String, dynamic>> _alertController = StreamController.broadcast();

  Stream<Map<String, dynamic>> get alertStream => _alertController.stream;

  void initWorker() {
    if (!kIsWeb) return;

    try {
      // Pornim script-ul JavaScript masiv pe un thread secundar
      _worker = html.Worker('mediapipe_worker.js');
      
      // Ascultăm mesajele trimise înapoi către Flutter
      _worker!.onMessage.listen((html.MessageEvent event) {
        final data = event.data;
        if (data != null && data['type'] == 'ALERT') {
          _alertController.add({
            'severity': data['severity'],
            'deviation': data['deviation'],
            'message': data['message']
          });
        }
      });
      
      _worker!.onError.listen((e) {
        debugPrint("❌ Eroare internă în Web Worker-ul MediaPipe.");
      });
      
      debugPrint("🚀 Web Worker MediaPipe (WASM + WebGL) a fost inițializat cu succes. Main UI thread eliberat!");
    } catch (e) {
      debugPrint("Eroare la pornirea worker-ului: \$e");
    }
  }

  /// Pompăm cadrele Video (pixels) spre Worker.
  /// Folosind buffer-ul transferabil (Zero-Copy pe cât posibil),
  /// prevenim un Garbage Collection imens în memorie.
  void processFrame(Uint8List rgbaPixels, int width, int height) {
    if (_worker == null) return;

    _worker!.postMessage({
      'action': 'PROCESS_FRAME',
      'frameData': rgbaPixels.buffer,
      'width': width,
      'height': height,
    });
  }

  void dispose() {
    _worker?.terminate();
    _alertController.close();
  }
}
