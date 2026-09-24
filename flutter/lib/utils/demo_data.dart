import '../models/marine_data.dart';

// ─────────────────────────────────────────────────────────────────────────────
// DemoData — clearly-labelled DEMO records for development testing.
//
// These are NOT real oceanographic measurements.
// Source is tagged 'demo' so they can be filtered/deleted cleanly.
// Remove or guard behind a debug flag before production release.
// ─────────────────────────────────────────────────────────────────────────────

class DemoData {
  DemoData._();

  static List<MarineData> sampleRecords() {
    final now = DateTime.now().toUtc();
    final expires = now.add(const Duration(hours: 24));

    return [
      MarineData(
        dataType: 'sea_surface_temp',
        title: 'Sea Surface Temperature',
        description: '[DEMO DATA] Approximate SST near Kerala coast. '
            'Not a real measurement.',
        latitude: 10.85,
        longitude: 76.27,
        value: '28.4',
        unit: '°C',
        source: 'demo',
        timestamp: now,
        expiresAt: expires,
        createdAt: now,
        updatedAt: now,
      ),
      MarineData(
        dataType: 'chlorophyll',
        title: 'Chlorophyll-a Concentration',
        description: '[DEMO DATA] Approximate Chl-a near Lakshadweep. '
            'Not a real measurement.',
        latitude: 11.50,
        longitude: 72.80,
        value: '0.32',
        unit: 'mg/m³',
        source: 'demo',
        timestamp: now,
        expiresAt: expires,
        createdAt: now,
        updatedAt: now,
      ),
      MarineData(
        dataType: 'wave_height',
        title: 'Significant Wave Height',
        description: '[DEMO DATA] Approximate wave height off Kanyakumari. '
            'Not a real measurement.',
        latitude: 8.08,
        longitude: 77.55,
        value: '1.2',
        unit: 'm',
        source: 'demo',
        timestamp: now,
        expiresAt: expires,
        createdAt: now,
        updatedAt: now,
      ),
      MarineData(
        dataType: 'wind_speed',
        title: 'Surface Wind Speed',
        description: '[DEMO DATA] Approximate wind speed near Calicut. '
            'Not a real measurement.',
        latitude: 11.25,
        longitude: 75.78,
        value: '12.5',
        unit: 'kn',
        source: 'demo',
        timestamp: now,
        expiresAt: expires,
        createdAt: now,
        updatedAt: now,
      ),
      MarineData(
        dataType: 'salinity',
        title: 'Sea Water Salinity',
        description: '[DEMO DATA] Approximate salinity near Mangalore. '
            'Not a real measurement.',
        latitude: 12.87,
        longitude: 74.88,
        value: '35.2',
        unit: 'PSU',
        source: 'demo',
        timestamp: now,
        expiresAt: expires,
        createdAt: now,
        updatedAt: now,
      ),
    ];
  }
}
