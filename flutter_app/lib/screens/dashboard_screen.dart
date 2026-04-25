import 'package:flutter/material.dart';
import 'pregame_screen.dart';
import 'ingame_screen.dart';
import 'halftime_screen.dart';
import 'settings_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _selectedIndex = 0;

  Widget _buildSelectedScreen() {
    switch (_selectedIndex) {
      case 0: return const PregameScreen();
      case 1: return const InGameScreen();
      case 2: return const HalftimeScreen();
      case 3: return const SettingsScreen();
      default: return const PregameScreen();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          // Sidebar de navigare (NavigationRail)
          NavigationRail(
            selectedIndex: _selectedIndex,
            onDestinationSelected: (int index) {
              setState(() {
                _selectedIndex = index;
              });
            },
            labelType: NavigationRailLabelType.all,
            backgroundColor: Theme.of(context).navigationRailTheme.backgroundColor,
            selectedIconTheme: Theme.of(context).navigationRailTheme.selectedIconTheme,
            unselectedIconTheme: Theme.of(context).navigationRailTheme.unselectedIconTheme,
            selectedLabelTextStyle: Theme.of(context).navigationRailTheme.selectedLabelTextStyle,
            unselectedLabelTextStyle: Theme.of(context).navigationRailTheme.unselectedLabelTextStyle,
            leading: Padding(
              padding: const EdgeInsets.only(bottom: 24.0, top: 16.0),
              child: Column(
                children: [
                  const Icon(Icons.sports_soccer, size: 40, color: Color(0xFF00FFCC)),
                  const SizedBox(height: 8),
                  const Text('FormaOS', style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1.5, fontSize: 14, color: Colors.white)),
                ],
              ),
            ),
            destinations: const [
              NavigationRailDestination(
                icon: Icon(Icons.schedule),
                selectedIcon: Icon(Icons.schedule, color: Color(0xFF00FFCC)),
                label: Text('Pregame'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.play_circle_outline),
                selectedIcon: Icon(Icons.play_circle_filled, color: Color(0xFF00FFCC)),
                label: Text('InGame'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.pause_circle_outline),
                selectedIcon: Icon(Icons.pause_circle_filled, color: Color(0xFF00FFCC)),
                label: Text('HalfTime'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.settings),
                selectedIcon: Icon(Icons.settings, color: Color(0xFF00FFCC)),
                label: Text('Settings'),
              ),
            ],
          ),
          const VerticalDivider(thickness: 1, width: 1, color: Colors.white10),
          // Conținutul principal (partea dreaptă)
          Expanded(
            child: _buildSelectedScreen(),
          ),
        ],
      ),
    );
  }
}
