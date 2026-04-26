import 'package:flutter/material.dart';
import 'dart:async';
import '../main.dart';
import '../models/match_data.dart';
import '../repositories/data_repository.dart';
import '../services/settings_service.dart';
import '../widgets/assistant_tab.dart';
import '../widgets/football_pitch.dart';

class InGameScreen extends StatefulWidget {
  const InGameScreen({super.key});

  @override
  State<InGameScreen> createState() => _InGameScreenState();
}

class _InGameScreenState extends State<InGameScreen> {
  final _settingsService = getIt<SettingsService>();
  DateTime? _matchStartTime;
  int _currentMinute = 0;
  Timer? _timer;
  List<LivePlayerFatigue> _players = [];
  bool _isLoadingPlayers = true;

  @override
  void initState() {
    super.initState();
    _loadMatchSettings();
    _startMinuteTimer();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _loadMatchSettings() async {
    final settings = await _settingsService.loadSettings();
    if (settings['gameDate'] != null) {
      try {
        final dt = DateTime.parse(settings['gameDate']!);
        int hour = 20, minute = 45;
        if (settings['matchTime'] != null) {
          final parts = settings['matchTime']!.split(':');
          if (parts.length == 2) {
            hour = int.tryParse(parts[0]) ?? 20;
            minute = int.tryParse(parts[1]) ?? 45;
          }
        }
        setState(() {
          _matchStartTime = DateTime(dt.year, dt.month, dt.day, hour, minute);
          _updateMatchMinute();
        });
      } catch (_) {}
    }
    
    // Load players once
    try {
      final repository = getIt<DataRepository>();
      final players = await repository.getIngamePlayers();
      setState(() {
        _players = players;
        _isLoadingPlayers = false;
      });
    } catch (e) {
      setState(() => _isLoadingPlayers = false);
    }
  }

  void _startMinuteTimer() {
    _timer = Timer.periodic(const Duration(seconds: 10), (timer) {
      if (mounted) {
        setState(() {
          _updateMatchMinute();
        });
      }
    });
  }

  void _updateMatchMinute() {
    if (_matchStartTime == null) return;
    final now = DateTime.now();
    if (now.isBefore(_matchStartTime!)) {
      _currentMinute = 0;
    } else {
      _currentMinute = now.difference(_matchStartTime!).inMinutes;
      if (_currentMinute > 95) _currentMinute = 95; // Clamp for demo
    }
  }

  double _calculatePlayerFatigue(LivePlayerFatigue player, int minute) {
    if (!player.isStartingXI) return 0.0;
    if (minute <= 0) return 0.0;
    
    // Parse position from name if not provided in model (e.g. "Name (CM)")
    String pos = player.position;
    if (pos == 'Unknown') {
      final match = RegExp(r'\((.*?)\)').firstMatch(player.name);
      if (match != null) {
        pos = match.group(1) ?? 'Unknown';
      }
    }

    double positionFactor = 1.0;
    pos = pos.toUpperCase();
    if (pos.contains('GK')) positionFactor = 0.15;
    else if (pos.contains('CB')) positionFactor = 0.75;
    else if (pos.contains('LB') || pos.contains('RB') || pos.contains('WB')) positionFactor = 1.15;
    else if (pos.contains('CM') || pos.contains('DM') || pos.contains('AM')) positionFactor = 1.35;
    else if (pos.contains('LW') || pos.contains('RW') || pos.contains('ST')) positionFactor = 1.05;

    double weightFactor = player.weight / 75.0;
    
    // Base fatigue: ~0.85% per minute for standard player
    double fatigue = minute * 0.85 * positionFactor * weightFactor;
    
    return fatigue.clamp(0.0, 100.0);
  }

  String _getFatigueRemark(double fatigue, String pos) {
    if (fatigue < 30) return "Fresh and highly energetic. High pressing intensity.";
    if (fatigue < 60) return "Moderate fatigue. Maintaining tactical discipline.";
    if (fatigue < 80) return "Noticeable drop in sprint volume. Vulnerable to fast transitions.";
    return "Critical exhaustion. Reaction time and positional awareness severely compromised.";
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            color: const Color(0xFF181818),
            child: const TabBar(
              indicatorColor: Color(0xFF00FFCC),
              indicatorWeight: 4.0,
              labelColor: Color(0xFF00FFCC),
              unselectedLabelColor: Colors.white54,
              labelStyle: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.2),
              tabs: [
                Tab(icon: Icon(Icons.battery_alert), text: 'OPPONENT WEAKNESS'),
                Tab(icon: Icon(Icons.mic), text: 'ASSISTANT'),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              children: [
                _buildOpponentWeaknessTab(),
                AssistantTab(
                  liveFatigue: _players.map((p) {
                    // Create a copy with updated fatigue for the AI
                    return LivePlayerFatigue(
                      id: p.id,
                      name: p.name,
                      fatigue: _calculatePlayerFatigue(p, _currentMinute),
                      liveRemark: p.liveRemark,
                      weight: p.weight,
                      position: p.position,
                      isStartingXI: p.isStartingXI,
                    );
                  }).toList(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildOpponentWeaknessTab() {
    if (_isLoadingPlayers) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF00FFCC)));
    }
    
    final players = List<LivePlayerFatigue>.from(_players);
    
    // Sort players: Starting XI first
    players.sort((a, b) {
      if (a.isStartingXI && !b.isStartingXI) return -1;
      if (!a.isStartingXI && b.isStartingXI) return 1;
      return 0;
    });

    if (players.isEmpty) {
      return const Center(
        child: Text('No players found for the selected opponent.', 
            style: TextStyle(color: Colors.white70, fontSize: 16)),
      );
    }

    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('LIVE PLAYER FATIGUE', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: const Color(0xFF00FFCC).withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: const Color(0xFF00FFCC).withValues(alpha: 0.5)),
                ),
                child: Text(
                  'MINUTE $_currentMinute\'',
                  style: const TextStyle(color: Color(0xFF00FFCC), fontWeight: FontWeight.bold, fontSize: 16),
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          Expanded(
            child: ListView.builder(
              itemCount: players.length,
              itemBuilder: (context, index) {
                final player = players[index];
                final calculatedFatigue = _calculatePlayerFatigue(player, _currentMinute);
                
                Color fatigueColor = Colors.green;
                if (calculatedFatigue > 60) {
                  fatigueColor = Colors.orange;
                }
                if (calculatedFatigue > 80) {
                  fatigueColor = Colors.red;
                }

                final isCritical = calculatedFatigue > 80;
                final isModerate = calculatedFatigue > 60 && calculatedFatigue <= 80;
                final borderColor = isCritical
                    ? Colors.redAccent.withValues(alpha: 0.7)
                    : isModerate
                        ? Colors.orangeAccent.withValues(alpha: 0.4)
                        : Colors.transparent;

                return Card(
                  color: const Color(0xFF1E1E1E),
                  margin: const EdgeInsets.only(bottom: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: BorderSide(color: borderColor, width: 1.5),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(20.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Row(
                                children: [
                                  Text(player.name,
                                      style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 18,
                                          color: player.isStartingXI ? Colors.white : Colors.white54)),
                                  if (player.isStartingXI)
                                    Padding(
                                      padding: const EdgeInsets.only(left: 8),
                                      child: Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                        decoration: BoxDecoration(
                                          color: Colors.white10,
                                          borderRadius: BorderRadius.circular(4),
                                        ),
                                        child: const Text('⭐ STARTING XI',
                                            style: TextStyle(fontSize: 10, color: Colors.amber)),
                                      ),
                                    ),
                                ],
                              ),
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                if (player.isStartingXI)
                                  Text('${calculatedFatigue.toStringAsFixed(0)}% Fatigue',
                                      style: TextStyle(
                                          color: player.isStartingXI ? fatigueColor : Colors.white24,
                                          fontWeight: FontWeight.bold))
                                else
                                  const Text('Bench / Sub',
                                      style: TextStyle(
                                          color: Colors.white24,
                                          fontWeight: FontWeight.bold)),
                                if (isCritical)
                                  const Text('⚠️ CRITICAL EXHAUSTION',
                                      style: TextStyle(color: Colors.redAccent, fontSize: 10)),
                                if (isModerate)
                                  const Text('⚠️ Moderate fatigue',
                                      style: TextStyle(color: Colors.orangeAccent, fontSize: 10)),
                              ],
                            ),
                          ],
                        ),
                        const Divider(color: Colors.white10, height: 24),
                        LinearProgressIndicator(
                          value: calculatedFatigue / 100,
                          backgroundColor: Colors.white10,
                          valueColor: AlwaysStoppedAnimation<Color>(fatigueColor),
                        ),
                        const SizedBox(height: 12),
                        Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                                const Icon(Icons.battery_alert, size: 18, color: Colors.orangeAccent),
                                const SizedBox(width: 8),
                                Expanded(
                                    child: Text(
                                        player.isStartingXI ? _getFatigueRemark(calculatedFatigue, player.position) : "Currently on the bench. Ready if substituted.",
                                        style: const TextStyle(color: Colors.white70),
                                    ),
                                ),
                            ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
