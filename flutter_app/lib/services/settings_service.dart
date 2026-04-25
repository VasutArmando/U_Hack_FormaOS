import 'package:shared_preferences/shared_preferences.dart';

class SettingsService {
  static const String _keyNextOpponentId = 'settings_next_opponent_id';
  static const String _keyGameDate = 'settings_game_date';
  static const String _keyMatchTime = 'settings_match_time';
  static const String _keyStadiumId = 'settings_stadium_id';

  Future<void> saveSettings({
    required String? nextOpponentId,
    required String? gameDate,
    required String? matchTime,
    required String? stadiumId,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    if (nextOpponentId != null) {
      await prefs.setString(_keyNextOpponentId, nextOpponentId);
    }
    if (gameDate != null) await prefs.setString(_keyGameDate, gameDate);
    if (matchTime != null) await prefs.setString(_keyMatchTime, matchTime);
    if (stadiumId != null) await prefs.setString(_keyStadiumId, stadiumId);
  }

  Future<Map<String, String?>> loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    return {
      'nextOpponentId': prefs.getString(_keyNextOpponentId),
      'gameDate': prefs.getString(_keyGameDate),
      'matchTime': prefs.getString(_keyMatchTime),
      'stadiumId': prefs.getString(_keyStadiumId),
    };
  }
}
