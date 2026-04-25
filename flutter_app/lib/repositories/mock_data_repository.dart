import 'dart:convert';
import 'package:flutter/services.dart';
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
  Future<List<TacticalGap>> getPregameGaps() async {
    final data = await _loadJsonList('assets/mock_data/pregame_gaps.json');
    return data.map((json) => TacticalGap.fromJson(json)).toList();
  }

  @override
  Future<List<PlayerWeakness>> getPregameOpponentWeakness() async {
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
    final data = await _loadJsonList('assets/mock_data/ingame_players.json');
    return data.map((json) => LivePlayerFatigue.fromJson(json)).toList();
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
}
