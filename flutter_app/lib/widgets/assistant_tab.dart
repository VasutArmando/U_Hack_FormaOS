import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_tts/flutter_tts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../main.dart';
import '../models/match_data.dart';
import '../repositories/data_repository.dart';

class AssistantTab extends StatefulWidget {
  final List<LivePlayerFatigue>? liveFatigue;
  const AssistantTab({super.key, this.liveFatigue});

  @override
  State<AssistantTab> createState() => _AssistantTabState();
}

class _AssistantTabState extends State<AssistantTab> with AutomaticKeepAliveClientMixin {
  final stt.SpeechToText _speech = stt.SpeechToText();
  final FlutterTts _flutterTts = FlutterTts();
  bool _isListening = false;
  bool _isTtsEnabled = true;

  @override
  bool get wantKeepAlive => true;
  String _recognizedText = "Tap the microphone to start asking questions.";
  String _assistantResponse = "";
  bool _isProcessing = false;

  String? _opponentId;
  String? _stadiumId;
  String? _gameDate;

  final TextEditingController _textController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _initSpeech();
    _initTts();
    _loadSettings();
  }

  void _initTts() async {
    await _flutterTts.setLanguage("ro-RO");
    await _flutterTts.setPitch(1.0);
    await _flutterTts.setSpeechRate(0.5);
  }

  Future<void> _speak(String text) async {
    if (_isTtsEnabled && text.isNotEmpty) {
      await _flutterTts.speak(text);
    }
  }

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _opponentId = prefs.getString('settings_next_opponent_id');
      _stadiumId = prefs.getString('settings_stadium_id');
      _gameDate = prefs.getString('settings_game_date');
    });
  }

  void _initSpeech() async {
    if (_speech.isAvailable) return;
    
    try {
      bool available = await _speech.initialize(
        onError: (val) {
          debugPrint('STT onError: $val');
          setState(() => _recognizedText =
              "Mic Error: ${val.errorMsg}. Try typing instead.");
        },
        onStatus: (val) => debugPrint('STT onStatus: $val'),
      );
      if (!available) {
        setState(() => _recognizedText =
            "Speech recognition unavailable. Please use manual input.");
      }
    } catch (e) {
      debugPrint('STT Init Error: $e');
      setState(
          () => _recognizedText = "Mic Init Failed. Please use manual input.");
    }
  }

  void _toggleListening() async {
    // Stop TTS if it's talking so it doesn't interfere with the mic
    await _flutterTts.stop();

    if (!_isListening) {
      bool available = _speech.isAvailable;
      if (!available) {
        available = await _speech.initialize();
      }

      if (available) {
        setState(() {
          _isListening = true;
          _recognizedText = "Listening... (Speak now)";
          _assistantResponse = "";
        });
        _speech.listen(
          onResult: (val) {
            setState(() {
              if (val.recognizedWords.isNotEmpty) {
                _recognizedText = val.recognizedWords;
              }
            });
          },
          listenOptions: stt.SpeechListenOptions(
            listenMode: stt.ListenMode.dictation,
            cancelOnError: true,
            partialResults: true,
          ),
        );
      } else {
        setState(() {
          _isListening = false;
          _recognizedText = "Microphone not available. Try typing below.";
        });
      }
    } else {
      await _speech.stop();
      setState(() {
        _isListening = false;
        // Fallback for demo if silence detected
        if (_recognizedText == "Listening... (Speak now)" ||
            _recognizedText.isEmpty) {
          _recognizedText = "Who is the most tired player?";
        }
      });
      _processVoiceQuery(_recognizedText);
    }
  }

  Future<void> _processVoiceQuery(String query) async {
    if (query.isEmpty || query.contains("Listening...")) return;

    setState(() {
      _isProcessing = true;
      _assistantResponse = "Analyzing tactical data...";
    });

    try {
      final repository = getIt<DataRepository>();
      
      // Convert LivePlayerFatigue models to Maps for the API
      final List<Map<String, dynamic>>? fatigueData = widget.liveFatigue?.map((p) => {
        'name': p.name,
        'fatigue': p.fatigue,
        'position': p.position,
        'isStartingXI': p.isStartingXI,
      }).toList();

      final response = await repository.askAssistant(
        query,
        opponentId: _opponentId,
        stadiumId: _stadiumId,
        gameDate: _gameDate,
        liveFatigue: fatigueData,
      );

      setState(() {
        _assistantResponse = response;
        _isProcessing = false;
      });

      // Speak result aloud if enabled
      _speak(response);
    } catch (e) {
      setState(() {
        _assistantResponse = "AI Analysis failed. Check if backend is running.";
        _isProcessing = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    return Scaffold(
      body: Container(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Icon(Icons.psychology, color: Color(0xFF00FFCC), size: 32),
                  SizedBox(width: 12),
                  Text(
                    'OMNISCIENT AI',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.5,
                    ),
                  ),
                ],
              ),
              // TTS Switch
              Row(
                children: [
                  Icon(
                    _isTtsEnabled ? Icons.volume_up : Icons.volume_off,
                    color: const Color(0xFF00FFCC).withValues(alpha: 0.7),
                    size: 20,
                  ),
                  Transform.scale(
                    scale: 0.8,
                    child: Switch(
                      value: _isTtsEnabled,
                      onChanged: (val) {
                        setState(() => _isTtsEnabled = val);
                        if (!val) _flutterTts.stop();
                      },
                      activeThumbColor: const Color(0xFF00FFCC),
                      activeTrackColor: const Color(0xFF00FFCC).withValues(alpha: 0.3),
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Message Output Area
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildMessageBubble(
                    title: 'COMMAND / VOICE',
                    text: _recognizedText,
                    color: Colors.white10,
                    textColor: Colors.white70,
                    icon: Icons.mic,
                  ),
                  const SizedBox(height: 20),
                  if (_assistantResponse.isNotEmpty || _isProcessing)
                    _buildMessageBubble(
                      title: 'AI STRATEGY',
                      text: _assistantResponse,
                      color: const Color(0xFF00FFCC).withValues(alpha: 0.1),
                      textColor: const Color(0xFF00FFCC),
                      icon: Icons.auto_awesome,
                      isProcessing: _isProcessing,
                    ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          // Control Area
          Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  decoration: BoxDecoration(
                    color: Colors.white10,
                    borderRadius: BorderRadius.circular(30),
                    border: Border.all(color: Colors.white24),
                  ),
                  child: TextField(
                    controller: _textController,
                    style: const TextStyle(color: Colors.white),
                    decoration: const InputDecoration(
                      hintText: 'Type tactical question...',
                      hintStyle: TextStyle(color: Colors.white38),
                      border: InputBorder.none,
                    ),
                    onSubmitted: (val) {
                      if (val.isNotEmpty) {
                        _recognizedText = val;
                        _processVoiceQuery(val);
                        _textController.clear();
                      }
                    },
                  ),
                ),
              ),
              const SizedBox(width: 12),
              GestureDetector(
                onTap: _toggleListening,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 300),
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(
                    color: _isListening ? Colors.red : const Color(0xFF00FFCC),
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: (_isListening
                                ? Colors.red
                                : const Color(0xFF00FFCC))
                            .withValues(alpha: 0.4),
                        blurRadius: _isListening ? 15 : 8,
                      )
                    ],
                  ),
                  child: Icon(
                    _isListening ? Icons.stop : Icons.mic,
                    color: Colors.black,
                    size: 28,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            _isListening ? 'LISTENING... TAP TO STOP' : 'USE MIC OR TYPE ABOVE',
            style: TextStyle(
              color: _isListening ? Colors.red : Colors.white38,
              fontSize: 10,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.0,
            ),
          ),
        ],
      ),
    ),
   );
  }

  Widget _buildMessageBubble({
    required String title,
    required String text,
    required Color color,
    required Color textColor,
    required IconData icon,
    bool isProcessing = false,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: textColor.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: textColor, size: 16),
              const SizedBox(width: 8),
              Text(
                title,
                style: TextStyle(
                  color: textColor,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.0,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (isProcessing)
            const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                  color: Color(0xFF00FFCC), strokeWidth: 2),
            )
          else
            Text(
              text,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                height: 1.5,
              ),
            ),
        ],
      ),
    );
  }
}
