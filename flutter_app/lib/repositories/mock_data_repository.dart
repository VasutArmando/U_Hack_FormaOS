import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/match_data.dart';
import 'data_repository.dart';

class MockDataRepository implements DataRepository {
  Future<List<dynamic>> _loadJsonList(String path) async {
    final String response = await rootBundle.loadString(path);
    return await json.decode(response) as List<dynamic>;
  }

  @override
  Future<List<Team>> getTeams() async {
    final data = await _loadJsonList('assets/mock_data/teams.json');
    return data.map((json) => Team.fromJson(json)).toList();
  }

  @override
  Future<List<Stadium>> getStadiums() async {
    final data = await _loadJsonList('assets/mock_data/stadiums.json');
    return data.map((json) => Stadium.fromJson(json)).toList();
  }

  @override
  Future<List<TacticalGap>> getPregameGaps({String? opponentId}) async {
    final data = await _loadJsonList('assets/mock_data/pregame_gaps.json');
    return data.map((json) => TacticalGap.fromJson(json)).toList();
  }

  @override
  Future<List<PlayerWeakness>> getPregameOpponentWeakness({String? opponentId, String? stadiumId, String? gameDate}) async {
    final data = await _loadJsonList('assets/mock_data/pregame_opponent_weakness.json');
    return data.map((json) => PlayerWeakness.fromJson(json)).toList();
  }

  @override
  Future<List<TacticalGap>> getIngameGaps() async {
    final data = await _loadJsonList('assets/mock_data/ingame_gaps.json');
    return data.map((json) => TacticalGap.fromJson(json)).toList();
  }

  @override
  Future<List<LivePlayerFatigue>> getIngamePlayers() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final opponentId = prefs.getString('settings_next_opponent_id');
      final teams = await getTeams();
      final opponent = teams.firstWhere((t) => t.id == opponentId, orElse: () => Team(id: '', name: ''));
      
      if (opponent.name.isEmpty) return [];

      final String response = await rootBundle.loadString('assets/mock_data/players.json');
      final Map<String, dynamic> data = json.decode(response);
      final List<dynamic> allPlayers = data['players'];

      // Fuzzy match team names (ignoring diacritics/case for common ones)
      String targetTeam = opponent.name;
      if (targetTeam == "Farul Constanta") targetTeam = "Farul Constanţa";
      if (targetTeam == "Dinamo Bucuresti") targetTeam = "Dinamo Bucureşti";
      if (targetTeam == "Rapid Bucuresti") targetTeam = "Rapid Bucureşti";
      if (targetTeam == "Otelul Galati") targetTeam = "Oţelul";
      if (targetTeam == "Petrolul Ploiesti") targetTeam = "Petrolul 52";
      if (targetTeam == "FCSB") targetTeam = "FCS Bucureşti";

      final teamPlayers = allPlayers.where((p) => p['teamname'] == targetTeam).toList();

      return teamPlayers.map((p) {
        double height = (p['height'] ?? 0).toDouble();
        double weight = (p['weight'] ?? 0).toDouble();
        if (weight <= 0) {
          weight = (height > 0) ? (height - 105).clamp(65, 95) : 75.0;
        }

        String role = p['role']?['name'] ?? 'Unknown';
        String posCode = 'Unknown';
        if (role == 'Goalkeeper') posCode = 'GK';
        else if (role == 'Defender') posCode = 'DF';
        else if (role == 'Midfielder') posCode = 'MD';
        else if (role == 'Forward') posCode = 'FW';

        return LivePlayerFatigue(
          id: (p['wyId'] ?? '').toString(),
          name: '${p['shortName']} ($posCode)',
          fatigue: 0.0, // Will be calculated in UI
          liveRemark: '', // Will be generated in UI
          weight: weight,
          position: posCode,
        );
      }).toList();
    } catch (e) {
      debugPrint('Error loading players: $e');
      return [];
    }
  }

  @override
  Future<List<TacticalGap>> getHalftimeGaps() async {
    final data = await _loadJsonList('assets/mock_data/halftime_gaps.json');
    return data.map((json) => TacticalGap.fromJson(json)).toList();
  }

  @override
  Future<List<HalftimeChange>> getHalftimeChanges() async {
    final data = await _loadJsonList('assets/mock_data/halftime_changes.json');
    return data.map((json) => HalftimeChange.fromJson(json)).toList();
  }

  @override
  Future<String> askAssistant(String query, {String? opponentId, String? stadiumId, String? gameDate, List<Map<String, dynamic>>? liveFatigue}) async {
    return "Mock AI Assistant: Analyzing '$query' for opponent $opponentId. (Switch to live mode for Gemini responses)";
  }
}
