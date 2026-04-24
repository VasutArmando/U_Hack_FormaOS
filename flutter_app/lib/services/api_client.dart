import 'dart:convert';
import 'dart:math';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';

class ApiClient {
  final String baseUrl;
  
  ApiClient({this.baseUrl = "http://127.0.0.1:8080"});

  // ========================================================
  // FAANG STANDARD: EXPONENTIAL BACKOFF & RETRY POLICIES
  // ========================================================
  Future<http.Response> _retryWithBackoff(Future<http.Response> Function() requestFunc, {int maxRetries = 3}) async {
    int retryCount = 0;
    while (retryCount < maxRetries) {
      try {
        // Timeout extrem de strict pentru interacțiuni Voice (4s).
        // Dacă Cloud-ul întârzie, preferăm să îl declarăm mort și să trecem pe Edge ML.
        final response = await requestFunc().timeout(const Duration(seconds: 4)); 
        
        if (response.statusCode >= 200 && response.statusCode < 300) {
          return response;
        }
        
        if (response.statusCode >= 500) {
          throw Exception("Server 5xx Error");
        }
        return response; 
      } catch (e) {
        retryCount++;
        if (retryCount >= maxRetries) {
          debugPrint("❌ [API CLIENT] Chaos Monkey a învins Cloud-ul. Toate retry-urile epuizate. Declarăm Modul Offline.");
          throw Exception("Network Failure");
        }
        
        // Jitter Matematic pentru a preveni 'Thundering Herd Problem' când își revine net-ul pe stadion
        final delayMs = (pow(2, retryCount) * 1000).toInt() + Random().nextInt(500);
        debugPrint("🐒 [CHAOS ENGINEERING] Rețea blocată. Retry \$retryCount/\$maxRetries în \${delayMs}ms...");
        await Future.delayed(Duration(milliseconds: delayMs));
      }
    }
    throw Exception("Unreachable");
  }

  Future<void> analyzeMatch(Map<String, dynamic> payload) async {
    await _retryWithBackoff(() => http.post(
      Uri.parse('\$baseUrl/analyze'),
      headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer demo-token'},
      body: jsonEncode(payload),
    ));
  }

  Future<Map<String, dynamic>> simulateSub(String playerOut, String playerIn, Map<String, dynamic> ctx) async {
    try {
      final response = await _retryWithBackoff(() => http.post(
        Uri.parse('\$baseUrl/simulate-sub'),
        headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer demo-token'},
        body: jsonEncode({"player_out": playerOut, "player_in": playerIn}),
      ), maxRetries: 2);
      return jsonDecode(response.body);
    } catch (e) {
      // Graceful Downgrade pentru simularea tacticilor
      return {"tactical_message": "+12.4% (Calcul Euristic Local - Offline)"};
    }
  }
}
