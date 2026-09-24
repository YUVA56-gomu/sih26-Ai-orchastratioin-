import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

import '../../app/theme.dart';
import '../../data/map/demo_pfz_zones.dart';
import '../../models/location_data.dart';
import '../../models/map/ocean_layer.dart';
import '../../services/location_service.dart';
import '../../services/map/copernicus_wmts.dart';
import '../../services/map/ocean_layer_registry.dart';
import '../../utils/demo_imbl.dart';
import '../../widgets/voice_input_button.dart';

// ─────────────────────────────────────────────────────────────────────────────
// MarineMapScreen — interactive marine chart.
//
// Ported from the Project ORCA web frontend (`1-front-endmaps`):
//   • base raster basemap (Carto dark)
//   • Copernicus Marine WMTS ocean layers (SST / wave / SLA / chlorophyll)
//   • PFZ (fishing-zone) DEMO polygons
//   • IMBL boundary overlay (reuses the existing ImblBoundaryService data)
//   • current-location marker + recentre, backed by the existing LocationService
//
// The screen stays the app's own design: dark marine theme, search bar, filter
// chips, bottom navigation. `embedded` suppresses the AppBar in the nav stack.
//
// All data is behind the models/services in `lib/services/map/` — a future
// backend can replace DEMO values without rewriting this UI.
// ─────────────────────────────────────────────────────────────────────────────

class MarineMapScreen extends StatefulWidget {
  final bool embedded;
  final void Function(String query)? onVoiceQuery;
  final Map<String, dynamic>? initialArtifact;

  const MarineMapScreen({
    super.key,
    this.embedded = false,
    this.onVoiceQuery,
    this.initialArtifact,
  });

  @override
  State<MarineMapScreen> createState() => _MarineMapScreenState();
}

class _MarineMapScreenState extends State<MarineMapScreen> {
  static const String _userAgent = 'com.example.samudra_ai';

  final MapController _mapController = MapController();
  final OceanLayerRegistry _registry = OceanLayerRegistry();

  StreamSubscription<LocationData>? _locationSub;
  LocationData? _currentLocation;
  bool _locating = false;
  String? _gpsMessage;

  Map<String, dynamic>? _activeArtifact;
  List<Marker> _artifactMarkers = [];
  List<Polyline> _artifactPolylines = [];

  // Camera state (kept in-sync via onPositionChanged so controls work even if
  // the MapController's camera accessor changes across flutter_map versions).
  LatLng _center = LatLng(DemoPfzZones.defaultCamera.lat,
      DemoPfzZones.defaultCamera.lng);
  double _zoom = DemoPfzZones.defaultCamera.zoom;

  // Layer visibility state (mutated in place; the reference stays final).
  final Set<String> _visibleOceanLayerIds = <String>{'copernicus-sst'};
  bool _showFishingZones = true;
  bool _showImbl = false;

  /// True while the search-bar microphone is actively listening.
  bool _listening = false;

  @override
  void initState() {
    super.initState();
    _activeArtifact = widget.initialArtifact;
    _initLocation();
    _parseArtifactData();
  }

  void _parseArtifactData() {
    if (_activeArtifact == null) return;
    final data = (_activeArtifact!['data'] as Map<String, dynamic>?) ?? _activeArtifact!;
    
    num? lat = (data['latitude'] ?? data['lat'] ?? data['center']?['lat']) as num?;
    num? lng = (data['longitude'] ?? data['lng'] ?? data['center']?['lng']) as num?;

    final markers = <Marker>[];
    final polylines = <Polyline>[];

    // Check candidate zones / markers in artifact
    final rawZones = (data['zones'] as List?) ?? (data['pfz_points'] as List?) ?? (data['candidates'] as List?) ?? [];
    for (final z in rawZones) {
      if (z is Map) {
        final zLat = (z['lat'] ?? z['latitude']) as num?;
        final zLng = (z['lng'] ?? z['longitude']) as num?;
        final zName = (z['name'] ?? z['zone_id'] ?? 'PFZ Candidate').toString();
        if (zLat != null && zLng != null) {
          if (lat == null) {
            lat = zLat;
            lng = zLng;
          }
          markers.add(
            Marker(
              point: LatLng(zLat.toDouble(), zLng.toDouble()),
              width: 32,
              height: 32,
              child: Tooltip(
                message: zName,
                child: Container(
                  decoration: BoxDecoration(
                    color: SamudraColors.accentCyan,
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 2),
                    boxShadow: const [BoxShadow(color: Colors.black45, blurRadius: 4)],
                  ),
                  child: const Icon(Icons.phishing, size: 18, color: SamudraColors.backgroundDark),
                ),
              ),
            ),
          );
        }
      }
    }

