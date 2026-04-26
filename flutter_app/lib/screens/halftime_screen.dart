import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../main.dart';
import '../models/match_data.dart';
import '../repositories/data_repository.dart';

class HalftimeScreen extends StatefulWidget {
  const HalftimeScreen({super.key});

  @override
  State<HalftimeScreen> createState() => _HalftimeScreenState();
}

class _HalftimeScreenState extends State<HalftimeScreen> {
  String? _opponentId;
  String? _stadiumId;
  String? _gameDate;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _opponentId = prefs.getString('settings_next_opponent_id');
      _stadiumId = prefs.getString('settings_stadium_id');
      _gameDate = prefs.getString('settings_game_date');
    });
  }

  double _calculatePlayerFatigue(LivePlayerFatigue player, int minute) {
    if (!player.isStartingXI) return 0.0;
    
    String pos = player.position;
    double positionFactor = 1.0;
    pos = pos.toUpperCase();
    if (pos.contains('GK')) positionFactor = 0.15;
    else if (pos.contains('CB')) positionFactor = 0.75;
    else if (pos.contains('LB') || pos.contains('RB') || pos.contains('WB')) positionFactor = 1.15;
    else if (pos.contains('CM') || pos.contains('DM') || pos.contains('AM')) positionFactor = 1.35;
    else if (pos.contains('LW') || pos.contains('RW') || pos.contains('ST')) positionFactor = 1.05;

    double weightFactor = player.weight / 75.0;
    
    // Base fatigue for minute 45
    double fatigue = minute * 0.85 * positionFactor * weightFactor;
    
    // Break recovery: reduce fatigue by 15% relative
    fatigue = fatigue * 0.85;
    
    return fatigue.clamp(0.0, 100.0);
  }

  Color _getFatigueColor(double fatigue) {
    if (fatigue < 40) return const Color(0xFF00FFCC);
    if (fatigue < 70) return Colors.orange;
    return Colors.red;
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
                Tab(icon: Icon(Icons.battery_alert), text: 'OPPONENT FATIGUE'),
                Tab(icon: Icon(Icons.change_circle), text: 'POSSIBLE CHANGES'),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              children: [
                _buildHalftimeFatigueTab(),
                _buildPossibleChangesTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHalftimeFatigueTab() {
    if (_opponentId == null) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF00FFCC)));
    }
    
    final repository = getIt<DataRepository>();
    return FutureBuilder<List<LivePlayerFatigue>>(
      future: repository.getIngamePlayers(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator(color: Color(0xFF00FFCC)));
        } else if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}', style: const TextStyle(color: Colors.red)));
        }
        
        final players = snapshot.data ?? [];
        if (players.isEmpty) {
          return const Center(child: Text('No player data available.', style: TextStyle(color: Colors.white54)));
        }

        // Sort so Starting XI is at the top
        final sortedPlayers = List<LivePlayerFatigue>.from(players);
        sortedPlayers.sort((a, b) {
          if (a.isStartingXI && !b.isStartingXI) return -1;
          if (!a.isStartingXI && b.isStartingXI) return 1;
          return 0;
        });

        return ListView.builder(
          padding: const EdgeInsets.all(24),
          itemCount: sortedPlayers.length,
          itemBuilder: (context, index) {
            final player = sortedPlayers[index];
            final fatigue = _calculatePlayerFatigue(player, 45);
            final color = _getFatigueColor(fatigue);

            return Card(
              color: const Color(0xFF1E1E1E),
              margin: const EdgeInsets.only(bottom: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
                side: BorderSide(color: player.isStartingXI ? color.withOpacity(0.3) : Colors.transparent, width: 1),
              ),
              child: ListTile(
                contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                title: Row(
                  children: [
                    Text(player.name, style: TextStyle(color: player.isStartingXI ? Colors.white : Colors.white54, fontWeight: FontWeight.bold)),
                    if (player.isStartingXI)
                      Padding(
                        padding: const EdgeInsets.only(left: 8),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(4)),
                          child: const Text('⭐ STARTING XI', style: TextStyle(fontSize: 8, color: Colors.amber)),
                        ),
                      ),
                  ],
                ),
                trailing: player.isStartingXI 
                  ? Text('${fatigue.toStringAsFixed(0)}%', style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 18))
                  : const Text('Bench', style: TextStyle(color: Colors.white24, fontSize: 12)),
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildPossibleChangesTab() {
    if (_opponentId == null) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF00FFCC)));
    }

    final repository = getIt<DataRepository>();
    
    return FutureBuilder<List<dynamic>>(
      future: Future.wait([
        repository.getIngamePlayers(),
        repository.getPregameOpponentWeakness(
          opponentId: _opponentId!,
          stadiumId: _stadiumId,
          gameDate: _gameDate,
        ),
      ]),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator(color: Color(0xFF00FFCC)));
        }
        
        final List<LivePlayerFatigue> roster = (snapshot.data?[0] as List<LivePlayerFatigue>?) ?? [];
        final List<PlayerWeakness> weaknesses = (snapshot.data?[1] as List<PlayerWeakness>?) ?? [];
        
        // 1. Calculate combined scores for all starting XI players
        List<Map<String, dynamic>> candidates = [];
        
        // Helper for diacritic-insensitive matching
        String normalize(String s) {
          return s.toLowerCase()
            .replaceAll('ș', 's').replaceAll('ț', 't')
            .replaceAll('ă', 'a').replaceAll('â', 'a')
            .replaceAll('î', 'i')
            .replaceAll('ş', 's').replaceAll('ţ', 't'); // handle old diacritics too
        }

        for (var player in roster.where((p) => p.isStartingXI)) {
          final fatigue = _calculatePlayerFatigue(player, 45);
          
          // Match by ID (primary) or Name (fallback)
          final weakness = weaknesses.firstWhere(
            (w) => w.id == player.id || (w.name.isNotEmpty && normalize(player.name).contains(normalize(w.name))),
            orElse: () => PlayerWeakness(
              id: '', 
              name: '', 
              physicalState: '', 
              psychologicalState: '', 
              tacticalTendencies: '', 
              exploitRecommendation: '', 
              overallWeaknessScore: 50.0 
            ),
          );
          
          double combinedScore = (fatigue + weakness.overallWeaknessScore) / 2;
          candidates.add({
            'player': player,
            'fatigue': fatigue,
            'weakness': weakness,
            'score': combinedScore,
          });
        }

        // Sort by highest combined score (most vulnerable first)
        candidates.sort((a, b) => (b['score'] as double).compareTo(a['score'] as double));

        // Group bench players by position for faster lookup
        final Map<String, List<Map<String, dynamic>>> benchByPosition = {};
        for (var p in roster.where((p) => !p.isStartingXI)) {
          final weakness = weaknesses.firstWhere(
            (w) => w.id == p.id || (w.name.isNotEmpty && normalize(p.name).contains(normalize(w.name))),
            orElse: () => PlayerWeakness(id: '', name: '', physicalState: '', psychologicalState: '', tacticalTendencies: '', exploitRecommendation: '', overallWeaknessScore: 50.0),
          );
          
          final pos = p.position;
          if (!benchByPosition.containsKey(pos)) benchByPosition[pos] = [];
          benchByPosition[pos]!.add({'player': p, 'score': weakness.overallWeaknessScore});
        }
        
        // Sort each group by LOWEST weakness score (best/most reliable players first)
        benchByPosition.forEach((key, list) {
          list.sort((a, b) => (a['score'] as double).compareTo(b['score'] as double));
        });
        
        // 2. Generate suggestions (at least 2 if available)
        List<HalftimeChange> suggestions = [];
        for (int i = 0; i < candidates.length; i++) {
          final c = candidates[i];
          final double fatigue = c['fatigue'];
          final PlayerWeakness weakness = c['weakness'];
          final LivePlayerFatigue player = c['player'];
          final double score = c['score'];

          // Always include top 2, others only if score is significant (> 40)
          if (i < 2 || score > 40) {
            final pos = player.position;
            final compatibleBench = benchByPosition[pos] ?? [];
            
            String replacementText = "";
            String extraReason = "";
            
            if (compatibleBench.isNotEmpty) {
              final replacementData = compatibleBench.first;
              final replacement = replacementData['player'] as LivePlayerFatigue;
              final double repScore = replacementData['score'];
              
              replacementText = ' \u279c ${replacement.name}';
              extraReason = ' | Best replacement: ${replacement.name} (Reliability: ${(100 - repScore).toStringAsFixed(0)}%)';
              
              // Mark this bench player as "used"
              compatibleBench.removeAt(0);
            } else {
              replacementText = ' (Check Bench)';
            }
            
            suggestions.add(HalftimeChange(
              id: 'off_${player.id}',
              title: 'Sub: ${player.name}$replacementText',
              description: 'Reason: Fatigue (${fatigue.toStringAsFixed(0)}%) + Weakness (${weakness.overallWeaknessScore.toStringAsFixed(0)})$extraReason',
              likelihood: score,
              category: 'Substitution (${player.position})',
            ));
          }
        }
        
        if (suggestions.isEmpty) {
          return const Center(child: Text('No urgent changes recommended.', style: TextStyle(color: Colors.white54)));
        }

        return Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('AI RECOMMENDED CHANGES', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
              const SizedBox(height: 8),
              const Text('Based on real-time fatigue and pre-game scouting scores.', style: TextStyle(color: Colors.white54)),
              const SizedBox(height: 24),
              Expanded(
                child: ListView.builder(
                  itemCount: suggestions.length,
                  itemBuilder: (context, index) {
                    final change = suggestions[index];
                    return Card(
                      color: const Color(0xFF1E1E1E),
                      margin: const EdgeInsets.only(bottom: 16),
                      child: ListTile(
                        contentPadding: const EdgeInsets.all(20),
                        leading: CircleAvatar(
                          backgroundColor: const Color(0xFF00FFCC).withOpacity(0.2),
                          child: Text('${change.likelihood.toStringAsFixed(0)}%', style: const TextStyle(color: Color(0xFF00FFCC), fontWeight: FontWeight.bold, fontSize: 12)),
                        ),
                        title: Text(change.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white)),
                        subtitle: Padding(
                          padding: const EdgeInsets.only(top: 8.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(change.description, style: const TextStyle(color: Colors.white70)),
                              const SizedBox(height: 12),
                              Chip(
                                label: Text(change.category, style: const TextStyle(fontSize: 10, color: Colors.white)),
                                backgroundColor: Colors.white10,
                                visualDensity: VisualDensity.compact,
                              )
                            ],
                          ),
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
}

