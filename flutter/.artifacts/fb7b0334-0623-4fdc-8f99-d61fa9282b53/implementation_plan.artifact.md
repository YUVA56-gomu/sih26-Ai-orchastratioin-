# SAMUDRA AI — Finish Notification Permission Fix

Verify and fix the Android 13+ notification permission flow for the Background Safety Monitor.

## User Review Required

- **Permission Request Logic**: The app will now explicitly request notification permission before starting the background monitor on Android 13+.
- **Settings Interop**: If the user permanently denies the permission, they will be directed to the App Settings page.

## Proposed Changes

### [Background Monitoring Service]

#### [MODIFY] [background_monitor_service.dart](file:///D:/flutter/samudra_ai/lib/services/background_monitor_service.dart)
- Simplify notification permission checks by removing redundant manual SDK version parsing.
- Let `permission_handler` manage Android version compatibility.
- Update `start()` logic to ensure it doesn't proceed without notification permission on supported Android versions.

### [Settings UI]

#### [MODIFY] [settings_screen.dart](file:///D:/flutter/samudra_ai/lib/screens/settings/settings_screen.dart)
- Update `_BackgroundMonitorPanel` to observe app lifecycle.
- Automatically re-check notification permission when the user returns to the app from Android Settings.
- Improve the "Grant Notification Permission" button behavior to handle both the initial request and the "Permanently Denied" case (opening settings).

## Verification Plan

### Automated Tests
- Run `flutter analyze` to ensure no regressions.
- Run `flutter build apk --debug` to verify the build completes successfully with `compileSdk 37`.

### Manual Verification
1. Open Background Safety Monitor settings.
2. Verify "Permission Required" is shown if notifications are disabled.
3. Tap "Start Monitoring".
4. Verify Android permission dialog appears (on Android 13+).
5. Grant permission and verify the monitor starts and notification appears.
6. Revoke permission in Android Settings.
7. Return to the app and verify the UI updates to "Permission Required" / "Notification Blocked".
8. Verify "Grant Notification Permission" button takes the user back to settings or shows the dialog.