    // Check primary location point
    if (lat != null && lng != null) {
      _center = LatLng(lat.toDouble(), lng.toDouble());
      _zoom = 11.0;
      markers.add(
        Marker(
          point: _center,
          width: 36,
          height: 36,
          child: Container(
            decoration: BoxDecoration(
              color: SamudraColors.accentBlue,
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 2.5),
              boxShadow: const [BoxShadow(color: Colors.black54, blurRadius: 6)],
            ),
            child: const Icon(Icons.location_on, size: 22, color: Colors.white),
          ),
        ),
      );
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _mapController.move(_center, _zoom);
      });
    }

    // Check route points / waypoints
    final waypoints = (data['waypoints'] as List?) ?? (data['route_points'] as List?) ?? (data['coordinates'] as List?) ?? [];
    final routePoints = <LatLng>[];
    for (final wp in waypoints) {
      if (wp is Map) {
        final wLat = (wp['lat'] ?? wp['latitude']) as num?;
        final wLng = (wp['lng'] ?? wp['longitude']) as num?;
        if (wLat != null && wLng != null) {
          routePoints.add(LatLng(wLat.toDouble(), wLng.toDouble()));
        }
      } else if (wp is List && wp.length >= 2) {
        final wLat = wp[0] as num;
        final wLng = wp[1] as num;
        routePoints.add(LatLng(wLat.toDouble(), wLng.toDouble()));
      }
    }

    if (routePoints.length >= 2) {
      polylines.add(
        Polyline(
          points: routePoints,
          strokeWidth: 4.0,
          color: SamudraColors.accentCyan,
        ),
      );
    }

    _artifactMarkers = markers;
    _artifactPolylines = polylines;
  }

  @override
  void dispose() {
    _locationSub?.cancel();
    _mapController.dispose();
    super.dispose();
  }

  // ── GPS ────────────────────────────────────────────────────────────────────

  Future<void> _initLocation() async {
    _locationSub = LocationService.instance.locationStream.listen(
      (data) {
        if (!mounted) return;
        setState(() {
          _currentLocation = data;
          _gpsMessage = null;
        });
      },
      onError: (_) {
        if (mounted) setState(() => _gpsMessage = 'Location unavailable');
      },
    );

    // One-shot attempt to centre on the current fix, if one exists.
    final fix = LocationService.instance.lastLocation ??
        await LocationService.instance.getCurrentLocation();
    if (!mounted) return;
    if (fix != null) {
      setState(() {
        _currentLocation = fix;
        _gpsMessage = null;
        _center = LatLng(fix.latitude, fix.longitude);
      });
      // Move once the map has been laid out (MapController must be attached).
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _mapController.move(_center, 10.0);
      });
    } else {
      setState(() => _gpsMessage = _locationMessage);
    }
  }

  String get _locationMessage {
    switch (LocationService.instance.currentStatus) {
      case LocationStatus.serviceDisabled:
        return 'Location services are disabled.';
      case LocationStatus.permissionDenied:
      case LocationStatus.permissionPermanentlyDenied:
        return 'Location permission is required.';
      case LocationStatus.error:
        return 'Location unavailable.';
      default:
        return 'Searching for GPS… showing region view.';
    }
  }

  Future<void> _locate() async {
    if (_locating) return;
    setState(() => _locating = true);
    final fix = await LocationService.instance.getCurrentLocation();
    if (!mounted) return;
    setState(() {
      _locating = false;
      if (fix != null) {
        _currentLocation = fix;
        _gpsMessage = null;
        _center = LatLng(fix.latitude, fix.longitude);
      } else {
        _gpsMessage = _locationMessage;
      }
    });
    if (fix != null) _mapController.move(_center, 10.0);
  }

  // ── Layer toggles ─────────────────────────────────────────────────────────

  void _toggleOceanLayer(String id) {
    setState(() {
      if (_visibleOceanLayerIds.contains(id)) {
        _visibleOceanLayerIds.remove(id);
      } else {
        _visibleOceanLayerIds.add(id);
      }
    });
  }

  bool _isOceanLayerVisible(String id) => _visibleOceanLayerIds.contains(id);

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: SamudraColors.backgroundDark,
      appBar: widget.embedded ? null : _buildAppBar(context),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (widget.embedded) _embeddedHeader(context),
          _searchBar(context),
          _filterRow(context),
          const SizedBox(height: 8),
          Expanded(child: _buildMap(context)),
          const SizedBox(height: 8),
        ],
      ),
    );
  }

  PreferredSizeWidget _buildAppBar(BuildContext context) {
    return AppBar(
      backgroundColor: SamudraColors.backgroundDark,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back, color: SamudraColors.textSecondary),
        onPressed: () => Navigator.pop(context),
      ),
      title: const _NavTitle(label: 'Marine Map'),
      centerTitle: false,
    );
  }

  Widget _embeddedHeader(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child:
          Text('Marine Map', style: Theme.of(context).textTheme.headlineMedium),
    );
  }

  Widget _searchBar(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
      child: Container(
        decoration: BoxDecoration(
          color: SamudraColors.backgroundCard,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: SamudraColors.borderSubtle),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        child: Row(
          children: [
            const Icon(Icons.search,
                color: SamudraColors.textMuted, size: 18),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                _listening
                    ? 'Listening… speak now'
                    : 'Search coordinates or zones…',
                style: Theme.of(context)
                    .textTheme
                    .bodyMedium
                    ?.copyWith(
                      color: _listening
                          ? SamudraColors.statusDanger
                          : SamudraColors.textMuted,
                    ),
              ),
            ),
            VoiceInputButton(
              onText: _onVoiceQuery,
              onListeningChanged: (listening) {
                if (mounted) setState(() => _listening = listening);
              },
            ),
          ],
        ),
      ),
    );
  }

  /// Handles a voice-transcribed query from the search-bar microphone: route it
  /// to the Assistant (via [widget.onVoiceQuery]) which auto-submits to the
  /// existing backend.
  void _onVoiceQuery(String query) {
    final text = query.trim();
    if (text.isEmpty) return;
    widget.onVoiceQuery?.call(text);
  }

  Widget _filterRow(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          _MapFilterChip(
            label: 'Fishing Zones',
            active: _showFishingZones,
            onTap: () => setState(() => _showFishingZones = !_showFishingZones),
          ),
          const SizedBox(width: 8),
          _MapFilterChip(
            label: 'Wave Height',
            active: _isOceanLayerVisible('copernicus-wave'),
            onTap: () => _toggleOceanLayer('copernicus-wave'),
          ),
          const SizedBox(width: 8),
          _MapFilterChip(
            label: 'IMBL',
            active: _showImbl,
            onTap: () => setState(() => _showImbl = !_showImbl),
          ),
          const Spacer(),
          IconButton(
            tooltip: 'Ocean layers',
            icon: const Icon(Icons.layers_outlined,
                color: SamudraColors.textSecondary, size: 22),
            onPressed: _openLayersSheet,
          ),
        ],
      ),
    );
  }

  void _openLayersSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: SamudraColors.backgroundCard,
      builder: (ctx) {
        // StatefulBuilder lets the sheet re-render its switches while the
        // parent (_MarineMapScreenState) keeps the authoritative layer state.
        return StatefulBuilder(
          builder: (context, setSheetState) {
            return _LayersSheet(
              registry: _registry,
              visibleIds: _visibleOceanLayerIds,
              onToggle: (id) {
                _toggleOceanLayer(id);
                setSheetState(() {});
              },
            );
          },
        );
      },
    );
  }

  Widget _buildMap(BuildContext context) {
    final imblPolygon = DemoImbl.polygon();

    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: _center,
              initialZoom: _zoom,
              minZoom: 3,
              maxZoom: 18,
              backgroundColor: const Color(0xFF0A1628),
              onPositionChanged: (position, hasGesture) {
                _center = position.center;
                _zoom = position.zoom;
              },
            ),
            children: [
              // Base basemap (Carto dark) — requires internet.
              TileLayer(
                urlTemplate:
                    'https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=cb1_2tka_1_84b8380ea0ef34e5e4bac11c',
                userAgentPackageName: _userAgent,
                maxNativeZoom: 19,
                errorTileCallback: (tile, error, stackTrace) {
                  // Swallow tile errors so offline/network failure never crashes.
                },
              ),
              // Copernicus Marine WMTS ocean overlays.
              for (final layer in _registry.renderableLayers)
                if (_isOceanLayerVisible(layer.id))
                  TileLayer(
                    urlTemplate: buildWmtsTileUrlTemplate(
                        layer.toCopernicusConfig(defaultSstConfig)),
                    userAgentPackageName: _userAgent,
                    maxNativeZoom: 9,
                    errorTileCallback: (tile, error, stackTrace) {
                      // Swallow tile errors (offline / service unavailable).
                    },
                  ),
              // Fishing-zone (PFZ) DEMO polygons.
              if (_showFishingZones)
                PolygonLayer(
                  polygons: [
                    for (final zone in DemoPfzZones.zones)
                      if (zone.geometry.points.length >= 3)
                        Polygon(
                          points: zone.geometry.toLatLng().map(
                              (p) => LatLng(p.lat, p.lon)).toList(),
                          color: SamudraColors.accentCyan.withValues(alpha: 0.18),
                          borderColor:
                              SamudraColors.accentCyan.withValues(alpha: 0.85),
                          borderStrokeWidth: 2,
                        ),
                  ],
                ),
              // IMBL boundary overlay (existing demo data).
              if (_showImbl)
                PolygonLayer(
                  polygons: [
                    Polygon(
                      points: imblPolygon.polygon
                          .map((p) => LatLng(p.lat, p.lon))
                          .toList(),
                      color: SamudraColors.accentBlue.withValues(alpha: 0.12),
                      borderColor: SamudraColors.accentBlue,
                      borderStrokeWidth: 2.5,
                    ),
                  ],
                ),
              // Dynamic artifact route polylines
              if (_artifactPolylines.isNotEmpty)
                PolylineLayer(polylines: _artifactPolylines),

              // Dynamic artifact markers
              if (_artifactMarkers.isNotEmpty)
                MarkerLayer(markers: _artifactMarkers),

              // Current-location marker.
              if (_currentLocation != null)
                MarkerLayer(
                  markers: [
                    Marker(
                      point: LatLng(_currentLocation!.latitude,
                          _currentLocation!.longitude),
                      width: 22,
                      height: 22,
                      child: Container(
                        decoration: BoxDecoration(
                          color: SamudraColors.accentCyan,
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: Colors.white,
                            width: 2.5,
                          ),
                          boxShadow: const [
                            BoxShadow(
                              color: Color(0x66000000),
                              blurRadius: 6,
                              spreadRadius: 2,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              // Attribution (static, no external launcher dependency).
              const _AttributionOverlay(),
            ],
          ),

          // Active artifact focused banner overlay
          if (_activeArtifact != null)
            Positioned(
              top: 10,
              left: 10,
              right: 10,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: SamudraColors.backgroundCard.withValues(alpha: 0.95),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: SamudraColors.accentCyan.withValues(alpha: 0.5)),
                  boxShadow: const [BoxShadow(color: Colors.black45, blurRadius: 8)],
                ),
                child: Row(
                  children: [
                    const Icon(Icons.map_outlined, color: SamudraColors.accentCyan, size: 20),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            _activeArtifact!['title'] as String? ?? 'Active Map Artifact',
                            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                  color: SamudraColors.textPrimary,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                ),
                          ),
                          Text(
                            'Focused spatial view from chat artifact',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: SamudraColors.textMuted,
                                  fontSize: 10,
                                ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, size: 18, color: SamudraColors.textSecondary),
                      onPressed: () {
                        setState(() {
                          _activeArtifact = null;
                          _artifactMarkers = [];
                          _artifactPolylines = [];
                        });
                      },
                      tooltip: 'Clear Focus',
                    ),
                  ],
                ),
              ),
            ),

          // Top status / legend overlay.
          Positioned(
            top: _activeArtifact != null ? 70 : 10,
            left: 10,
            right: 10,
            child: _MapStatusOverlay(
              layerTitle: _activeLayerTitle,
              layerUnit: _activeLayerUnit,
              gpsMessage: _gpsMessage,
              showDemoBadge: _showFishingZones,
            ),
          ),

          // Bottom-right map controls.
          Positioned(
            right: 12,
            bottom: 12,
            child: _MapControls(
              onZoomIn: () =>
                  _mapController.move(_center, (_zoom + 1).clamp(3.0, 18.0)),
              onZoomOut: () =>
                  _mapController.move(_center, (_zoom - 1).clamp(3.0, 18.0)),
              onLocate: _locating ? null : _locate,
            ),
          ),
        ],
      ),
    );
  }

  String get _activeLayerTitle {
    if (_isOceanLayerVisible('copernicus-sst')) {
      return _registry.getLayer('copernicus-sst')?.name ?? 'Sea Surface Temperature';
    }
    if (_isOceanLayerVisible('copernicus-wave')) {
      return _registry.getLayer('copernicus-wave')?.name ?? 'Significant Wave Height';
    }
    if (_isOceanLayerVisible('copernicus-sla')) {
      return _registry.getLayer('copernicus-sla')?.name ?? 'Sea Level Anomaly';
    }
    if (_isOceanLayerVisible('copernicus-chl')) {
      return _registry.getLayer('copernicus-chl')?.name ?? 'Chlorophyll-a';
    }
    return 'Base Map';
  }

  String get _activeLayerUnit {
    final layer = _registry.getLayer('copernicus-sst');
    return layer?.unit ?? '';
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Map overlay widgets
// ─────────────────────────────────────────────────────────────────────────────

class _MapStatusOverlay extends StatelessWidget {
  final String layerTitle;
  final String layerUnit;
  final String? gpsMessage;
  final bool showDemoBadge;

  const _MapStatusOverlay({
    required this.layerTitle,
    required this.layerUnit,
    required this.gpsMessage,
    required this.showDemoBadge,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: SamudraColors.backgroundCard.withValues(alpha: 0.92),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: SamudraColors.borderSubtle),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Flexible(
                      child: Text(
                        layerTitle,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: SamudraColors.accentCyan,
                              fontWeight: FontWeight.w700,
                              fontSize: 11,
                              letterSpacing: 0.4,
                            ),
                      ),
                    ),
                    if (layerUnit.isNotEmpty) ...[
                      const SizedBox(width: 6),
                      Text(
                        '($layerUnit)',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: SamudraColors.textSecondary,
                              fontSize: 11,
                            ),
                      ),
                    ],
                  ],
                ),
                if (gpsMessage != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    gpsMessage!,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: SamudraColors.statusWarning,
                          fontSize: 10,
                        ),
                  ),
                ],
                if (showDemoBadge) ...[
                  const SizedBox(height: 2),
                  Text(
                    'Fishing zones are DEMO data',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: SamudraColors.textMuted,
                          fontSize: 9,
                        ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _MapControls extends StatelessWidget {
  final VoidCallback onZoomIn;
  final VoidCallback onZoomOut;
  final VoidCallback? onLocate;

  const _MapControls({
    required this.onZoomIn,
    required this.onZoomOut,
    required this.onLocate,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        _ControlButton(icon: Icons.add, tooltip: 'Zoom in', onTap: onZoomIn),
        const SizedBox(height: 8),
        _ControlButton(
            icon: Icons.remove, tooltip: 'Zoom out', onTap: onZoomOut),
        const SizedBox(height: 8),
        _ControlButton(
          icon: Icons.my_location,
          tooltip: 'Go to my location',
          onTap: onLocate,
          highlight: onLocate != null,
        ),
      ],
    );
  }
}

class _ControlButton extends StatelessWidget {
  final IconData icon;
  final String tooltip;
  final VoidCallback? onTap;
  final bool highlight;

  const _ControlButton({
    required this.icon,
    required this.tooltip,
    required this.onTap,
    this.highlight = false,
  });

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: Material(
        color: SamudraColors.backgroundCard.withValues(alpha: 0.92),
        shape: const CircleBorder(),
        child: InkWell(
          customBorder: const CircleBorder(),
          onTap: onTap,
          child: Container(
            width: 42,
            height: 42,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(
                color: highlight
                    ? SamudraColors.accentCyan
                    : SamudraColors.borderSubtle,
              ),
            ),
            child: Icon(
              icon,
              size: 20,
              color: onTap == null
                  ? SamudraColors.textMuted
                  : highlight
                      ? SamudraColors.accentCyan
                      : SamudraColors.textSecondary,
            ),
          ),
        ),
      ),
    );
  }
}

