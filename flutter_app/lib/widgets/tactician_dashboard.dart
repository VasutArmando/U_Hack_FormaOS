import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_tts/flutter_tts.dart';
import '../bloc/match_cubit.dart';

class TacticianDashboard extends StatefulWidget {
  const TacticianDashboard({super.key});

  @override
  State<TacticianDashboard> createState() => _TacticianDashboardState();
}

class _TacticianDashboardState extends State<TacticianDashboard> {
  final stt.SpeechToText _speech = stt.SpeechToText();
  final FlutterTts _tts = FlutterTts();
  
  bool _isListening = false;
  String _spokenText = "Țineți apăsat pentru a întreba TACTICIAN-ul...";
  String _lastAiResponse = "";

  @override
  void initState() {
    super.initState();
    _initTts();
  }

  Future<void> _initTts() async {
    // Configurare Enterprise Voice: Limba Română fluentă
    await _tts.setLanguage("ro-RO");
    await _tts.setSpeechRate(0.5); // Ritm clar, dictat, sobru
    await _tts.setPitch(1.0);
  }

  void _listen() async {
    if (!_isListening) {
      bool available = await _speech.initialize(
        onStatus: (val) => debugPrint('STT Status: \$val'),
        onError: (val) => debugPrint('STT Eroare Hardware Microfon: \$val'),
      );
      if (available) {
        setState(() => _isListening = true);
        _speech.listen(
          onResult: (val) {
            setState(() {
              _spokenText = val.recognizedWords;
            });
          },
          localeId: "ro_RO", // Forțăm dicționarul în Română
        );
      }
    } else {
      // Operatorul a ridicat degetul (Push-To-Talk)
      setState(() => _isListening = false);
      _speech.stop();
      
      // Imediat ce termină de vorbit, propulsăm transcrierea spre Baza de Date/API!
      if (_spokenText.isNotEmpty && _spokenText != "Țineți apăsat pentru a întreba TACTICIAN-ul...") {
        context.read<MatchCubit>().askTacticianVoiceCommand(_spokenText);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocListener<MatchCubit, MatchState>(
      listener: (context, state) {
        if (state is MatchLoaded) {
          final advice = state.matchData['latest_ai_advice'] as String?;
          // Când intră pe rețea un Răspuns Nou de la Vertex AI:
          if (advice != null && advice != _lastAiResponse) {
            setState(() => _lastAiResponse = advice);
            // DECLANȘĂM TEXT-TO-SPEECH AUTOMAT ÎN CĂȘTI (Zero Ecran Necesar!)
            _tts.speak(_lastAiResponse);
          }
        }
      },
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.psychology, size: 80, color: Colors.blueAccent),
            const SizedBox(height: 20),
            Text(
              "ASISTENT TACTIC (VOICE-FIRST)",
              style: TextStyle(color: Colors.white.withOpacity(0.7), letterSpacing: 2.0, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 40),
            
            // Display-ul de Transcriere Live (Feedback vizual instant)
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: _isListening ? Colors.redAccent : Colors.white12)
              ),
              child: Text(
                _spokenText,
                style: const TextStyle(color: Colors.white, fontSize: 18),
                textAlign: TextAlign.center,
              ),
            ),
            
            const Spacer(),
            
            // Buton Masiv "Push-To-Talk" optimizat pentru antrenorul pe gazon (cu orbire la soare)
            GestureDetector(
              onTapDown: (_) => _listen(),
              onTapUp: (_) => _listen(), // Oprește și execută la release
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: _isListening ? 120 : 100,
                height: _isListening ? 120 : 100,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _isListening ? Colors.redAccent : Colors.blueAccent,
                  boxShadow: _isListening ? [
                    BoxShadow(color: Colors.redAccent.withOpacity(0.6), blurRadius: 30, spreadRadius: 10)
                  ] : [],
                ),
                child: const Icon(Icons.mic, color: Colors.white, size: 50),
              ),
            ),
            const SizedBox(height: 20),
            Text(
              _isListening ? "ASCULT... (ELIBEREAZĂ PENTRU A TRIMITE)" : "ȚINE APĂSAT PENTRU COMANDĂ VOCALĂ",
              style: TextStyle(color: _isListening ? Colors.redAccent : Colors.blueAccent, fontWeight: FontWeight.bold),
            ),
            
            const Spacer(),
            
            // Afișăm textual Ultimul Sfat (Ca subtitrare în caz de zgomot pe stadion)
            if (_lastAiResponse.isNotEmpty)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF1B1B1B),
                  border: Border(left: BorderSide(
                    color: _lastAiResponse.contains("OFFLINE") ? Colors.amberAccent : Colors.greenAccent, 
                    width: 4
                  ))
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (_lastAiResponse.contains("OFFLINE"))
                      Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: Colors.amberAccent.withOpacity(0.2), borderRadius: BorderRadius.circular(4)),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.warning_amber_rounded, color: Colors.amberAccent, size: 14),
                            SizedBox(width: 6),
                            Text("MOD OFFLINE / EURISTIC ACTIVAT", style: TextStyle(color: Colors.amberAccent, fontWeight: FontWeight.bold, fontSize: 10))
                          ]
                        )
                      ),
                    Text(
                      _lastAiResponse,
                      style: const TextStyle(color: Colors.white, fontStyle: FontStyle.italic),
                    ),
                  ],
                ),
              ),
              
            // NOU: Arborele de Decizii AI
            BlocBuilder<MatchCubit, MatchState>(
              builder: (context, state) {
                if (state is MatchLoaded) {
                  final tree = state.matchData['decision_tree'] as List?;
                  if (tree != null && tree.isNotEmpty) {
                    return _buildDecisionTree(tree);
                  }
                }
                return const SizedBox.shrink();
              }
            ),
              
            // Card Inteligent de Predicție a Viitorului
            if (_lastAiResponse.toLowerCase().contains("înlocui") || _lastAiResponse.toLowerCase().contains("substituție"))
              Container(
                margin: const EdgeInsets.only(top: 20),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.blueAccent.withOpacity(0.15),
                  border: Border.all(color: Colors.blueAccent, width: 2),
                  borderRadius: BorderRadius.circular(12)
                ),
                child: Row(
                  children: [
                    const Icon(Icons.swap_horiz, color: Colors.blueAccent, size: 36),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Text(
                        "Oportunitate: Iese Nr. 9, Intră Nr. 17", 
                        style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)
                      )
                    ),
                    ElevatedButton.icon(
                      icon: const Icon(Icons.science, size: 16),
                      label: const Text("PREVIEW IMPACT", style: TextStyle(fontWeight: FontWeight.bold)),
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.blueAccent),
                      onPressed: () async {
                         final result = await context.read<MatchCubit>().simulateSubstitution("9", "17");
                         if (mounted) {
                           showDialog(context: context, builder: (_) => AlertDialog(
                              backgroundColor: const Color(0xFF1B1B1B),
                              title: const Text("ORACLE: Simulare Teritorială", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                              content: Column(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.radar, color: Colors.greenAccent, size: 80),
                                  const SizedBox(height: 20),
                                  Text(
                                    result['tactical_message'] ?? "+12.4% dominație",
                                    style: const TextStyle(color: Colors.greenAccent, fontSize: 24, fontWeight: FontWeight.bold),
                                    textAlign: TextAlign.center,
                                  ),
                                  const SizedBox(height: 15),
                                  const Text("Zona de control Voronoi a noului jucător se extinde cu 4.2m² datorită vitezei superioare de sprint (28 km/h). Riscul defensiv scade cu 80%.", 
                                    style: TextStyle(color: Colors.white70, fontSize: 14), textAlign: TextAlign.center,)
                                ]
                              ),
                              actions: [
                                TextButton(onPressed: () => Navigator.pop(context), child: const Text("ÎNCHIDE PREVIEW", style: TextStyle(color: Colors.grey)))
                              ]
                           ));
                         }
                      }
                    )
                  ]
                )
              )
          ],
        ),
      ),
    );
  }

  Widget _buildDecisionTree(List tree) {
    return Container(
      margin: const EdgeInsets.only(top: 20),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1B1B1B),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white24)
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.account_tree_outlined, color: Colors.greenAccent),
              SizedBox(width: 8),
              Text("AI DECISION TREE (PONDERI MATEMATICE)", style: TextStyle(color: Colors.greenAccent, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
            ],
          ),
          const SizedBox(height: 16),
          ...tree.map((node) {
            final double weight = (node['weight_pct'] as num).toDouble();
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(child: Text(node['factor'].toString(), style: const TextStyle(color: Colors.white70, fontSize: 14), overflow: TextOverflow.ellipsis)),
                      Text("\${weight.toInt()}%", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const SizedBox(height: 6),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: weight / 100.0,
                      backgroundColor: Colors.white10,
                      color: weight >= 40 ? Colors.greenAccent : (weight >= 25 ? Colors.blueAccent : Colors.amberAccent),
                      minHeight: 6,
                    ),
                  )
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}
