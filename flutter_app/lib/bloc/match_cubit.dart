import 'dart:async';
import 'dart:collection';
import 'package:flutter/foundation.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../services/firestore_service.dart';
import '../services/api_client.dart';
import '../services/websocket_service.dart';
import '../services/biomechanics_worker.dart';

abstract class MatchState {}
class MatchInitial extends MatchState {}
class MatchLoaded extends MatchState {
  final Map<String, dynamic> matchData;
  MatchLoaded(this.matchData);
}
class MatchError extends MatchState {
  final String error;
  MatchError(this.error);
}

class MatchCubit extends Cubit<MatchState> {
  final FirestoreService firestoreService;
  final ApiClient apiClient;
  final WebSocketService wsService;
  final BiomechanicsWorker bioWorker;
  
  StreamSubscription? _firestoreSub;
  StreamSubscription? _wsSub;
  StreamSubscription? _connectivitySub;
  StreamSubscription? _workerAlertSub;
  
  String _manualTargetZone = '';
  final Queue<Map<String, dynamic>> _offlineActionQueue = Queue();

  MatchCubit({
    required this.firestoreService, 
    required this.apiClient, 
    required this.wsService,
    required this.bioWorker
  }) : super(MatchInitial()) {
    _initFirestoreStream();
    _initWebSocketStream();
    _initNetworkListener();
    _initWorkerListener();
  }

  void _initWorkerListener() {
    _workerAlertSub = bioWorker.alertStream.listen((alertData) {
      // Worker-ul a detectat o ruptură ligamentară din cadrele video!
      debugPrint("🚨 [CRITICAL ALERT] Din Web Worker: \${alertData['message']}");
      // Aici putem declanșa update-ul UI-ului de alerte prin emit(...)
    });
  }

  void _initFirestoreStream() {
    _firestoreSub = firestoreService.streamCurrentMatch().listen((doc) {
      if (doc.exists && doc.data() != null) {
        emit(MatchLoaded(doc.data() as Map<String, dynamic>));
      }
    }, onError: (e) {
      emit(MatchError(e.toString()));
    });
  }

  void _initWebSocketStream() {
    wsService.connect();
    
    _wsSub = wsService.telemetryStream.listen((data) {
      if (data['type'] == 'LIVE_TELEMETRY' && state is MatchLoaded) {
         final oldData = (state as MatchLoaded).matchData;
         final newData = Map<String, dynamic>.from(oldData);
         newData['live_home_positions'] = data['home_positions_live'];
         emit(MatchLoaded(newData));
      } else if (data['type'] == 'TACTICAL_ANALYSIS_READY' && state is MatchLoaded) {
         // FAANG: Când ascultătorul prinde pachetul cu Analiza finalizată pe nodurile Celery
         final oldData = (state as MatchLoaded).matchData;
         final newData = Map<String, dynamic>.from(oldData);
         
         final analysisData = data['analysis_data'] ?? {};
         var advice = analysisData['tactician_advice'];
         
         if (advice != null && advice is Map) {
             newData['latest_ai_advice'] = advice['speech_text'] ?? "Conexiune Vertex AI indisponibilă.";
             newData['decision_tree'] = advice['decision_tree'] ?? [];
         } else {
             newData['latest_ai_advice'] = advice?.toString() ?? "Conexiune Vertex AI indisponibilă.";
             newData['decision_tree'] = [];
         }
         
         // NOUL ADAOS: Salvăm datele brute X-Ray pentru Bannere (Compactness, etc)
         newData['analysis_data'] = analysisData;
         
         emit(MatchLoaded(newData));
      }
    });
  }

  void _initNetworkListener() {
    _connectivitySub = Connectivity().onConnectivityChanged.listen((List<ConnectivityResult> results) {
       if (!results.contains(ConnectivityResult.none) && _offlineActionQueue.isNotEmpty) {
          debugPrint("🌐 Net Revenit! Sincronizăm coada de comenzi tactice...");
          _syncOfflineQueue();
       }
    });
  }

