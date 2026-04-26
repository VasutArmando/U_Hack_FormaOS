import 'package:flutter/material.dart';
import '../main.dart';
import '../models/match_data.dart';
import '../repositories/api_data_repository.dart';
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
  MatchWeather? _previewWeather;
  bool _isLoadingWeather = false;

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
        if (_selectedTeamId != null &&
            !_teams.any((t) => t.id == _selectedTeamId)) _selectedTeamId = null;

        _selectedStadiumId = settings['stadiumId'];
        if (_selectedStadiumId != null &&
            !_stadiums.any((s) => s.id == _selectedStadiumId))
          _selectedStadiumId = null;

        if (settings['gameDate'] != null) {
          _selectedDate = DateTime.tryParse(settings['gameDate']!);
        }

        if (settings['matchTime'] != null) {
          final parts = settings['matchTime']!.split(':');
          if (parts.length == 2) {
            _selectedTime = TimeOfDay(
                hour: int.parse(parts[0]), minute: int.parse(parts[1]));
          }
        }
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Failed to load data: $e')));
      }
    }
  }

  bool _isPreparing = false;
  String? _prepareStatus;

  Future<void> _saveSettings() async {
    setState(() => _isSaving = true);

    String? dateStr = _selectedDate?.toIso8601String();
    String? timeStr;
    if (_selectedTime != null) {
      timeStr =
          '${_selectedTime!.hour.toString().padLeft(2, '0')}:${_selectedTime!.minute.toString().padLeft(2, '0')}';
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
        content: Text('Settings saved! Starting AI analysis...'),
        backgroundColor: Colors.green,
      ));
    }

    // Fetch weather preview for the chosen stadium + date
    if (_selectedStadiumId != null) {
      _fetchWeatherPreview();
    }

    // Trigger the AI analysis pipeline on the backend
    if (_selectedTeamId != null) {
      _triggerPrepareMatch();
    }
  }

  Future<void> _triggerPrepareMatch() async {
    setState(() {
      _isPreparing = true;
      _prepareStatus = null;
    });

    try {
      final apiRepo = getIt<DataRepository>() as ApiDataRepository?;
      if (apiRepo == null) return;

      // Build the full game date ISO string
      String? gameDate;
      if (_selectedDate != null) {
        final hour = _selectedTime?.hour ?? 20;
        final minute = _selectedTime?.minute ?? 45;
        final dt = DateTime(_selectedDate!.year, _selectedDate!.month,
            _selectedDate!.day, hour, minute);
        gameDate = dt.toIso8601String();
      }

      // Fire-and-forget: this returns instantly
      final startResult = await apiRepo.prepareMatch(
        opponentId: _selectedTeamId!,
        stadiumId: _selectedStadiumId,
        gameDate: gameDate,
      );

      if (startResult['status'] == 'error') {
        if (mounted) {
          setState(() {
            _prepareStatus =
                '⚠️ Failed to start: ${startResult['detail'] ?? 'unknown'}';
            _isPreparing = false;
          });
        }
        return;
      }

      // Poll for completion every 3 seconds
      while (mounted) {
        await Future.delayed(const Duration(seconds: 3));
        if (!mounted) break;

        final status = await apiRepo.pollPrepareStatus();
        final state = status['status'] ?? 'error';

        if (state == 'done') {
          if (mounted) {
            setState(() {
              _prepareStatus =
                  '✅ Analysis ready — ${status['player_count']} players analyzed';
              _isPreparing = false;
            });
          }
          return;
        } else if (state == 'error') {
          if (mounted) {
            setState(() {
              _prepareStatus =
                  '⚠️ Analysis error: ${status['error'] ?? 'unknown'}';
              _isPreparing = false;
            });
          }
          return;
        }
        // state == 'processing' — keep polling
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _prepareStatus = '⚠️ Error: $e';
          _isPreparing = false;
        });
      }
    }
  }

  Future<void> _fetchWeatherPreview() async {
    setState(() => _isLoadingWeather = true);
    try {
      final apiRepo = getIt<DataRepository>() as ApiDataRepository?;
      if (apiRepo == null) return;

      String? gameDate;
      if (_selectedDate != null) {
        final hour = _selectedTime?.hour ?? 20;
        final minute = _selectedTime?.minute ?? 45;
        final dt = DateTime(_selectedDate!.year, _selectedDate!.month,
            _selectedDate!.day, hour, minute);
        gameDate = dt.toIso8601String();
      }

      final weather = await apiRepo.getMatchWeather(
        stadiumId: _selectedStadiumId!,
        gameDate: gameDate,
      );
      if (mounted) setState(() => _previewWeather = weather);
    } catch (e) {
      // silently fail
    } finally {
      if (mounted) setState(() => _isLoadingWeather = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(
          child: CircularProgressIndicator(color: Color(0xFF00FFCC)));
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
          const Text(
              'Configure the upcoming match details. Settings are saved locally on your device.',
              style: TextStyle(color: Colors.white54)),
          const SizedBox(height: 32),
          Card(
            color: const Color(0xFF1E1E1E),
            elevation: 4,
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Next Opponent Team',
                      style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.white)),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    initialValue: _selectedTeamId,
                    decoration: const InputDecoration(
                      filled: true,
                      fillColor: Colors.white10,
                      border: OutlineInputBorder(),
                    ),
                    dropdownColor: const Color(0xFF2C2C2C),
                    items: _teams
                        .map((t) => DropdownMenuItem(
                            value: t.id,
                            child: Text(t.name,
                                style: const TextStyle(color: Colors.white))))
                        .toList(),
                    onChanged: (val) => setState(() => _selectedTeamId = val),
                  ),
                  const SizedBox(height: 24),

                  const Text('Game Date',
                      style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.white)),
                  const SizedBox(height: 8),
                  InkWell(
                    onTap: () async {
                      final date = await showDatePicker(
                        context: context,
                        initialDate: _selectedDate ?? DateTime.now(),
                        firstDate:
                            DateTime.now().subtract(const Duration(days: 365)),
                        lastDate: DateTime.now().add(const Duration(days: 365)),
                      );
                      if (date != null) setState(() => _selectedDate = date);
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 16),
                      decoration: BoxDecoration(
                        color: Colors.white10,
                        border: Border.all(color: Colors.white30),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                              _selectedDate != null
                                  ? DateFormat('yyyy-MM-dd')
                                      .format(_selectedDate!)
                                  : 'Select Date',
                              style: const TextStyle(color: Colors.white)),
                          const Icon(Icons.calendar_today,
                              color: Colors.white54),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  const Text('Match Time',
                      style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.white)),
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
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 16),
                      decoration: BoxDecoration(
                        color: Colors.white10,
                        border: Border.all(color: Colors.white30),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                              _selectedTime != null
                                  ? _selectedTime!.format(context)
                                  : 'Select Time',
                              style: const TextStyle(color: Colors.white)),
                          const Icon(Icons.access_time, color: Colors.white54),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  const Text('Stadium',
                      style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.white)),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    initialValue: _selectedStadiumId,
                    decoration: const InputDecoration(
                      filled: true,
                      fillColor: Colors.white10,
                      border: OutlineInputBorder(),
                    ),
                    dropdownColor: const Color(0xFF2C2C2C),
                    items: _stadiums
                        .map((s) => DropdownMenuItem(
                            value: s.id,
                            child: Text(s.name,
                                style: const TextStyle(color: Colors.white))))
                        .toList(),
                    onChanged: (val) =>
                        setState(() => _selectedStadiumId = val),
                  ),
                  const SizedBox(height: 32),

                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton(
                      onPressed:
                          (_isSaving || _isPreparing) ? null : _saveSettings,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF00FFCC),
                        foregroundColor: Colors.black,
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8)),
                      ),
                      child: _isSaving
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                  color: Colors.black, strokeWidth: 2))
                          : const Text('SAVE SETTINGS',
                              style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                  letterSpacing: 1.2)),
                    ),
                  ),

                  // AI Preparation Status
                  if (_isPreparing)
                    Container(
                      margin: const EdgeInsets.only(top: 16),
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: const Color(0xFF00FFCC).withOpacity(0.08),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                            color: const Color(0xFF00FFCC).withOpacity(0.3)),
                      ),
                      child: const Row(
                        children: [
                          SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                  color: Color(0xFF00FFCC), strokeWidth: 2)),
                          SizedBox(width: 12),
                          Expanded(
                              child: Text(
                            'Omniscient AI is analyzing the opponent squad...\nThis may take 1-2 minutes.',
                            style: TextStyle(
                                color: Color(0xFF00FFCC), fontSize: 13),
                          )),
                        ],
                      ),
                    )
                  else if (_prepareStatus != null)
                    Container(
                      margin: const EdgeInsets.only(top: 16),
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: _prepareStatus!.startsWith('✅')
                            ? Colors.green.withOpacity(0.1)
                            : Colors.orange.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: _prepareStatus!.startsWith('✅')
                              ? Colors.green.withOpacity(0.4)
                              : Colors.orange.withOpacity(0.4),
                        ),
                      ),
                      child: Text(_prepareStatus!,
                          style: const TextStyle(
                              color: Colors.white, fontSize: 13)),
                    ),

                  // Weather Preview
                  if (_isLoadingWeather)
                    const Padding(
                      padding: EdgeInsets.only(top: 24),
                      child: Center(
                          child: CircularProgressIndicator(
                              color: Color(0xFF00FFCC), strokeWidth: 2)),
                    )
                  else if (_previewWeather != null)
                    _buildWeatherPreview(_previewWeather!),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWeatherPreview(MatchWeather w) {
    final isRain = w.condition.toLowerCase().contains('rain');
    final isSnow = w.condition.toLowerCase().contains('snow');
    final gradientColors = isSnow
        ? [const Color(0xFF1565C0), const Color(0xFF0D47A1)]
        : isRain
            ? [const Color(0xFF283593), const Color(0xFF1A237E)]
            : [const Color(0xFF2E7D32), const Color(0xFF1B5E20)];
    return Container(
      margin: const EdgeInsets.only(top: 24),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
            colors: gradientColors,
            begin: Alignment.topLeft,
            end: Alignment.bottomRight),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(w.conditionIcon, style: const TextStyle(fontSize: 36)),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                        '${w.temperature.toStringAsFixed(1)}°C — ${w.condition}',
                        style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 18)),
                    if (w.forecastNote.isNotEmpty)
                      Text(w.forecastNote,
                          style: const TextStyle(
                              color: Colors.white60, fontSize: 12)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _weatherStat(
                  '💨', '${w.windSpeed.toStringAsFixed(0)} m/s', 'Vânt'),
              _weatherStat('💧', '${w.humidity}%', 'Umiditate'),
              _weatherStat('🌡️', '${w.temperature.toStringAsFixed(0)}°C',
                  'Temperatură'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _weatherStat(String emoji, String value, String label) {
    return Column(
      children: [
        Text(emoji, style: const TextStyle(fontSize: 20)),
        const SizedBox(height: 4),
        Text(value,
            style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 16)),
        Text(label,
            style: const TextStyle(color: Colors.white54, fontSize: 11)),
      ],
    );
  }
}
