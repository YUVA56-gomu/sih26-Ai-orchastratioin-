import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../../app/theme.dart';
import '../../utils/map_navigation.dart';

class RouteMapWidget extends StatelessWidget {
  final Map<String, dynamic> artifact;

  const RouteMapWidget({super.key, required this.artifact});

  @override
  Widget build(BuildContext context) {
    final title = artifact['title'] as String? ?? 'Navigation Route';
    final data = (artifact['data'] as Map<String, dynamic>?) ?? artifact;

    final originLat = (data['origin']?['lat'] ?? data['origin_latitude'] ?? data['start_lat'] ?? 17.6868) as num;
    final originLng = (data['origin']?['lng'] ?? data['origin_longitude'] ?? data['start_lng'] ?? 83.2185) as num;
    final destLat = (data['destination']?['lat'] ?? data['destination_latitude'] ?? data['end_lat'] ?? 17.8500) as num;
    final destLng = (data['destination']?['lng'] ?? data['destination_longitude'] ?? data['end_lng'] ?? 83.4500) as num;

    final origin = LatLng(originLat.toDouble(), originLng.toDouble());
    final destination = LatLng(destLat.toDouble(), destLng.toDouble());

    final distanceKm = data['distance_km'] ?? data['distance_nm'] ?? '24.5';
    final durationHrs = data['estimated_time'] ?? data['duration_hours'] ?? '1.5';
    final safetyScore = data['safety_score'] ?? '92';

    // Parse route polyline waypoints if present
    final rawWaypoints = (data['waypoints'] as List?) ?? (data['path'] as List?) ?? [];
    final routePoints = <LatLng>[origin];

    for (final wp in rawWaypoints) {
      if (wp is Map<String, dynamic>) {
        final wLat = (wp['lat'] ?? wp['latitude']) as num?;
        final wLng = (wp['lng'] ?? wp['longitude']) as num?;
        if (wLat != null && wLng != null) {
          routePoints.add(LatLng(wLat.toDouble(), wLng.toDouble()));
        }
      }
    }
    routePoints.add(destination);

    // Calculate map bounds center
    final centerLat = (origin.latitude + destination.latitude) / 2;
    final centerLng = (origin.longitude + destination.longitude) / 2;
    final center = LatLng(centerLat, centerLng);

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
                    const Icon(Icons.navigation_outlined, size: 18, color: SamudraColors.accentCyan),
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
                        color: SamudraColors.statusSafe.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        'Safety $safetyScore%',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: SamudraColors.statusSafe,
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
                    _DetailColumn(label: 'Distance', value: '$distanceKm km'),
                    _DetailColumn(label: 'Est. Time', value: '$durationHrs hrs'),
                    _DetailColumn(label: 'Waypoints', value: '${routePoints.length}'),
                  ],
                ),
              ],
            ),
          ),

          // Interactive Map Widget preview with Route Polyline & Markers (Tap to open full dedicated map)
          GestureDetector(
            onTap: () => openMapArtifact(context, artifact),
            child: Stack(
              children: [
                SizedBox(
                  height: 170,
                  child: ClipRRect(
                    borderRadius: const BorderRadius.only(
                      bottomLeft: Radius.circular(14),
                      bottomRight: Radius.circular(14),
                    ),
                    child: IgnorePointer(
                      child: FlutterMap(
                        options: MapOptions(
                          initialCenter: center,
                          initialZoom: 9.5,
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
                          PolylineLayer(
                            polylines: [
                              Polyline(
                                points: routePoints,
                                color: SamudraColors.accentCyan,
                                strokeWidth: 3.5,
                              ),
                            ],
                          ),
                          MarkerLayer(
                            markers: [
                              Marker(
                                point: origin,
                                width: 24,
                                height: 24,
                                child: Container(
                                  decoration: const BoxDecoration(
                                    color: SamudraColors.statusSafe,
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(Icons.my_location, size: 14, color: Colors.white),
                                ),
                              ),
                              Marker(
                                point: destination,
                                width: 24,
                                height: 24,
                                child: Container(
                                  decoration: const BoxDecoration(
                                    color: SamudraColors.statusDanger,
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(Icons.flag, size: 14, color: Colors.white),
                                ),
                              ),
                            ],
                          ),
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

class _DetailColumn extends StatelessWidget {
  final String label;
  final String value;

  const _DetailColumn({required this.label, required this.value});

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