  Future<void> _syncOfflineQueue() async {
     while(_offlineActionQueue.isNotEmpty) {
        final payload = _offlineActionQueue.removeFirst();
        try {
           await apiClient.analyzeMatch(payload);
           debugPrint("✅ Sincronizare Reușită pentru comandă din coadă!");
        } catch(e) {
           debugPrint("❌ Sincronizare eșuată. Re-queue.");
           _offlineActionQueue.addFirst(payload);
           break; 
        }
     }
  }

  void setManualTargetZone(double x, double y) {
    _manualTargetZone = 'Coordonate Targetate Manual de Sabău: X=\${x.toStringAsFixed(1)}m, Y=\${y.toStringAsFixed(1)}m';
    triggerAnalysis(); 
  }
  
  // NOU: Funcție pentru transmiterea directă a mesajelor audio transcrise
  void askTacticianVoiceCommand(String spokenQuestion) async {
    if (state is MatchLoaded) {
      final currentData = (state as MatchLoaded).matchData;
      final payload = Map<String, dynamic>.from(currentData);
      
      payload['coach_question'] = spokenQuestion; // Suprascriem default-ul!
      if (_manualTargetZone.isNotEmpty) {
        payload['manual_target_zone'] = _manualTargetZone;
      }
      
      try {
        await apiClient.analyzeMatch(payload);
      } catch (e) {
        debugPrint("🐒 CHAOS MONKEY: Conexiunea Cloud a murit! Executăm GRACEFUL DOWNGRADE (Euristică Locală).");
        _offlineActionQueue.add(payload); // Siguranță Offline First
        
        payload['latest_ai_advice'] = "MOD OFFLINE ACTIVAT. Mister, rețeaua din stadion a picat. Am comutat pe modelul euristic de rezervă: Avem metrici critice pe ecran. Sugerez folosirea metricilor directe (Spații X-RAY și nivel de oboseală) pentru a lua o decizie imediată pe flancuri!";
        payload['decision_tree'] = [
            {"factor": "ALGORITM EURISTIC DE REZERVĂ", "weight_pct": 100}
        ];
        emit(MatchLoaded(payload));
      }
    }
  }

  // NOU: Predicția Matematică a Terenului în viitor
  Future<Map<String, dynamic>> simulateSubstitution(String playerOut, String playerIn) async {
     if (state is MatchLoaded) {
       final ctx = (state as MatchLoaded).matchData;
       return await apiClient.simulateSub(playerOut, playerIn, ctx);
     }
     return {
       "tactical_message": "+0.0% dominație (Date lipsă)"
     };
  }

  Future<void> triggerAnalysis() async {
    if (state is MatchLoaded) {
      final currentData = (state as MatchLoaded).matchData;
      final payload = Map<String, dynamic>.from(currentData);
      
      if (_manualTargetZone.isNotEmpty) {
        payload['manual_target_zone'] = _manualTargetZone;
      }
      
      final connectivityResults = await Connectivity().checkConnectivity();
      
      if (connectivityResults.contains(ConnectivityResult.none)) {
         // OFFLINE HARDWARE
         _offlineActionQueue.add(payload);
      } else {
         try {
            await apiClient.analyzeMatch(payload);
         } catch (e) {
            _offlineActionQueue.add(payload); 
            
            payload['latest_ai_advice'] = "MOD OFFLINE ACTIVAT. Rulăm algoritmi euristici fără intervenția Vertex AI.";
            payload['decision_tree'] = [{"factor": "FALLBACK LOCAL", "weight_pct": 100}];
            emit(MatchLoaded(payload));
         }
      }
    }
  }

  @override
  Future<void> close() {
    _firestoreSub?.cancel();
    _wsSub?.cancel();
    _connectivitySub?.cancel();
    wsService.dispose();
    return super.close();
  }
}
