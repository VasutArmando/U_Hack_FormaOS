import 'dart:convert';
import 'package:http/http.dart' as http;
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
    final data = await _fetchList('/api/v1/ingame/opponent-status');
    return data.map((json) => LivePlayerFatigue.fromJson(json)).toList();
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

  Future<String> askAssistant(String query) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/ingame/assistant'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'query': query}),
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
}
