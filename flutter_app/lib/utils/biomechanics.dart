import 'dart:math';

class BiomechanicsCalculator {
  /// Calculează deviația genunchiului (Valgus/Varus) pe baza coordonatelor articulare 2D.
  /// Așteaptă vectorii [x,y] pentru șold (hip), genunchi (knee) și gleznă (ankle).
  /// Returnează unghiul de deviație absolut în grade. Un picior perfect drept = 0 grade deviație.
  static double calculateKneeValgus(List<double> hip, List<double> knee, List<double> ankle) {
    if (hip.length < 2 || knee.length < 2 || ankle.length < 2) return 0.0;
    
    // Algoritm Vectorial (Dot Product între segmentele femurului și tibiei)
    final double femurVectorX = hip[0] - knee[0];
    final double femurVectorY = hip[1] - knee[1];
    
    final double tibiaVectorX = ankle[0] - knee[0];
    final double tibiaVectorY = ankle[1] - knee[1];
    
    final double normFemur = sqrt(femurVectorX * femurVectorX + femurVectorY * femurVectorY);
    final double normTibia = sqrt(tibiaVectorX * tibiaVectorX + tibiaVectorY * tibiaVectorY);
    
    if (normFemur == 0 || normTibia == 0) return 0.0;
    
    final double dotProduct = femurVectorX * tibiaVectorX + femurVectorY * tibiaVectorY;
    final double cosTheta = dotProduct / (normFemur * normTibia);
    
    final double angleRad = acos(cosTheta.clamp(-1.0, 1.0));
    final double angleDeg = angleRad * (180.0 / pi);
    
    // Deviația este abaterea unghiului format față de o dreaptă absolută (180 grade)
    final double valgusDeviation = (180.0 - angleDeg).abs();
    
    return double.parse(valgusDeviation.toStringAsFixed(2));
  }
}
