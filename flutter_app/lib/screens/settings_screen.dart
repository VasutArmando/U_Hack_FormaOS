import 'package:flutter/material.dart';
import '../main.dart';
import '../models/match_data.dart';
import '../repositories/data_repository.dart';
import '../services/settings_service.dart';
import 'package:intl/intl.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _settingsService = getIt<SettingsService>();
  final _dataRepository = getIt<DataRepository>();

  List<Team> _teams = [];
  List<Stadium> _stadiums = [];

  String? _selectedTeamId;
  String? _selectedStadiumId;
  DateTime? _selectedDate;
  TimeOfDay? _selectedTime;

  bool _isLoading = true;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _loadDataAndSettings();
  }

  Future<void> _loadDataAndSettings() async {
    try {
      final teams = await _dataRepository.getTeams();
      final stadiums = await _dataRepository.getStadiums();
      final settings = await _settingsService.loadSettings();

      setState(() {
        _teams = teams;
        _stadiums = stadiums;
        
        _selectedTeamId = settings['nextOpponentId'];
        if (_selectedTeamId != null && !_teams.any((t) => t.id == _selectedTeamId)) _selectedTeamId = null;

        _selectedStadiumId = settings['stadiumId'];
        if (_selectedStadiumId != null && !_stadiums.any((s) => s.id == _selectedStadiumId)) _selectedStadiumId = null;

        if (settings['gameDate'] != null) {
          _selectedDate = DateTime.tryParse(settings['gameDate']!);
        }
        
        if (settings['matchTime'] != null) {
          final parts = settings['matchTime']!.split(':');
          if (parts.length == 2) {
            _selectedTime = TimeOfDay(hour: int.parse(parts[0]), minute: int.parse(parts[1]));
          }
        }
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to load data: $e')));
      }
    }
  }

  Future<void> _saveSettings() async {
    setState(() => _isSaving = true);
    
    String? dateStr = _selectedDate?.toIso8601String();
    String? timeStr;
    if (_selectedTime != null) {
      timeStr = '${_selectedTime!.hour.toString().padLeft(2, '0')}:${_selectedTime!.minute.toString().padLeft(2, '0')}';
    }

    await _settingsService.saveSettings(
      nextOpponentId: _selectedTeamId,
      gameDate: dateStr,
      matchTime: timeStr,
      stadiumId: _selectedStadiumId,
    );

    setState(() => _isSaving = false);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Settings saved successfully!'),
        backgroundColor: Colors.green,
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF00FFCC)));
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(32.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'MATCH SETTINGS',
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.w900,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 8),
          const Text('Configure the upcoming match details. Settings are saved locally on your device.', style: TextStyle(color: Colors.white54)),
          const SizedBox(height: 32),
          
          Card(
            color: const Color(0xFF1E1E1E),
            elevation: 4,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Next Opponent Team', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    initialValue: _selectedTeamId,
                    decoration: const InputDecoration(
                      filled: true,
                      fillColor: Colors.white10,
                      border: OutlineInputBorder(),
                    ),
                    dropdownColor: const Color(0xFF2C2C2C),
                    items: _teams.map((t) => DropdownMenuItem(value: t.id, child: Text(t.name, style: const TextStyle(color: Colors.white)))).toList(),
                    onChanged: (val) => setState(() => _selectedTeamId = val),
                  ),
                  const SizedBox(height: 24),

                  const Text('Game Date', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                  const SizedBox(height: 8),
                  InkWell(
                    onTap: () async {
                      final date = await showDatePicker(
                        context: context,
                        initialDate: _selectedDate ?? DateTime.now(),
                        firstDate: DateTime.now().subtract(const Duration(days: 365)),
                        lastDate: DateTime.now().add(const Duration(days: 365)),
                      );
                      if (date != null) setState(() => _selectedDate = date);
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                      decoration: BoxDecoration(
                        color: Colors.white10,
                        border: Border.all(color: Colors.white30),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(_selectedDate != null ? DateFormat('yyyy-MM-dd').format(_selectedDate!) : 'Select Date', style: const TextStyle(color: Colors.white)),
                          const Icon(Icons.calendar_today, color: Colors.white54),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  const Text('Match Time', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                  const SizedBox(height: 8),
                  InkWell(
                    onTap: () async {
                      final time = await showTimePicker(
                        context: context,
                        initialTime: _selectedTime ?? TimeOfDay.now(),
                      );
                      if (time != null) setState(() => _selectedTime = time);
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                      decoration: BoxDecoration(
                        color: Colors.white10,
                        border: Border.all(color: Colors.white30),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(_selectedTime != null ? _selectedTime!.format(context) : 'Select Time', style: const TextStyle(color: Colors.white)),
                          const Icon(Icons.access_time, color: Colors.white54),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  const Text('Stadium', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    initialValue: _selectedStadiumId,
                    decoration: const InputDecoration(
                      filled: true,
                      fillColor: Colors.white10,
                      border: OutlineInputBorder(),
                    ),
                    dropdownColor: const Color(0xFF2C2C2C),
                    items: _stadiums.map((s) => DropdownMenuItem(value: s.id, child: Text(s.name, style: const TextStyle(color: Colors.white)))).toList(),
                    onChanged: (val) => setState(() => _selectedStadiumId = val),
                  ),
                  const SizedBox(height: 32),

                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton(
                      onPressed: _isSaving ? null : _saveSettings,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF00FFCC),
                        foregroundColor: Colors.black,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      child: _isSaving 
                        ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2))
                        : const Text('SAVE SETTINGS', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, letterSpacing: 1.2)),
                    ),
                  ),
                ],
              ),
            ),
          )
        ],
      ),
    );
  }
}
