class Team {
  final String id;
  final String name;

  Team({required this.id, required this.name});

  factory Team.fromJson(Map<String, dynamic> json) {
    return Team(
      id: json['id'],
      name: json['name'],
    );
  }
}

class Stadium {
  final String id;
  final String name;

  Stadium({required this.id, required this.name});

  factory Stadium.fromJson(Map<String, dynamic> json) {
    return Stadium(
      id: json['id'],
      name: json['name'],
    );
  }
}

class TacticalGap {
  final String id;
  final String location;
  final String description;
  final String severity;
  final double x;
  final double y;
  final double w;
  final double h;

  TacticalGap({
    required this.id,
    required this.location,
    required this.description,
    required this.severity,
    required this.x,
    required this.y,
    required this.w,
    required this.h,
  });

  factory TacticalGap.fromJson(Map<String, dynamic> json) {
    final coords = json['coordinates'];
    return TacticalGap(
      id: json['id'],
      location: json['location'],
      description: json['description'],
      severity: json['severity'],
      x: coords['x'].toDouble(),
      y: coords['y'].toDouble(),
      w: coords['w'].toDouble(),
      h: coords['h'].toDouble(),
    );
  }
}

class PlayerWeakness {
  final String id;
  final String name;
  final String physicalState;
  final String psychologicalState;
  final String tacticalTendencies;
  final double overallWeaknessScore;

  PlayerWeakness({
    required this.id,
    required this.name,
    required this.physicalState,
    required this.psychologicalState,
    required this.tacticalTendencies,
    required this.overallWeaknessScore,
  });

  factory PlayerWeakness.fromJson(Map<String, dynamic> json) {
    return PlayerWeakness(
      id: (json['id'] ?? json['player_id'] ?? '').toString(),
      name: json['name'] ?? 'Unknown',
      physicalState: json['physical_state'] ?? '',
      psychologicalState: json['psychological_state'] ?? '',
      tacticalTendencies: json['tactical_tendencies'] ?? '',
      overallWeaknessScore: (json['overall_weakness_score'] ?? json['weakness_score'] ?? 0).toDouble(),
    );
  }
}

class LivePlayerFatigue {
  final String id;
  final String name;
  final double fatigue;
  final String liveRemark;

  LivePlayerFatigue({
    required this.id,
    required this.name,
    required this.fatigue,
    required this.liveRemark,
  });

  factory LivePlayerFatigue.fromJson(Map<String, dynamic> json) {
    return LivePlayerFatigue(
      id: (json['id'] ?? '').toString(),
      name: json['name'] ?? 'Unknown',
      fatigue: (json['fatigue'] ?? 0).toDouble(),
      liveRemark: json['live_remark'] ?? '',
    );
  }
}

class HalftimeChange {
  final String id;
  final String title;
  final String description;
  final double likelihood;
  final String category;

  HalftimeChange({
    required this.id,
    required this.title,
    required this.description,
    required this.likelihood,
    required this.category,
  });

  factory HalftimeChange.fromJson(Map<String, dynamic> json) {
    return HalftimeChange(
      id: (json['id'] ?? '').toString(),
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      likelihood: (json['likelihood'] ?? 0).toDouble(),
      category: json['category'] ?? '',
    );
  }
}
