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

## About `.gitignore`

**`.gitignore` should be committed to GitHub.** It is a normal tracked file.

What should *not* go to GitHub are the paths listed **inside** `.gitignore`, for example:

- `.venv/` (local virtual environment)
- `build/` and `dist/` (PyInstaller outputs)
- `__pycache__/`, IDE folders, local media files

Those stay on your machine (or in CI artifacts).

## Development setup

Requires **Python 3.10+**.

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

PyInstaller outputs (gitignored) go under `dist/<platform>/`:

| Type | Example |
|------|---------|
| Portable (`--onefile`) | `dist/windows/onefile/SubtitleMuxer.exe` |
| Folder (`--onedir`) | `dist/windows/onedir/SubtitleMuxer/` |

```bat
scripts\build_app.bat
```

```bash
./scripts/build_app.sh
```

## Build with GitHub Actions (manual)

Workflow: [`.github/workflows/build.yml`](.github/workflows/build.yml)

- Trigger: **Actions → Build → Run workflow** only (`workflow_dispatch` — no push/PR builds)
- Matrix: `windows-latest`, `ubuntu-latest`, `macos-latest`
- Artifacts: `subtitle-muxer-<platform>-onefile` and `…-onedir`

```bash
gh workflow run build.yml
gh run watch
gh run download
```

## Screenshots

Put PNG/WebP screenshots in [`docs/images/`](docs/images/).  
Filename conventions and README wiring are described in [`docs/images/README.md`](docs/images/README.md).

## Code organization

- UI (CustomTkinter): `src/ui/`
- FFmpeg / ffprobe / settings: `src/core/`
- Prefer small, focused pull requests
