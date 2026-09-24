import 'package:flutter/material.dart';
import '../screens/marine_map/marine_map_screen.dart';

/// Clean deep-link helper to open the dedicated MarineMapScreen focused on an artifact.
void openMapArtifact(BuildContext context, Map<String, dynamic> artifact) {
  Navigator.push(
    context,
    MaterialPageRoute(
      builder: (_) => MarineMapScreen(initialArtifact: artifact),
    ),
  );
}
