import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketService {
  WebSocketChannel? _channel;
  final _streamController = StreamController<Map<String, dynamic>>.broadcast();
  
  bool _isConnecting = false;
  int _reconnectAttempts = 0;
  Timer? _reconnectTimer;
  
  // Stream-ul expus către BLoC
  Stream<Map<String, dynamic>> get telemetryStream => _streamController.stream;

  void connect() {
    if (_isConnecting) return;
    _isConnecting = true;
    
    try {
      final wsUrl = Uri.parse('ws://127.0.0.1:8080/ws/telemetry');
      
      _channel = WebSocketChannel.connect(wsUrl);
      debugPrint("📡 WebSocket: Conectare TCP deschisă la \$wsUrl");
      
      _channel!.stream.listen(
        (message) {
          _isConnecting = false;
          _reconnectAttempts = 0; // Conexiune stabilă
          
          final decoded = jsonDecode(message);
          _streamController.add(decoded);
        },
        onDone: () {
          debugPrint("⚠️ WebSocket: Conexiunea a fost închisă de server.");
          _triggerReconnect();
        },
        onError: (error) {
          debugPrint("🚨 WebSocket: Eroare de rețea stadion. (\$error)");
          _triggerReconnect();
        },
      );
    } catch (e) {
      _triggerReconnect();
    }
  }

  void _triggerReconnect() {
    _isConnecting = false;
    _channel?.sink.close();
    
    // FAANG Standard: Exponential Backoff (1s, 2s, 4s, 8s, 16s, 30s)
    // Previne spamarea serverului când cade rețeaua.
    final delay = min(pow(2, _reconnectAttempts).toInt(), 30);
    _reconnectAttempts++;
    
    debugPrint("🔄 WebSocket: Exponential Backoff - Reîncercăm în \$delay secunde...");
    
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(Duration(seconds: delay), () {
      connect();
    });
  }

  void dispose() {
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _streamController.close();
  }
}
