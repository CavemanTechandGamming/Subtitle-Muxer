# Contributing

Thanks for helping improve Subtitle Muxer. This document is for people developing or packaging the app. End-user download and usage instructions live in [README.md](README.md).

## Repository layout

Keep the **repository root** reserved for project metadata only:

| Path | Purpose |
|------|---------|
| `README.md` | End-user overview |
| `LICENSE` | License text |
| `CONTRIBUTING.md` | This file |
| `.gitignore` | Tells Git which **local** files to skip |
| `.github/` | GitHub Actions workflows |
| `docs/images/` | Screenshots and other images for the README |
| `src/` | Application source code |
| `scripts/` | Setup / run / build helpers |
| `requirements/` | Python dependency pins |

Do not add application code, build outputs, or virtualenvs at the root.

## Version number (single source of truth)

The app version lives in **one place only**:

```text
src/__init__.py  →  __version__ = "x.y.z"
```

Everything else reads from that value:

- Window title and About dialog
- `python scripts/read_version.py` (used by CI)
- GitHub Release tags / asset names (`vX.Y.Z`, `SubtitleMuxer-X.Y.Z-…`)

**When shipping a new release:** bump `__version__` in `src/__init__.py`, commit, then run **Build and Release**. Do not hard-code the version in workflows or scripts.

## About `.gitignore`

**`.gitignore` should be committed to GitHub.** It is a normal tracked file.

What should *not* go to GitHub are the paths listed **inside** `.gitignore`, for example:

- `.venv/` (local virtual environment)
- `build/` and `dist/` (PyInstaller outputs)
- `__pycache__/`, IDE folders, local media files

Those stay on your machine (or in CI artifacts).

## Development setup

Requires **Python 3.10+** (development / CI currently use **3.14**).

**Windows:**

```bat
scripts\setup_env.bat
```

**Linux / macOS:**

```bash
chmod +x scripts/setup_env.sh scripts/build_app.sh
./scripts/setup_env.sh
```

This creates `.venv`, upgrades `pip`, installs packages from `requirements/requirements.txt`, and downloads bundled FFmpeg binaries via `static-ffmpeg`.

## Run from source

**Windows:**

```bat
scripts\run_app.bat
```

**Any platform (from the repository root):**

```bash
python -m src
```

## Build locally

Windows builds a **portable** onefile `.exe` and a real **Setup.exe** (Inno Setup 6 required).
Linux and Mac default to one packaged binary each.

| Type | Example |
|------|---------|
| Windows portable | `dist/windows/0.1.1/portable/SubtitleMuxer-0.1.1.exe` |
| Windows setup | `dist/windows/0.1.1/setup/SubtitleMuxer-0.1.1-windows-setup.exe` |
| Mac Apple Silicon | `dist/mac-apple-silicon/0.1.1/portable/SubtitleMuxer-0.1.1` |
| Mac Intel | `dist/mac-intel/0.1.1/portable/SubtitleMuxer-0.1.1` |

```bat
scripts\build_app.bat
```

Requires [Inno Setup 6](https://jrsoftware.org/isinfo.php) on `PATH` (or the default install location). On CI it is installed with Chocolatey.

```bash
./scripts/build_app.sh
# Optional: also build the onedir layout
SUBTITLE_MUXER_BUILD_KINDS=both ./scripts/build_app.sh
```

## GitHub Actions

Two manual workflows (no push/PR triggers):

| Workflow | File | What it does |
|----------|------|----------------|
| **Build** | [`.github/workflows/build.yml`](.github/workflows/build.yml) | Matrix build → upload versioned artifacts |
| **Build and Release** | [`.github/workflows/release.yml`](.github/workflows/release.yml) | Same builds → GitHub Release with versioned assets |

Windows/macOS default to Python **3.14**. Linux builds use each distro’s system Python in containers.

### What gets built

| Platform | Artifact / release asset |
|----------|--------------------------|
| Windows portable | CI artifact `…-portable` → release `SubtitleMuxer-…-windows-portable.zip` |
| Windows setup | CI artifact `…-setup` → release `SubtitleMuxer-…-windows-setup.exe` |
| Mac Apple Silicon | `subtitle-muxer-mac-apple-silicon-…` → `.tar.gz` |
| Mac Intel | `subtitle-muxer-mac-intel-…` → `.tar.gz` |
| Linux | `subtitle-muxer-<distro>-…` → `.tar.gz` |

### Linux matrix

GitHub only hosts Ubuntu runners, so Linux flavours are built in Docker containers:

| Platform label | Container image |
|----------------|-----------------|
| `ubuntu` | `ubuntu:24.04` |
| `debian` | `debian:bookworm` |
| `mint` | `linuxmintd/mint22.1-amd64` |
| `fedora` | `fedora:latest` |
| `arch` | `archlinux:latest` |

### Build only

1. Actions → **Build** → **Run workflow**
2. Download the versioned artifacts when finished

```bash
gh workflow run build.yml
gh run watch
gh run download
```

### Build and release

1. Bump `__version__` in `src/__init__.py` and push to `main`
2. Actions → **Build and Release** → **Run workflow**
3. Creates tag `vX.Y.Z` and attaches assets such as:

   - `SubtitleMuxer-0.1.1-windows-portable.zip`
   - `SubtitleMuxer-0.1.1-windows-setup.exe`
   - `SubtitleMuxer-0.1.1-mac-apple-silicon.tar.gz`
   - `SubtitleMuxer-0.1.1-mac-intel.tar.gz`
   - `SubtitleMuxer-0.1.1-ubuntu.tar.gz`
   - (same `.tar.gz` pattern for `debian`, `mint`, `fedora`, `arch`)

Optional inputs: **draft**, **prerelease**.

```bash
gh workflow run "Build and Release"
# or: gh workflow run release.yml
```

If `vX.Y.Z` already exists, the release job fails — bump the version and try again.

## Screenshots

Put PNG/WebP screenshots in [`docs/images/`](docs/images/).  
Filename conventions and README wiring are described in [`docs/images/README.md`](docs/images/README.md).

## Code organization

- UI (CustomTkinter): `src/ui/`
- FFmpeg / ffprobe / settings: `src/core/`
- Prefer small, focused pull requests
