import 'package:flutter/material.dart';
import 'screens/dashboard_screen.dart';

void main() {
  runApp(const FormaScoutApp());
}

class FormaScoutApp extends StatelessWidget {
  const FormaScoutApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FORMA SCOUT',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF121212), // Fundal foarte închis (charcoal)
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF00FFCC), // Accent neon cyan
          secondary: Color(0xFFFF00FF), // Accent neon magenta
          surface: Color(0xFF1E1E1E), // Gri închis pentru carduri
          background: Color(0xFF121212),
        ),
        navigationRailTheme: const NavigationRailThemeData(
          backgroundColor: Color(0xFF181818),
          indicatorColor: Color(0x2200FFCC), // O umbră fină cyan în loc de pastila roz
          selectedIconTheme: IconThemeData(color: Color(0xFF00FFCC), size: 28),
          unselectedIconTheme: IconThemeData(color: Colors.white54, size: 24),
          selectedLabelTextStyle: TextStyle(color: Color(0xFF00FFCC), fontWeight: FontWeight.bold, letterSpacing: 1.1),
          unselectedLabelTextStyle: TextStyle(color: Colors.white54),
        ),
        textTheme: const TextTheme(
          displayLarge: TextStyle(color: Colors.white, fontWeight: FontWeight.w900),
          bodyLarge: TextStyle(color: Colors.white70),
        ),
        useMaterial3: true,
      ),
      home: const DashboardScreen(),
    );
  }
}
