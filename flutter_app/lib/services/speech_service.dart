import 'package:flutter/foundation.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

class SpeechService {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isInitialized = false;

  Future<bool> initialize() async {
    if (!_isInitialized) {
      _isInitialized = await _speech.initialize(
        onError: (error) => debugPrint("Speech recognition error: \$error"),
        onStatus: (status) => debugPrint("Speech recognition status: \$status"),
      );
    }
    return _isInitialized;
  }

  void startListening(Function(String) onResult) {
    if (_isInitialized && !_speech.isListening) {
      _speech.listen(onResult: (result) {
        onResult(result.recognizedWords);
      });
    }
  }

  void stopListening() {
    if (_speech.isListening) {
      _speech.stop();
    }
  }

  bool get isListening => _speech.isListening;
}