class _AttributionOverlay extends StatelessWidget {
  const _AttributionOverlay();

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.bottomLeft,
      child: Padding(
        padding: const EdgeInsets.all(4),
        child: Text(
          '© OpenStreetMap contributors © CARTO · Copernicus Marine',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: SamudraColors.textMuted,
                fontSize: 8,
              ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Filter chip
// ─────────────────────────────────────────────────────────────────────────────

class _MapFilterChip extends StatelessWidget {
  final String label;
  final bool active;
  final VoidCallback onTap;

  const _MapFilterChip({
    required this.label,
    required this.active,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: active
              ? SamudraColors.accentCyan.withValues(alpha: 0.15)
              : SamudraColors.backgroundCard,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: active ? SamudraColors.accentCyan : SamudraColors.borderSubtle,
            width: active ? 1 : 0.5,
          ),
        ),
        child: Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: active
                    ? SamudraColors.accentCyan
                    : SamudraColors.textSecondary,
                fontSize: 11,
                fontWeight: active ? FontWeight.w600 : FontWeight.w400,
              ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Ocean layers bottom sheet
// ─────────────────────────────────────────────────────────────────────────────

class _LayersSheet extends StatelessWidget {
  final OceanLayerRegistry registry;
  final Set<String> visibleIds;
  final void Function(String id) onToggle;

  const _LayersSheet({
    required this.registry,
    required this.visibleIds,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    final layers = registry.layers;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Ocean Layers',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: SamudraColors.textPrimary,
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 4),
            Text(
              'Copernicus Marine WMTS overlays',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: SamudraColors.textMuted,
                  ),
            ),
            const SizedBox(height: 12),
            for (final layer in layers)
              _LayerToggleTile(
                layer: layer,
                available: layer.isRenderable,
                active: visibleIds.contains(layer.id),
                onTap: layer.isRenderable ? () => onToggle(layer.id) : null,
              ),
          ],
        ),
      ),
    );
  }
}

