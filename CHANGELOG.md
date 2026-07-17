# Changelog

All notable changes to **Subtitle Muxer** will be documented in this file.

The format is based on **Keep a Changelog** and this project adheres to **Semantic Versioning**.

## [Unreleased]

### Added
- App icon (steampunk projector): transparent PNG master, `256×256` PNG, and multi-size Windows `.ico` (includes 256) under `assets/`.
- Pre-mux **duration mismatch** warning when source and target lengths differ by 2+ seconds (confirm to continue).

### Fixed
- Windows title-bar icon now uses the `.ico` (`iconbitmap`) instead of leaving the default Tk blue cube.
- Subtitle track list no longer shows a scrollbar when nothing needs scrolling (empty / few tracks).
- Removed the duplicate app title/version and tagline from the main window body (version stays in the title bar and About).

## [0.1.1] - 2026-07-16

### Fixed
- Corrected GitHub Release packaging so Mac/Linux assets are proper `.tar.gz` archives and not tiny placeholder files.

### Changed
- Windows download layout is now clearer:
  - Portable stays as a `.zip` container for the single `.exe` (room for extras later).
  - Windows “installer” is now a real **Setup.exe** build (Inno Setup), not a zipped folder.
- GitHub Release assets are no longer blanket-zipped for every platform/variant.

### Added
- Added an Inno Setup build script (`scripts/windows/SubtitleMuxer.iss`) to produce the real Windows Setup.exe installer.

## [0.1.0] - 2026-07-15

### Added
- Initial public release of Subtitle Muxer: a desktop app that copies **soft subtitle tracks** from a source video onto a target video using **FFmpeg stream copy** (no re-encoding).
- Windows, macOS (Apple Silicon + Intel), and multiple Linux distro builds.

