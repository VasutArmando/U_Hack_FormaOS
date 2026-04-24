import 'package:cloud_firestore/cloud_firestore.dart';

class FirestoreService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  // Ascultă în timp real documentul meciului curent (MatchState)
  Stream<DocumentSnapshot> streamCurrentMatch() {
    return _db.collection('matches').doc('current_match').snapshots();
  }

  // Ascultă în timp real colecția de alerte sortate descrescător după timestamp
  Stream<QuerySnapshot> streamAlerts() {
    return _db.collection('alerts')
              .orderBy('timestamp', descending: true)
              .limit(50)
              .snapshots();
  }
  
  // Opțional: Ascultă jucătorii
  Stream<QuerySnapshot> streamPlayers() {
    return _db.collection('players').snapshots();
  }
}
