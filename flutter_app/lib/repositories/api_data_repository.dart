import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/match_data.dart';
import 'data_repository.dart';

class ApiDataRepository implements DataRepository {
  final String baseUrl;

  ApiDataRepository({this.baseUrl = 'http://127.0.0.1:8000'});

  Future<List<dynamic>> _fetchList(String endpoint, {Duration timeout = const Duration(seconds: 30)}) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl$endpoint')).timeout(timeout);
      if (response.statusCode == 200) {
        return json.decode(response.body) as List<dynamic>;
      } else {
        print('Error fetching data from $endpoint: ${response.statusCode}');
        return [];
      }
    } catch (e) {
      print('Exception fetching data from $endpoint: $e');
      return [];
    }
  }

  Future<Map<String, dynamic>?> _fetchMap(String endpoint, {Duration timeout = const Duration(seconds: 10)}) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl$endpoint')).timeout(timeout);
      if (response.statusCode == 200) {
        return json.decode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      print('Exception fetching map from $endpoint: $e');
    }
    return null;
  }

  @override
  Future<List<Team>> getTeams() async {
    final data = await _fetchList('/api/v1/settings/teams');
    return data.map((json) => Team.fromJson(json)).toList();
  }

  @override
  Future<List<Stadium>> getStadiums() async {
    final data = await _fetchList('/api/v1/settings/stadiums');
    return data.map((json) => Stadium.fromJson(json)).toList();
  }

  @override
  Future<List<TacticalGap>> getPregameGaps({String? opponentId}) async {
    String url = '/api/v1/pregame/chronic-gaps';
    if (opponentId != null) url += '?opponent_id=$opponentId';
    final data = await _fetchList(url);
    return data.map((json) => TacticalGap.fromJson(json)).toList();
  }

  @override
  Future<List<PlayerWeakness>> getPregameOpponentWeakness({String? opponentId, String? stadiumId, String? gameDate}) async {
    String url = '/api/v1/pregame/opponent-weakness';
    List<String> params = [];
    if (opponentId != null) params.add('opponent_id=$opponentId');
    if (stadiumId != null) params.add('stadium_id=$stadiumId');
    if (gameDate != null) params.add('game_date=${Uri.encodeComponent(gameDate)}');
    if (params.isNotEmpty) url += '?${params.join('&')}';
    
    // First load requires Gemini to process the full squad (~2min); cached loads are <5s
    final data = await _fetchList(url, timeout: const Duration(minutes: 5));
    return data.map((json) => PlayerWeakness.fromJson(json)).toList();
  }

  Future<MatchWeather?> getMatchWeather({required String stadiumId, String? gameDate}) async {
    String url = '/api/v1/pregame/match-weather?stadium_id=$stadiumId';
    if (gameDate != null) url += '&game_date=${Uri.encodeComponent(gameDate)}';
    final data = await _fetchMap(url);
    if (data == null) return null;
    return MatchWeather.fromJson(data);
  }

  @override
  Future<List<TacticalGap>> getIngameGaps() async {
    final data = await _fetchList('/api/v1/ingame/live-gaps');
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

      // Team name is now synced across teams.json, players.json and starting11.json
      String targetTeam = opponent.name;

      final teamPlayers = allPlayers.where((p) => p['teamname'] == targetTeam).toList();

      final String starting11Response = await rootBundle.loadString('assets/mock_data/starting11.json');
      final Map<String, dynamic> starting11Data = json.decode(starting11Response);
      
      // Get the correct key for the JSON user provided
      // Find the best match in starting11Data
      String starting11Key = targetTeam;
      if (!starting11Data.containsKey(targetTeam)) {
        for (var key in starting11Data.keys) {
          // Normalize both for comparison
          String normalizedKey = key.toLowerCase().replaceAll(RegExp(r'[^a-z0-9]'), '');
          String normalizedTarget = targetTeam.toLowerCase().replaceAll(RegExp(r'[^a-z0-9]'), '');
          
          if (normalizedKey.contains(normalizedTarget) || normalizedTarget.contains(normalizedKey)) {
            starting11Key = key;
            break;
          }
        }
      }

      final List<dynamic> teamStarting11List = starting11Data[starting11Key] ?? starting11Data[targetTeam] ?? [];

      List<LivePlayerFatigue> finalRoster = [];

      // 1. Add exact Starting XI from the provided JSON
      for (int i = 0; i < teamStarting11List.length; i++) {
        final p = teamStarting11List[i];
        final String name = p['name'] ?? 'Unknown';
        final String role = p['position'] ?? 'Unknown';
        
        // Attempt to find the real player in the roster to get their wyId and weight
        var realPlayer = teamPlayers.firstWhere((tp) {
          String tpShort = (tp['shortName'] ?? "").toString().toLowerCase();
          String tpFull = ("${tp['firstName']} ${tp['lastName']}").toLowerCase();
          String target = name.toLowerCase();
          return tpShort.contains(target) || target.contains(tpShort) || tpFull.contains(target) || target.contains(tpFull);
        }, orElse: () => null);

        String wyId = realPlayer != null ? realPlayer['wyId'].toString() : 'starter_$i';
        double height = realPlayer != null ? (realPlayer['height'] ?? 0).toDouble() : 0.0;
        double weight = realPlayer != null ? (realPlayer['weight'] ?? 0).toDouble() : 0.0;
        if (weight <= 0) {
          weight = (height > 0) ? (height - 105).clamp(65, 95) : 75.0;
        }

        String posCode = 'Unknown';
        if (role == 'Goalkeeper') posCode = 'GK';
        else if (role == 'Defender') posCode = 'DF';
        else if (role == 'Midfielder') posCode = 'MD';
        else if (role == 'Forward') posCode = 'FW';

        finalRoster.add(LivePlayerFatigue(
          id: wyId,
          name: '$name ($posCode)',
          fatigue: 0.0,
          liveRemark: '',
          weight: weight,
          position: posCode,
          isStartingXI: true,
        ));
      }

      // 2. Add bench from players (1).json
      for (var p in teamPlayers) {
        final String wyId = (p['wyId'] ?? "").toString();
        
        // Prevent adding a player to the bench if they're already in the starting XI
        bool isAlreadyStarter = finalRoster.any((starter) => starter.id == wyId);
        
        if (!isAlreadyStarter) {
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

            finalRoster.add(LivePlayerFatigue(
              id: p['wyId']?.toString() ?? 'unknown',
              name: '${p['shortName']} ($posCode)',
              fatigue: 0.0,
              liveRemark: '',
              weight: weight,
              position: posCode,
              isStartingXI: false,
            ));
        }
      }

      return finalRoster;
    } catch (e) {
      debugPrint('Error loading players: $e');
      return [];
    }
  }

  @override
  Future<List<TacticalGap>> getHalftimeGaps() async {
    final data = await _fetchList('/api/v1/halftime/tactical-gaps');
    return data.map((json) => TacticalGap.fromJson(json)).toList();
  }

  @override
  Future<List<HalftimeChange>> getHalftimeChanges() async {
    final data = await _fetchList('/api/v1/halftime/predicted-changes');
    return data.map((json) => HalftimeChange.fromJson(json)).toList();
  }

  @override
  Future<String> askAssistant(String query, {String? opponentId, String? stadiumId, String? gameDate, List<Map<String, dynamic>>? liveFatigue}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/ingame/assistant'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'query': query,
          'opponent_id': opponentId,
          'stadium_id': stadiumId,
          'game_date': gameDate,
          'live_fatigue': liveFatigue,
        }),
      );
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['advice'] ?? 'Nu am primit un sfat clar.';
      }
      return 'Eroare conexiune: ${response.statusCode}';
    } catch (e) {
      return 'Exceptie: $e';
    }
  }

  /// Fire-and-forget: starts the AI pipeline on the backend.
  /// Returns immediately with {"status": "processing"}.
  Future<Map<String, dynamic>> prepareMatch({
    required String opponentId,
    String? stadiumId,
    String? gameDate,
  }) async {
    try {
      final body = <String, dynamic>{
        'opponent_id': opponentId,
      };
      if (stadiumId != null) body['stadium_id'] = stadiumId;
      if (gameDate != null) body['game_date'] = gameDate;

      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/settings/prepare-match'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(body),
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        return json.decode(response.body) as Map<String, dynamic>;
      }
      return {'status': 'error', 'detail': 'HTTP ${response.statusCode}'};
    } catch (e) {
      return {'status': 'error', 'detail': '$e'};
    }
  }

  /// Polls the backend for the status of the AI pipeline.
  Future<Map<String, dynamic>> pollPrepareStatus() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/settings/prepare-match/status'),
      ).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        return json.decode(response.body) as Map<String, dynamic>;
      }
      return {'status': 'error'};
    } catch (e) {
      return {'status': 'error', 'detail': '$e'};
    }
  }
}
