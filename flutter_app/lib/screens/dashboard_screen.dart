import 'package:flutter/material.dart';
import 'oracle_screen.dart';
import 'xray_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _selectedIndex = 0;

  // Destinațiile (ecranele placeholder temporare)
  final List<Widget> _views = const [
    Center(
      child: Text('📊 Overview (Sumarul adversarului)', 
        style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white70)
      )
    ),
    const OracleScreen(),
    const XrayScreen(), // Înlocuit Placeholder-ul X-RAY
    Center(
      child: Text('🧠 TACTICIAN (Master Game Plan)', 
        style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white70)
      )
    ),
  ];

  @override
  Widget build(BuildContext context) {
    // Extindem automat NavigationRail pe rezoluții mari (Desktop/Tabletă Landscape)
    final bool isDesktop = MediaQuery.of(context).size.width >= 800;

    return Scaffold(
      body: Row(
        children: [
          // Meniul lateral standard pentru interfețe B2B/Dashboard
          NavigationRail(
            selectedIndex: _selectedIndex,
            onDestinationSelected: (int index) {
              setState(() {
                _selectedIndex = index;
              });
            },
            extended: isDesktop,
            minExtendedWidth: 220,
            leading: Padding(
              padding: const EdgeInsets.symmetric(vertical: 24.0),
              child: isDesktop 
                  ? Column(
                      children: const [
                        Icon(Icons.sports_soccer, size: 40, color: Color(0xFF00FFCC)),
                        SizedBox(height: 8),
                        Text('FORMA SCOUT', style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 2.0, fontSize: 16)),
                      ],
                    )
                  : const Icon(Icons.sports_soccer, size: 36, color: Color(0xFF00FFCC)),
            ),
            destinations: const [
              NavigationRailDestination(
                icon: Icon(Icons.dashboard_outlined),
                selectedIcon: Icon(Icons.dashboard),
                label: Text('Overview'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.hub_outlined),
                selectedIcon: Icon(Icons.hub),
                label: Text('ORACLE'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.radar_outlined),
                selectedIcon: Icon(Icons.radar),
                label: Text('X-RAY'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.psychology_outlined),
                selectedIcon: Icon(Icons.psychology),
                label: Text('TACTICIAN'),
              ),
            ],
          ),
          
          // Separator fin între meniu și corpul aplicației
          const VerticalDivider(thickness: 1, width: 1, color: Colors.white10),
          
          // Zona principală (Dinamică în funcție de selecție)
          Expanded(
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 300),
              child: _views[_selectedIndex],
            ),
          ),
        ],
      ),
    );
  }
}
