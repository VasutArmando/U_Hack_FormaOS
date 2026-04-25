import 'package:flutter/material.dart';
import '../main.dart';
import '../models/match_data.dart';
import '../repositories/api_data_repository.dart';
import '../repositories/data_repository.dart';
import '../services/settings_service.dart';
import '../widgets/football_pitch.dart';

class PregameScreen extends StatefulWidget {
  const PregameScreen({super.key});

  @override
  State<PregameScreen> createState() => _PregameScreenState();
}

class _PregameScreenState extends State<PregameScreen> {
  final _settingsService = getIt<SettingsService>();
  String _weaknessFilter = 'All';
  String? _opponentId;
  String? _opponentName;
  String? _stadiumId;
  String? _gameDate;
  bool _isSettingsLoading = true;

  @override
  void initState() {
    super.initState();
    _loadMatchSettings();
  }

  Future<void> _loadMatchSettings() async {
    final settings = await _settingsService.loadSettings();
    final repository = getIt<DataRepository>();
    
    String? opponentName;
    if (settings['nextOpponentId'] != null) {
       try {
         final teams = await repository.getTeams();
         final team = teams.firstWhere((t) => t.id == settings['nextOpponentId'], orElse: () => Team(id: '', name: 'Unknown Opponent'));
         opponentName = team.name;
       } catch (e) {
         opponentName = 'Unknown Opponent';
       }
    }

    // Combine game date + match time into an ISO string for the weather forecast
    String? gameDate;
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
        final matchDt = DateTime(dt.year, dt.month, dt.day, hour, minute);
        gameDate = matchDt.toIso8601String();
      } catch (_) {}
    }

    setState(() {
      _opponentId = settings['nextOpponentId'];
      _opponentName = opponentName;
      _stadiumId = settings['stadiumId'];
      _gameDate = gameDate;
      _isSettingsLoading = false;
    });
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
              labelStyle:
                  TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.2),
              tabs: [
                Tab(icon: Icon(Icons.analytics), text: 'CHRONIC GAPS'),
                Tab(icon: Icon(Icons.psychology), text: 'OPPONENT WEAKNESS'),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              children: [
                _buildChronicGapsTab(),
                _buildOpponentWeaknessTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildChronicGapsTab() {
    if (_isSettingsLoading) {
      return const Center(
          child: CircularProgressIndicator(color: Color(0xFF00FFCC)));
    }
    if (_opponentId == null) {
      return const Center(
        child: Text('Please select an opponent in the Settings screen.', 
            style: TextStyle(color: Colors.white, fontSize: 16)),
      );
    }
    final repository = getIt<DataRepository>();
    return FutureBuilder<List<TacticalGap>>(
      future: repository.getPregameGaps(opponentId: _opponentId),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const CircularProgressIndicator(color: Color(0xFF00FFCC)),
                const SizedBox(height: 16),
                Text('Analiză tactică Date - meciuri...',
                    style: TextStyle(color: Colors.white.withOpacity(0.7))),
              ],
            ),
          );
        } else if (snapshot.hasError) {
          return Center(
              child: Text('Error: ${snapshot.error}',
                  style: const TextStyle(color: Colors.red)));
        }

        final gaps = snapshot.data ?? [];
        return SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('PREDICTED TACTICAL GAPS: ${_opponentName ?? ""}'.toUpperCase(),
                  style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.white)),
              const SizedBox(height: 24),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    flex: 3,
                    child: _buildPitchVisualization(gaps),
                  ),
                  const SizedBox(width: 24),
                  Expanded(
                    flex: 2,
                    child: _buildGapsList(gaps),
                  ),
                ],
              )
            ],
          ),
        );
      },
    );
  }

  Widget _buildPitchVisualization(List<TacticalGap> gaps) {
    return SizedBox(
      height: 400,
      child: FootballPitch(gaps: gaps),
    );
  }

  Widget _buildGapsList(List<TacticalGap> gaps) {
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: gaps.length,
      itemBuilder: (context, index) {
        final gap = gaps[index];
        return Card(
          color: const Color(0xFF1E1E1E),
          margin: const EdgeInsets.only(bottom: 12),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(gap.location,
                        style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                            color: Colors.white)),
                    Chip(
                      label: Text(gap.severity,
                          style: const TextStyle(
                              fontSize: 10, color: Colors.white)),
                      backgroundColor: gap.severity == 'Critical'
                          ? Colors.red
                          : Colors.orange,
                    )
                  ],
                ),
                const SizedBox(height: 8),
                Text(gap.description,
                    style: const TextStyle(color: Colors.white70)),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildOpponentWeaknessTab() {
    if (_isSettingsLoading) {
      return const Center(
          child: CircularProgressIndicator(color: Color(0xFF00FFCC)));
    }
    if (_opponentId == null) {
      return const Center(
        child: Text('Please select an opponent in the Settings screen.', 
            style: TextStyle(color: Colors.white, fontSize: 16)),
      );
    }
    final repository = getIt<DataRepository>();
    final apiRepo = getIt<DataRepository>() as ApiDataRepository?;

    return FutureBuilder<List<PlayerWeakness>>(
      future: repository.getPregameOpponentWeakness(
          opponentId: _opponentId, stadiumId: _stadiumId, gameDate: _gameDate),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const CircularProgressIndicator(color: Color(0xFF00FFCC)),
                const SizedBox(height: 16),
                Text('Omniscient AI: Analizăm tot lotul adversarului...',
                    style: TextStyle(color: Colors.white.withOpacity(0.7))),
                const SizedBox(height: 8),
                Text('(Prima încărcare poate dura 1-2 minute)',
                    style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 12)),
              ],
            ),
          );
        } else if (snapshot.hasError) {
          return Center(
              child: Text('Error: ${snapshot.error}',
                  style: const TextStyle(color: Colors.red)));
        }

        final allPlayers = snapshot.data ?? [];
        // Apply filter
        final players = _weaknessFilter == 'Climate Risk'
            ? allPlayers.where((p) => p.climateDanger == 'High' || p.climateDanger == 'Medium').toList()
            : allPlayers;

        return Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('OPPONENT WEAKNESS: ${_opponentName ?? ""}'.toUpperCase(),
                  style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.white)),
              const SizedBox(height: 12),

              // --- Weather Banner ---
              if (_stadiumId != null && apiRepo != null)
                FutureBuilder<MatchWeather?>(
                  future: apiRepo.getMatchWeather(stadiumId: _stadiumId!, gameDate: _gameDate),
                  builder: (ctx, wSnap) {
                    if (!wSnap.hasData) return const SizedBox.shrink();
                    final w = wSnap.data!;
                    final isRain = w.condition.toLowerCase().contains('rain');
                    final isSnow = w.condition.toLowerCase().contains('snow');
                    final bannerColor = isSnow
                        ? const Color(0xFF1565C0)
                        : isRain
                            ? const Color(0xFF1A237E)
                            : const Color(0xFF1B5E20);
                    return Container(
                      margin: const EdgeInsets.only(bottom: 16),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: BoxDecoration(
                        color: bannerColor.withOpacity(0.85),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.white12),
                      ),
                      child: Row(
                        children: [
                          Text(w.conditionIcon, style: const TextStyle(fontSize: 28)),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '${w.temperature.toStringAsFixed(1)}°C — ${w.condition}  💨 ${w.windSpeed.toStringAsFixed(0)} m/s  💧 ${w.humidity}%',
                                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                                ),
                                if (w.forecastNote.isNotEmpty)
                                  Text(w.forecastNote,
                                      style: const TextStyle(color: Colors.white60, fontSize: 11)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),

              // --- Filter chips ---
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildFilterChip('All'),
                    const SizedBox(width: 8),
                    _buildFilterChip('Physical State'),
                    const SizedBox(width: 8),
                    _buildFilterChip('Psychological State'),
                    const SizedBox(width: 8),
                    _buildFilterChip('Tactical Tendencies'),
                    const SizedBox(width: 8),
                    _buildFilterChip('Climate Risk', icon: Icons.thermostat, badgeCount:
                        allPlayers.where((p) => p.climateDanger == 'High' || p.climateDanger == 'Medium').length),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Player count
              Text('${players.length} jucători${_weaknessFilter == "Climate Risk" ? " cu risc climatic" : ""}',
                  style: const TextStyle(color: Colors.white38, fontSize: 12)),
              const SizedBox(height: 8),

              Expanded(
                child: ListView.builder(
                  itemCount: players.length,
                  itemBuilder: (context, index) {
                    final player = players[index];
                    final isDangerous = player.climateDanger == 'High';
                    final isMedium = player.climateDanger == 'Medium';
                    final borderColor = isDangerous
                        ? Colors.orangeAccent.withOpacity(0.7)
                        : isMedium
                            ? Colors.yellow.withOpacity(0.4)
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
                                          style: const TextStyle(
                                              fontWeight: FontWeight.bold,
                                              fontSize: 18,
                                              color: Colors.white)),
                                      if (player.birthCountry.isNotEmpty && player.birthCountry != 'Unknown' && player.birthCountry != 'Romania')
                                        Padding(
                                          padding: const EdgeInsets.only(left: 8),
                                          child: Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                            decoration: BoxDecoration(
                                              color: Colors.white10,
                                              borderRadius: BorderRadius.circular(4),
                                            ),
                                            child: Text('🌍 ${player.birthCountry}',
                                                style: const TextStyle(fontSize: 10, color: Colors.white60)),
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Text('Score: ${player.overallWeaknessScore.toStringAsFixed(0)}',
                                        style: const TextStyle(
                                            color: Color(0xFF00FFCC),
                                            fontWeight: FontWeight.bold)),
                                    if (isDangerous)
                                      const Text('🌡️ RISC CLIMATIC RIDICAT',
                                          style: TextStyle(color: Colors.orangeAccent, fontSize: 10)),
                                    if (isMedium)
                                      const Text('🌡️ Risc climatic mediu',
                                          style: TextStyle(color: Colors.yellowAccent, fontSize: 10)),
                                  ],
                                ),
                              ],
                            ),
                            const Divider(color: Colors.white10, height: 24),
                            if (_weaknessFilter == 'All' ||
                                _weaknessFilter == 'Physical State')
                              Padding(
                                padding: const EdgeInsets.only(bottom: 8.0),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Icon(Icons.fitness_center,
                                        size: 18, color: Colors.orangeAccent),
                                    const SizedBox(width: 8),
                                    Expanded(
                                        child: Text(
                                            'Physical: ${player.physicalState}',
                                            style: const TextStyle(
                                                color: Colors.white70))),
                                  ],
                                ),
                              ),
                            if (_weaknessFilter == 'All' ||
                                _weaknessFilter == 'Psychological State')
                              Padding(
                                padding: const EdgeInsets.only(bottom: 8.0),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Icon(Icons.psychology,
                                        size: 18, color: Colors.blueAccent),
                                    const SizedBox(width: 8),
                                    Expanded(
                                        child: Text(
                                            'Psychological: ${player.psychologicalState}',
                                            style: const TextStyle(
                                                color: Colors.white70))),
                                  ],
                                ),
                              ),
                            if (_weaknessFilter == 'All' ||
                                _weaknessFilter == 'Tactical Tendencies')
                              if (player.tacticalTendencies.isNotEmpty)
                                Padding(
                                  padding: const EdgeInsets.only(bottom: 8.0),
                                  child: Row(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Icon(Icons.lightbulb_outline,
                                          size: 18, color: Colors.yellowAccent),
                                      const SizedBox(width: 8),
                                      Expanded(
                                          child: Text(
                                              'Tactics: ${player.tacticalTendencies}',
                                              style: const TextStyle(
                                                  color: Colors.white70))),
                                    ],
                                  ),
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
      },
    );
  }

  Widget _buildFilterChip(String label, {IconData? icon, int badgeCount = 0}) {
    final isSelected = _weaknessFilter == label;
    return Stack(
      clipBehavior: Clip.none,
      children: [
        ChoiceChip(
          avatar: icon != null ? Icon(icon, size: 14, color: isSelected ? const Color(0xFF00FFCC) : Colors.white54) : null,
          label: Text(label),
          selected: isSelected,
          onSelected: (bool selected) {
            setState(() {
              if (selected) _weaknessFilter = label;
            });
          },
          selectedColor: const Color(0xFF00FFCC).withOpacity(0.2),
          backgroundColor: Colors.white10,
          side: isSelected
              ? const BorderSide(color: Color(0xFF00FFCC), width: 1)
              : BorderSide.none,
          labelStyle: TextStyle(
              color: isSelected ? const Color(0xFF00FFCC) : Colors.white),
        ),
        if (badgeCount > 0)
          Positioned(
            top: -4,
            right: -4,
            child: Container(
              padding: const EdgeInsets.all(4),
              decoration: const BoxDecoration(
                color: Colors.orangeAccent,
                shape: BoxShape.circle,
              ),
              child: Text('$badgeCount',
                  style: const TextStyle(fontSize: 9, color: Colors.black, fontWeight: FontWeight.bold)),
            ),
          ),
      ],
    );
  }
}
