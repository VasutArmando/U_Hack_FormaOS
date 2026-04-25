import 'package:flutter/material.dart';
import '../main.dart';
import '../models/match_data.dart';
import '../repositories/data_repository.dart';
import '../widgets/football_pitch.dart';

class HalftimeScreen extends StatefulWidget {
  const HalftimeScreen({Key? key}) : super(key: key);

  @override
  State<HalftimeScreen> createState() => _HalftimeScreenState();
}

class _HalftimeScreenState extends State<HalftimeScreen> {
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
                Tab(icon: Icon(Icons.analytics), text: 'CHRONIC GAPS (UPDATED)'),
                Tab(icon: Icon(Icons.change_circle), text: 'POSSIBLE CHANGES'),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              children: [
                _buildHalftimeGapsTab(),
                _buildPossibleChangesTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHalftimeGapsTab() {
    final repository = getIt<DataRepository>();
    return FutureBuilder<List<TacticalGap>>(
      future: repository.getHalftimeGaps(),
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
              const Text('1ST HALF TACTICAL GAPS EVOLUTION', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
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

  Widget _buildPossibleChangesTab() {
    final repository = getIt<DataRepository>();
    return FutureBuilder<List<HalftimeChange>>(
      future: repository.getHalftimeChanges(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator(color: Color(0xFF00FFCC)));
        } else if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}', style: const TextStyle(color: Colors.red)));
        }
        
        final changes = snapshot.data ?? [];
        return Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('PREDICTED TACTICAL CHANGES', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
              const SizedBox(height: 8),
              const Text('Ranked by AI likelihood based on first-half data.', style: TextStyle(color: Colors.white54)),
              const SizedBox(height: 24),
              Expanded(
                child: ListView.builder(
                  itemCount: changes.length,
                  itemBuilder: (context, index) {
                    final change = changes[index];
                    return Card(
                      color: const Color(0xFF1E1E1E),
                      margin: const EdgeInsets.only(bottom: 16),
                      child: ListTile(
                        contentPadding: const EdgeInsets.all(20),
                        leading: CircleAvatar(
                          backgroundColor: const Color(0xFF00FFCC).withOpacity(0.2),
                          child: Text('${change.likelihood}%', style: const TextStyle(color: Color(0xFF00FFCC), fontWeight: FontWeight.bold, fontSize: 12)),
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
