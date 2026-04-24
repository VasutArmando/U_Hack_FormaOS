import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../bloc/match_cubit.dart';
import '../widgets/scouting_report_dashboard.dart';
import '../widgets/opponent_intelligence_card.dart';
import '../widgets/alert_banner.dart';
import '../widgets/xray_canvas.dart';
import '../widgets/shield_dashboard.dart';
import '../widgets/tactician_dashboard.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 1;
  
  List<ConnectivityResult> _connectionStatus = [ConnectivityResult.wifi];
  late StreamSubscription<List<ConnectivityResult>> _connectivitySubscription;

  @override
  void initState() {
    super.initState();
    _initConnectivity();
  }
  
  Future<void> _initConnectivity() async {
    try {
      final result = await Connectivity().checkConnectivity();
      setState(() => _connectionStatus = result);
    } catch (e) {
      debugPrint('Network Check Error: \$e');
    }
    
    _connectivitySubscription = Connectivity().onConnectivityChanged.listen((List<ConnectivityResult> result) {
      setState(() => _connectionStatus = result);
    });
  }

  @override
  void dispose() {
    _connectivitySubscription.cancel();
    super.dispose();
  }

  void _onZoneMarked(double x, double y) {
    context.read<MatchCubit>().setManualTargetZone(x, y);
    
    final bool isOffline = _connectionStatus.contains(ConnectivityResult.none);
    final String message = isOffline 
        ? '⚠️ Zonă marcată (Offline). Se va trimite la AI când revine semnalul.' 
        : 'Zonă tactică marcată! TACTICIAN recalculează...';
        
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.black)),
        backgroundColor: isOffline ? Colors.amberAccent : Colors.white,
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 4),
      )
    );
  }

  @override
  Widget build(BuildContext context) {
    final bool isOffline = _connectionStatus.contains(ConnectivityResult.none);

    final xRayTab = Padding(
      padding: const EdgeInsets.all(16.0),
      child: Center(
        child: BlocBuilder<MatchCubit, MatchState>(
          builder: (context, state) {
            List<List<double>> hPositions = const [[20.0, 30.0], [25.5, 45.1], [40.2, 50.0], [35.0, 20.0]];
            
            if (state is MatchLoaded && state.matchData.containsKey('live_home_positions')) {
               final rawPos = state.matchData['live_home_positions'] as List;
               hPositions = rawPos.map((e) => List<double>.from(e.map((x) => (x as num).toDouble()))).toList();
            }

            return XRayCanvas(
              homePositions: hPositions,
              awayPositions: const [[55.0, 34.0], [60.0, 50.0], [65.0, 20.0], [80.0, 34.0]],
              onZoneMarked: _onZoneMarked,
            );
          }
        ),
      ),
    );

    final List<Widget> tabs = [
      const Center(child: Text('ORACLE - Tactical Layout', style: TextStyle(color: Colors.white))),
      xRayTab,
      const ShieldDashboard(),
      const TacticianDashboard(), // Substituția Voice-First integrată
      const ScoutingReportDashboard(),
      const OpponentIntelligenceCard(), // Tab 6: Gemini 2.0
    ];

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const CircleAvatar(
              backgroundColor: Colors.white,
              radius: 16,
              child: Text('U', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 20)),
            ),
            const SizedBox(width: 12),
            const Text('FORMA OS', style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1.5)),
            const SizedBox(width: 12),
            // NOU: Sensor Fusion Status Badge (Puls vizual de nivel Hardware)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.greenAccent.withOpacity(0.15),
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: Colors.greenAccent, width: 1.5)
              ),
              child: const Row(
                children: [
                  Icon(Icons.satellite_alt, color: Colors.greenAccent, size: 14),
                  SizedBox(width: 6),
                  Text("EKF NTP SYNC", style: TextStyle(color: Colors.greenAccent, fontSize: 10, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
            if (isOffline) ...[
              const SizedBox(width: 12),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.redAccent.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: Colors.redAccent)
                ),
                child: const Row(
                  children: [
                    Icon(Icons.wifi_off, color: Colors.redAccent, size: 14),
                    SizedBox(width: 6),
                    Text("OFFLINE (CACHE)", style: TextStyle(color: Colors.redAccent, fontSize: 10, fontWeight: FontWeight.bold)),
                  ],
                ),
              )
            ]
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(isOffline ? Icons.cloud_off : Icons.sync),
            tooltip: 'Recalculare Tactică',
            onPressed: isOffline ? null : () => context.read<MatchCubit>().triggerAnalysis(),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => Navigator.pushReplacementNamed(context, '/login'),
          )
        ],
      ),
      body: Stack(
        children: [
          tabs[_currentIndex],
          const Align(
            alignment: Alignment.topCenter,
            child: AlertBanner(), 
          ),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        selectedItemColor: Colors.white,
        unselectedItemColor: Colors.white38,
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.remove_red_eye), label: 'ORACLE'),
          BottomNavigationBarItem(icon: Icon(Icons.radar), label: 'X-RAY'),
          BottomNavigationBarItem(icon: Icon(Icons.health_and_safety), label: 'SHIELD'),
          BottomNavigationBarItem(icon: Icon(Icons.smart_toy), label: 'TACTICIAN'),
          BottomNavigationBarItem(icon: Icon(Icons.picture_as_pdf), label: 'SCOUTING'),
          BottomNavigationBarItem(icon: Icon(Icons.psychology), label: 'INTEL'),
        ],
      ),
    );
  }
}
