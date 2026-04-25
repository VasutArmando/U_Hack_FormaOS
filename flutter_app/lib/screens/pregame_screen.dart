import 'package:flutter/material.dart';
import '../main.dart';
import '../models/match_data.dart';
import '../repositories/data_repository.dart';
import '../widgets/football_pitch.dart';

class PregameScreen extends StatefulWidget {
  const PregameScreen({Key? key}) : super(key: key);

  @override
  State<PregameScreen> createState() => _PregameScreenState();
}

class _PregameScreenState extends State<PregameScreen> {
  String _weaknessFilter = 'All';

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
    final repository = getIt<DataRepository>();
    return FutureBuilder<List<TacticalGap>>(
      future: repository.getPregameGaps(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator(color: Color(0xFF00FFCC)));
        } else if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}', style: const TextStyle(color: Colors.red)));
        }
        
        final gaps = snapshot.data ?? [];
        return SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('PREDICTED TACTICAL GAPS', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
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
                    Text(gap.location, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white)),
                    Chip(
                      label: Text(gap.severity, style: const TextStyle(fontSize: 10, color: Colors.white)),
                      backgroundColor: gap.severity == 'Critical' ? Colors.red : Colors.orange,
                    )
                  ],
                ),
                const SizedBox(height: 8),
                Text(gap.description, style: const TextStyle(color: Colors.white70)),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildOpponentWeaknessTab() {
    final repository = getIt<DataRepository>();
    return FutureBuilder<List<PlayerWeakness>>(
      future: repository.getPregameOpponentWeakness(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator(color: Color(0xFF00FFCC)));
        } else if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}', style: const TextStyle(color: Colors.red)));
        }
        
        final players = snapshot.data ?? [];
        return Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('OPPONENT PLAYER WEAKNESSES', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
              const SizedBox(height: 16),
              Row(
                children: [
                  _buildFilterChip('All'),
                  const SizedBox(width: 8),
                  _buildFilterChip('Physical State'),
                  const SizedBox(width: 8),
                  _buildFilterChip('Psychological State'),
                ],
              ),
              const SizedBox(height: 24),
              Expanded(
                child: ListView.builder(
                  itemCount: players.length,
                  itemBuilder: (context, index) {
                    final player = players[index];
                    return Card(
                      color: const Color(0xFF1E1E1E),
                      margin: const EdgeInsets.only(bottom: 16),
                      child: Padding(
                        padding: const EdgeInsets.all(20.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(player.name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white)),
                                Text('Score: ${player.overallWeaknessScore}', style: const TextStyle(color: Color(0xFF00FFCC), fontWeight: FontWeight.bold)),
                              ],
                            ),
                            const Divider(color: Colors.white10, height: 24),
                            if (_weaknessFilter == 'All' || _weaknessFilter == 'Physical State')
                              Padding(
                                padding: const EdgeInsets.only(bottom: 8.0),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Icon(Icons.fitness_center, size: 18, color: Colors.orangeAccent),
                                    const SizedBox(width: 8),
                                    Expanded(child: Text('Physical: ${player.physicalState}', style: const TextStyle(color: Colors.white70))),
                                  ],
                                ),
                              ),
                            if (_weaknessFilter == 'All' || _weaknessFilter == 'Psychological State')
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Icon(Icons.psychology, size: 18, color: Colors.blueAccent),
                                  const SizedBox(width: 8),
                                  Expanded(child: Text('Psychological: ${player.psychologicalState}', style: const TextStyle(color: Colors.white70))),
                                ],
                              )
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

  Widget _buildFilterChip(String label) {
    return ChoiceChip(
      label: Text(label),
      selected: _weaknessFilter == label,
      onSelected: (bool selected) {
        setState(() {
          if (selected) _weaknessFilter = label;
        });
      },
      selectedColor: const Color(0xFF00FFCC).withOpacity(0.3),
      backgroundColor: Colors.white10,
      labelStyle: TextStyle(color: _weaknessFilter == label ? const Color(0xFF00FFCC) : Colors.white),
    );
  }
}
