import '../models/match_data.dart';

abstract class DataRepository {
  Future<List<Team>> getTeams();
  Future<List<Stadium>> getStadiums();
  Future<List<TacticalGap>> getPregameGaps();
  Future<List<PlayerWeakness>> getPregameOpponentWeakness();
  Future<List<TacticalGap>> getIngameGaps();
  Future<List<LivePlayerFatigue>> getIngamePlayers();
  Future<List<TacticalGap>> getHalftimeGaps();
  Future<List<HalftimeChange>> getHalftimeChanges();
}
