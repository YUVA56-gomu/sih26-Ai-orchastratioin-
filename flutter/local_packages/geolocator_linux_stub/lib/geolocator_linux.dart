// No-op stub — Android-only project, Linux desktop is never used.
// Satisfies the geolocator plugin platform registry without pulling in
// package_info_plus (which causes Kotlin cache failures on cross-drive builds).

library geolocator_linux;

import 'package:geolocator_platform_interface/geolocator_platform_interface.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';

class GeolocatorLinux extends GeolocatorPlatform {
  static void registerWith() {
    // Only register if no implementation is already set.
    // On Android this will never be called.
    GeolocatorPlatform.instance = GeolocatorLinux();
  }
}
