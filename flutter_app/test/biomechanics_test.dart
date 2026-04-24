import 'package:flutter_test/flutter_test.dart';
import '../lib/utils/biomechanics.dart'; 

void main() {
  group('🛡️ SHIELD - Biomechanics Calculator Unit Tests', () {
    
    test('Returnează 0.0 grade deviație pentru o postură perfect aliniată (180°)', () {
      // Setup: Coordonate pe o singură axă verticală
      final hip = [0.0, 10.0];
      final knee = [0.0, 5.0];
      final ankle = [0.0, 0.0];
      
      // Act
      final deviation = BiomechanicsCalculator.calculateKneeValgus(hip, knee, ankle);
      
      // Assert
      expect(deviation, 0.0, reason: "Dacă articulațiile sunt pe aceeași axă X, unghiul este 180° (Deviație 0).");
    });

    test('Detectează deviația Valgus/Varus când piciorul colapsează medial/lateral', () {
      // Setup: Picior îndoit (triunghi isoscel pentru validare matematică ușoară)
      // Femur vector (2, 5), Tibia vector (-2, 5) => unghi ascuțit la nivelul genunchiului
      final hip = [2.0, 10.0];
      final knee = [4.0, 5.0];
      final ankle = [2.0, 0.0];
      
      // Act
      final deviation = BiomechanicsCalculator.calculateKneeValgus(hip, knee, ankle);
      
      // Assert: Trebuie să rezulte un unghi de deviație masivă. 
      // Dot product: (-2)*(-2) + (5)*(-5) = 4 - 25 = -21
      // Norm1 = sqrt(29), Norm2 = sqrt(29)
      // cos(theta) = -21 / 29 = -0.724 => unghiul interior e aprox 136.4 grade
      // Deviatia = 180 - 136.4 = ~43.6 grade
      expect(deviation, greaterThan(0.0));
      expect(deviation, closeTo(43.60, 0.1), reason: "Matematica dot product a deviat cu peste limitele impuse.");
    });
    
    test('Previne NaN / Erori la date invalide (zero distance)', () {
      // Act: Toate punctele sunt în coordonata [0,0]
      final deviation = BiomechanicsCalculator.calculateKneeValgus([0.0, 0.0], [0.0, 0.0], [0.0, 0.0]);
      
      // Assert
      expect(deviation, 0.0, reason: "Diviziunea cu 0 trebuie tratată și să returneze 0.0 în siguranță.");
    });
  });
}
