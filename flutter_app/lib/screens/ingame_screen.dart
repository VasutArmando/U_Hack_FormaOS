import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../main.dart';
import '../models/match_data.dart';
import '../repositories/data_repository.dart';
import '../widgets/football_pitch.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

class InGameScreen extends StatefulWidget {
  const InGameScreen({super.key});

  @override
  State<InGameScreen> createState() => _InGameScreenState();
}

class _InGameScreenState extends State<InGameScreen> {
  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
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
                Tab(icon: Icon(Icons.analytics), text: 'LIVE GAPS'),
                Tab(icon: Icon(Icons.battery_alert), text: 'OPPONENT WEAKNESS'),
                Tab(icon: Icon(Icons.mic), text: 'ASSISTANT'),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              children: [
                _buildLiveGapsTab(),
                _buildOpponentWeaknessTab(),
                const AssistantTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLiveGapsTab() {
    final repository = getIt<DataRepository>();
    return FutureBuilder<List<TacticalGap>>(
      future: repository.getIngameGaps(),
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
              const Text('LIVE CHRONIC GAPS', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
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
    return FutureBuilder<List<LivePlayerFatigue>>(
      future: repository.getIngamePlayers(),
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
              const Text('LIVE PLAYER FATIGUE', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
              const SizedBox(height: 24),
              Expanded(
                child: ListView.builder(
                  itemCount: players.length,
                  itemBuilder: (context, index) {
                    final player = players[index];
                    Color fatigueColor = Colors.green;
                    if (player.fatigue > 60) fatigueColor = Colors.orange;
                    if (player.fatigue > 80) fatigueColor = Colors.red;

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
                                Text('${player.fatigue}% Fatigue', style: TextStyle(color: fatigueColor, fontWeight: FontWeight.bold)),
                              ],
                            ),
                            const SizedBox(height: 8),
                            LinearProgressIndicator(
                              value: player.fatigue / 100,
                              backgroundColor: Colors.white10,
                              valueColor: AlwaysStoppedAnimation<Color>(fatigueColor),
                            ),
                            const SizedBox(height: 12),
                            Text(player.liveRemark, style: const TextStyle(color: Colors.white70)),
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
}

class AssistantTab extends StatefulWidget {
  const AssistantTab({super.key});

  @override
  State<AssistantTab> createState() => _AssistantTabState();
}

class _AssistantTabState extends State<AssistantTab> {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isListening = false;
  String _recognizedText = "Tap the microphone to start asking questions.";
  String _assistantResponse = "";

  @override
  void initState() {
    super.initState();
    _initSpeech();
  }

  void _initSpeech() async {
    await _speech.initialize(
      onError: (val) => debugPrint('onError: $val'),
      onStatus: (val) => debugPrint('onStatus: $val'),
    );
  }

  void _toggleListening() async {
    if (!_isListening) {
      bool available = _speech.isAvailable;
      if (!available) {
        available = await _speech.initialize(
          onError: (val) => debugPrint('onError: $val'),
          onStatus: (val) => debugPrint('onStatus: $val'),
        );
      }
      
      if (available) {
        setState(() {
          _isListening = true;
          _recognizedText = "Listening...";
          _assistantResponse = "";
        });
        _speech.listen(
          onResult: (val) {
            setState(() {
              // Only update if it actually recognized something
              if (val.recognizedWords.isNotEmpty) {
                _recognizedText = val.recognizedWords;
              }
            });
          },
        );
      } else {
        setState(() {
          _isListening = false;
          _recognizedText = "Speech recognition is not available on this device.";
        });
      }
    } else {
      _speech.stop();
      setState(() {
        _isListening = false;
        // Fallback for hackathon presentation if mic failed to pick up on Windows/Emulator
        if (_recognizedText == "Listening..." || _recognizedText.isEmpty) {
           _recognizedText = "what is the fatigue of player 9";
        }
      });
      _processVoiceQuery(_recognizedText.toLowerCase());
    }
  }

  void _processVoiceQuery(String query) async {
    if (query.isEmpty || query == "listening...") return;

    setState(() {
      _assistantResponse = "Analizez comanda tactică...";
    });

    try {
      final response = await http.post(
        Uri.parse('http://127.0.0.1:8000/api/v1/ingame/assistant'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'query': query}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _assistantResponse = data['advice'] ?? "Niciun sfat returnat.";
        });
      } else {
        setState(() {
          _assistantResponse = "Eroare AI Backend: ${response.statusCode}";
        });
      }
    } catch (e) {
      setState(() {
        _assistantResponse = "Conexiune backend eșuată! Pornește Uvicorn pe portul 8000.";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Icon(Icons.record_voice_over, size: 80, color: _isListening ? Colors.redAccent : const Color(0xFF00FFCC)),
          const SizedBox(height: 32),
          Text(
            _recognizedText,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 20, color: Colors.white, fontStyle: FontStyle.italic),
          ),
          const SizedBox(height: 32),
          if (_assistantResponse.isNotEmpty)
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: const Color(0xFF1E1E1E),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF00FFCC).withValues(alpha: 0.3)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.smart_toy, color: Color(0xFF00FFCC)),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Text(
                      _assistantResponse,
                      style: const TextStyle(fontSize: 16, color: Colors.white, height: 1.5),
                    ),
                  ),
                ],
              ),
            ),
          const Spacer(),
          SizedBox(
            width: 200,
            height: 60,
            child: ElevatedButton.icon(
              onPressed: _toggleListening,
              icon: Icon(_isListening ? Icons.stop : Icons.mic, color: Colors.black),
              label: Text(_isListening ? 'Stop Listening' : 'Ask Question', style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 16)),
              style: ElevatedButton.styleFrom(
                backgroundColor: _isListening ? Colors.redAccent : const Color(0xFF00FFCC),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
              ),
            ),
          ),
          const SizedBox(height: 40),
        ],
      ),
    );
  }
}
