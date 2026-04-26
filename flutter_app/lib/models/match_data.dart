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
  final String? exploitRecommendation;
  final double overallWeaknessScore;
  final String climateDanger;   // "High", "Medium", "Low", "None"
  final String birthCountry;

  PlayerWeakness({
    required this.id,
    required this.name,
    required this.physicalState,
    required this.psychologicalState,
    required this.tacticalTendencies,
    this.exploitRecommendation,
    required this.overallWeaknessScore,
    this.climateDanger = 'None',
    this.birthCountry = '',
  });

  factory PlayerWeakness.fromJson(Map<String, dynamic> json) {
    return PlayerWeakness(
      id: (json['id'] ?? json['player_id'] ?? '').toString(),
      name: json['name'] ?? 'Unknown',
      physicalState: json['physical_state'] ?? '',
      psychologicalState: json['psychological_state'] ?? '',
      tacticalTendencies: json['tactical_tendencies'] ?? '',
      exploitRecommendation: json['exploit_recommendation'],
      overallWeaknessScore: (json['overall_weakness_score'] ?? json['weakness_score'] ?? 0).toDouble(),
      climateDanger: json['climate_danger'] ?? 'None',
      birthCountry: json['birth_country'] ?? '',
    );
  }
}

class MatchWeather {
  final double temperature;
  final String condition;
  final int humidity;
  final double windSpeed;
  final String forecastNote;

  MatchWeather({
    required this.temperature,
    required this.condition,
    required this.humidity,
    required this.windSpeed,
    this.forecastNote = '',
  });

  factory MatchWeather.fromJson(Map<String, dynamic> json) {
    return MatchWeather(
      temperature: (json['temperature'] ?? 15.0).toDouble(),
      condition: json['condition'] ?? 'Clear',
      humidity: (json['humidity'] ?? 50).toInt(),
      windSpeed: (json['wind_speed'] ?? 0.0).toDouble(),
      forecastNote: json['forecast_note'] ?? '',
    );
  }

  String get conditionIcon {
    final c = condition.toLowerCase();
    if (c.contains('rain') || c.contains('drizzle')) return '🌧️';
    if (c.contains('snow')) return '❄️';
    if (c.contains('thunder') || c.contains('storm')) return '⛈️';
    if (c.contains('cloud')) return '☁️';
    if (c.contains('fog') || c.contains('mist')) return '🌫️';
    return '☀️';
  }
}

class LivePlayerFatigue {
  final String id;
  final String name;
  final double fatigue;
  final String liveRemark;
  final double weight; // in kg
  final String position;
  final bool isStartingXI;

  LivePlayerFatigue({
    required this.id,
    required this.name,
    required this.fatigue,
    required this.liveRemark,
    this.weight = 75.0,
    this.position = 'Unknown',
    this.isStartingXI = false,
  });

  factory LivePlayerFatigue.fromJson(Map<String, dynamic> json) {
    return LivePlayerFatigue(
      id: (json['id'] ?? '').toString(),
      name: json['name'] ?? 'Unknown',
      fatigue: (json['fatigue'] ?? 0).toDouble(),
      liveRemark: json['live_remark'] ?? '',
      weight: (json['weight'] ?? 75.0).toDouble(),
      position: json['position'] ?? 'Unknown',
      isStartingXI: json['isStartingXI'] ?? false,
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
