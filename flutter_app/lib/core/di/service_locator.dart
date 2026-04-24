import 'package:get_it/get_it.dart';
import '../../services/firestore_service.dart';
import '../../services/api_client.dart';
import '../../services/websocket_service.dart';
import '../../services/biomechanics_worker.dart';
import '../../bloc/match_cubit.dart';

final sl = GetIt.instance;

void setupLocator() {
  sl.registerLazySingleton<FirestoreService>(() => FirestoreService());
  sl.registerLazySingleton<ApiClient>(() => ApiClient());
  sl.registerLazySingleton<WebSocketService>(() => WebSocketService());
  
  // Injectăm Worker-ul la inițializare pentru a fi gata de calcul I/O
  sl.registerLazySingleton<BiomechanicsWorker>(() {
    final worker = BiomechanicsWorker();
    worker.initWorker();
    return worker;
  });

  sl.registerFactory<MatchCubit>(() => MatchCubit(
    firestoreService: sl<FirestoreService>(),
    apiClient: sl<ApiClient>(),
    wsService: sl<WebSocketService>(),
    bioWorker: sl<BiomechanicsWorker>(),
  ));
}