class _LayerToggleTile extends StatelessWidget {
  final OceanMapLayer layer;
  final bool available;
  final bool active;
  final VoidCallback? onTap;

  const _LayerToggleTile({
    required this.layer,
    required this.available,
    required this.active,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      dense: true,
      contentPadding: EdgeInsets.zero,
      leading: Icon(
        Icons.layers,
        size: 20,
        color: available
            ? SamudraColors.accentCyan
            : SamudraColors.textMuted,
      ),
      title: Text(
        layer.name,
        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: available
                  ? SamudraColors.textPrimary
                  : SamudraColors.textMuted,
              fontSize: 14,
            ),
      ),
      subtitle: available
          ? Text(
              '${layer.unit} · ${layer.temporalResolution ?? ''}',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: SamudraColors.textSecondary,
                    fontSize: 11,
                  ),
            )
          : Text(
              'Coming soon',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: SamudraColors.statusWarning,
                    fontSize: 11,
                  ),
            ),
      trailing: available
          ? Switch(
              value: active,
              activeThumbColor:
                  SamudraColors.accentCyan,
              onChanged: (_) => onTap?.call(),
            )
          : const SizedBox.shrink(),
      onTap: onTap,
    );
  }
}

class _NavTitle extends StatelessWidget {
  final String label;
  const _NavTitle({required this.label});

  @override
  Widget build(BuildContext context) {
    return Text(label,
        style:
            Theme.of(context).textTheme.headlineSmall?.copyWith(fontSize: 17));
  }
}
