import '../models/match_data.dart';

abstract class DataRepository {
  Future<List<Team>> getTeams();
  Future<List<Stadium>> getStadiums();
  Future<List<TacticalGap>> getPregameGaps({String? opponentId});
  Future<List<PlayerWeakness>> getPregameOpponentWeakness({String? opponentId, String? stadiumId, String? gameDate});
  Future<List<TacticalGap>> getIngameGaps();
  Future<List<LivePlayerFatigue>> getIngamePlayers();
  Future<List<TacticalGap>> getHalftimeGaps();
  Future<List<HalftimeChange>> getHalftimeChanges();
}
