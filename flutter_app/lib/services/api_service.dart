import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/match_intelligence.dart';

class ApiService {
  // Configurare standard pentru FastAPI local
  static const String baseUrl = 'http://127.0.0.1:8000';

  // =========================================================
  // STATE MANAGEMENT (Global ValueNotifier)
  // Elimină necesitatea unui boilerplate complex precum BLoC
  // și permite widget-urilor să asculte schimbările folosind 
  // ValueListenableBuilder<MatchIntelligenceData>
  // =========================================================
  static final ValueNotifier<MatchIntelligenceData> matchState = 
      ValueNotifier(MatchIntelligenceData());
  
  static final ValueNotifier<bool> isLoading = ValueNotifier(false);
  static final ValueNotifier<String?> errorMessage = ValueNotifier(null);

  /// Orchestratorul principal: Preia asincron toate modulele de intelligence
  static Future<void> fetchAllIntelligence() async {
    isLoading.value = true;
    errorMessage.value = null;

    try {
      // Optimizare de rețea: Paralelizăm apelurile pentru latență minimă pe 3G
      final responses = await Future.wait([
        _safeGet('/api/context/environment'),
        _safeGet('/api/context/psychology'),
        _safeGet('/api/tactics/pivot-optimization'),
        _safeGet('/api/xray/threat-map'),
      ]);

      WeatherContext? weather;
      PsychologyReport? psychology;
      PivotTarget? pivotTarget;
      List<VulnerabilityZone> zones = [];

      // Parsează Datele Meteorologice (Index 0)
      if (responses[0] != null) {
        weather = WeatherContext.fromJson(responses[0]!);
      }
      
      // Parsează Profilul Psihologic (Index 1)
      if (responses[1] != null) {
        psychology = PsychologyReport.fromJson(responses[1]!);
      }
      
      // Parsează Optimizarea Tactica pentru Pivot (Index 2)
      if (responses[2] != null) {
        pivotTarget = PivotTarget.fromJson(responses[2]!);
      }
      
      // Parsează Zonele X-RAY (Index 3)
      if (responses[3] != null && responses[3]!['vulnerability_zones'] != null) {
        zones = (responses[3]!['vulnerability_zones'] as List)
            .map((z) => VulnerabilityZone.fromJson(z))
            .toList();
      }

      // Propagă datele în tot arborele de widget-uri instantaneu
      matchState.value = MatchIntelligenceData(
        weather: weather,
        psychology: psychology,
        pivotTarget: pivotTarget,
        vulnerabilityZones: zones,
      );

    } catch (e) {
      errorMessage.value = "Eroare la sincronizarea datelor de Intelligence: \${e.toString()}";
      debugPrint(errorMessage.value);
    } finally {
      isLoading.value = false;
    }
  }

  /// Utilitar pentru request-uri HTTP sigure, protejând UI-ul de crash-uri
  static Future<Map<String, dynamic>?> _safeGet(String endpoint) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl$endpoint'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        debugPrint('Avertisment: API-ul a returnat codul \${response.statusCode} pentru ruta $endpoint');
        return null;
      }
    } catch (e) {
      debugPrint('Eroare rețea/conexiune către $endpoint: $e');
      return null; // Returnează null dacă endpoint-ul încă nu a fost creat în FastAPI
    }
  }
}
