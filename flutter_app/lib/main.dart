import 'package:flutter/material.dart';
import 'screens/dashboard_screen.dart';

import 'package:get_it/get_it.dart';
import 'repositories/data_repository.dart';
import 'repositories/mock_data_repository.dart';
import 'services/settings_service.dart';

final getIt = GetIt.instance;

void setupLocator() {
  getIt.registerLazySingleton<DataRepository>(() => MockDataRepository());
  getIt.registerLazySingleton<SettingsService>(() => SettingsService());
}

void main() {
  setupLocator();
  runApp(const FormaOSApp());
}

class FormaOSApp extends StatelessWidget {
  const FormaOSApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FormaOS',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor:
            const Color(0xFF121212), // Fundal foarte închis (charcoal)
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF00FFCC), // Accent neon cyan
          secondary: Color(0xFFFF00FF), // Accent neon magenta
          surface: Color(0xFF1E1E1E),
        ),
        navigationRailTheme: const NavigationRailThemeData(
          backgroundColor: Color(0xFF181818),
          indicatorColor:
              Color(0x2200FFCC), // O umbră fină cyan în loc de pastila roz
          selectedIconTheme: IconThemeData(color: Color(0xFF00FFCC), size: 28),
          unselectedIconTheme: IconThemeData(color: Colors.white54, size: 24),
          selectedLabelTextStyle: TextStyle(
              color: Color(0xFF00FFCC),
              fontWeight: FontWeight.bold,
              letterSpacing: 1.1),
          unselectedLabelTextStyle: TextStyle(color: Colors.white54),
        ),
        textTheme: const TextTheme(
          displayLarge:
              TextStyle(color: Colors.white, fontWeight: FontWeight.w900),
          bodyLarge: TextStyle(color: Colors.white70),
        ),
        useMaterial3: true,
      ),
      home: const DashboardScreen(),
    );
  }
}
