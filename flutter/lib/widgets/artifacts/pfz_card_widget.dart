import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../../app/theme.dart';
import '../../utils/map_navigation.dart';

class PFZCardWidget extends StatelessWidget {
  final Map<String, dynamic> artifact;

  const PFZCardWidget({super.key, required this.artifact});

  @override
  Widget build(BuildContext context) {
    final title = artifact['title'] as String? ?? 'Potential Fishing Zone (PFZ)';
    final data = (artifact['data'] as Map<String, dynamic>?) ?? artifact;

    final lat = (data['latitude'] ?? data['lat'] ?? data['center']?['lat'] ?? 17.6868) as num;
    final lng = (data['longitude'] ?? data['lng'] ?? data['center']?['lng'] ?? 83.2185) as num;
    final centerPoint = LatLng(lat.toDouble(), lng.toDouble());

    final depth = data['depth_m'] ?? data['depth'] ?? '35-50';
    final sst = data['sst'] ?? data['sst_range'] ?? '28.5';
    final chl = data['chlorophyll'] ?? data['chlorophyll_a'] ?? '1.2';
    final status = data['status'] ?? data['validity'] ?? 'Active Forecast';
    final distance = data['distance_km'] ?? data['distance_nm'];

    // Collect zones / markers if list provided
    final rawZones = (data['zones'] as List?) ?? (data['pfz_points'] as List?) ?? [];
    final markers = <Marker>[];

    // Main location marker
    markers.add(
      Marker(
        point: centerPoint,
        width: 32,
        height: 32,
        child: Container(
          decoration: BoxDecoration(
            color: SamudraColors.accentCyan,
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white, width: 2),
            boxShadow: const [
              BoxShadow(color: Colors.black45, blurRadius: 4),
            ],
          ),
          child: const Icon(Icons.phishing, size: 18, color: SamudraColors.backgroundDark),
        ),
      ),
    );

    for (final z in rawZones) {
      if (z is Map<String, dynamic>) {
        final zLat = (z['lat'] ?? z['latitude']) as num?;
        final zLng = (z['lng'] ?? z['longitude']) as num?;
        if (zLat != null && zLng != null) {
          markers.add(
            Marker(
              point: LatLng(zLat.toDouble(), zLng.toDouble()),
              width: 24,
              height: 24,
              child: Container(
                decoration: const BoxDecoration(
                  color: SamudraColors.accentBlue,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.location_on, size: 14, color: Colors.white),
              ),
            ),
          );
        }
      }
    }

    return Container(
      margin: const EdgeInsets.only(top: 8, bottom: 4),
      decoration: BoxDecoration(
        color: SamudraColors.backgroundCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: SamudraColors.accentCyan.withValues(alpha: 0.35)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x22000000),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.phishing, size: 18, color: SamudraColors.accentCyan),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        title,
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                              color: SamudraColors.textPrimary,
                              fontWeight: FontWeight.w600,
                            ),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: SamudraColors.accentCyan.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        '$status',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: SamudraColors.accentCyan,
                              fontWeight: FontWeight.w600,
                              fontSize: 11,
                            ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _DetailChip(label: 'Depth', value: '$depth m'),
                    _DetailChip(label: 'SST', value: '$sst °C'),
                    _DetailChip(label: 'Chlorophyll', value: '$chl mg/m³'),
                    if (distance != null) _DetailChip(label: 'Distance', value: '$distance km'),
                  ],
                ),
              ],
            ),
          ),

          // Interactive Map Widget preview inside PFZ Card (Tap to open full dedicated map)
          GestureDetector(
            onTap: () => openMapArtifact(context, artifact),
            child: Stack(
              children: [
                SizedBox(
                  height: 160,
                  child: ClipRRect(
                    borderRadius: const BorderRadius.only(
                      bottomLeft: Radius.circular(14),
                      bottomRight: Radius.circular(14),
                    ),
                    child: IgnorePointer(
                      child: FlutterMap(
                        options: MapOptions(
                          initialCenter: centerPoint,
                          initialZoom: 10.5,
                          minZoom: 4,
                          maxZoom: 16,
                          backgroundColor: const Color(0xFF0A1628),
                        ),
                        children: [
                          TileLayer(
                            urlTemplate:
                                'https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
                            userAgentPackageName: 'com.example.samudra_ai',
                            errorTileCallback: (tile, error, stackTrace) {},
                          ),
                          MarkerLayer(markers: markers),
                        ],
                      ),
                    ),
                  ),
                ),

                Positioned(
                  bottom: 8,
                  right: 8,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: SamudraColors.backgroundDark.withValues(alpha: 0.85),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: SamudraColors.accentCyan.withValues(alpha: 0.6)),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          'View on Map',
                          style: TextStyle(
                            color: SamudraColors.accentCyan,
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        SizedBox(width: 4),
                        Icon(Icons.arrow_forward_ios, size: 10, color: SamudraColors.accentCyan),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _DetailChip extends StatelessWidget {
  final String label;
  final String value;

  const _DetailChip({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: SamudraColors.textMuted,
                fontSize: 10,
              ),
        ),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: SamudraColors.textPrimary,
                fontWeight: FontWeight.w700,
                fontSize: 12,
              ),
        ),
      ],
    );
  }
}
