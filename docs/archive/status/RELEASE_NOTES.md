# Tally Sync Agent — Release Notes

## v0.4.0 (2026-06-28)

### New Features
- **Registration system**: One-time installation key flow (portal → agent → cloud)
- **OTA auto-updater**: Agent checks daily and self-updates with rollback support
- **Registration wizard**: GUI onboarding dialog shown during first install
- **Windows installer**: Inno Setup .exe wizard with NSSM service installation
- **CI/CD pipeline**: GitHub Actions builds, signs, and publishes on every tag

### What's Included
- `TallySyncAgent.exe` — background sync service
- `registration_wizard.exe` — first-run onboarding GUI
- `TallySyncAgent-Setup-0.4.0.exe` — full installer with service install

### Upgrade Path
Agents on v0.3.x will auto-update via OTA within 24 hours of this release.
No manual action required.

### Known Limitations
- Code signing: exe is unsigned in this release (EV cert pending)
- SmartScreen may warn on first launch — click "More info → Run anyway"
