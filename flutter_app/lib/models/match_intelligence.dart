class WeatherContext {
  final double temperature;
  final String condition;
  final double windSpeed;

  WeatherContext({
    required this.temperature,
    required this.condition,
    required this.windSpeed,
  });

  factory WeatherContext.fromJson(Map<String, dynamic> json) {
    return WeatherContext(
      temperature: (json['temperature'] ?? 0).toDouble(),
      condition: json['condition'] ?? 'Unknown',
      windSpeed: (json['wind_speed'] ?? 0).toDouble(),
    );
  }
}

class PsychologyReport {
  final double moraleScore;
  final String pressureResistance;

  PsychologyReport({
    required this.moraleScore,
    required this.pressureResistance,
  });

  factory PsychologyReport.fromJson(Map<String, dynamic> json) {
    return PsychologyReport(
      moraleScore: (json['morale_score'] ?? 0).toDouble(),
      pressureResistance: json['pressure_resistance'] ?? 'Medium',
    );
  }
}

class VulnerabilityZone {
  final int id;
  final double x;
  final double y;
  final double radius;
  final double threatScore;

  VulnerabilityZone({
    required this.id,
    required this.x,
    required this.y,
    required this.radius,
    required this.threatScore,
  });

  factory VulnerabilityZone.fromJson(Map<String, dynamic> json) {
    return VulnerabilityZone(
      id: json['id'] ?? 0,
      x: (json['x'] ?? 0).toDouble(),
      y: (json['y'] ?? 0).toDouble(),
      radius: (json['radius'] ?? 0).toDouble(),
      threatScore: (json['threat_score'] ?? 0).toDouble(),
    );
  }
}

class PivotTarget {
  final String playerId;
  final double optimalX;
  final double optimalY;
  final String recommendation;

  PivotTarget({
    required this.playerId,
    required this.optimalX,
    required this.optimalY,
    required this.recommendation,
  });

  factory PivotTarget.fromJson(Map<String, dynamic> json) {
    return PivotTarget(
      playerId: json['player_id'] ?? '',
      optimalX: (json['optimal_x'] ?? 0).toDouble(),
      optimalY: (json['optimal_y'] ?? 0).toDouble(),
      recommendation: json['recommendation'] ?? '',
    );
  }
}

// Un container global care încapsulează întregul context al adversarului
class MatchIntelligenceData {
  final WeatherContext? weather;
  final PsychologyReport? psychology;
  final PivotTarget? pivotTarget;
  final List<VulnerabilityZone> vulnerabilityZones;

  MatchIntelligenceData({
    this.weather,
    this.psychology,
    this.pivotTarget,
    this.vulnerabilityZones = const [],
  });
}
