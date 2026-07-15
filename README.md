# Subtitle Muxer

Copy subtitle tracks from one video onto another — for example an original rip with softsubs onto an upscaled version that has none — with **no re-encoding** (stream copy).

---

## Screenshots

![Main window](docs/images/main-window.png)

![Destination settings](docs/images/destination.png)

![Mux complete](docs/images/mux-complete.png)

---

## Features

- Pick a **source** video (with subtitles) and a **target** video (video/audio to keep)
- Drag-and-drop or browse for files
- View every subtitle track (language, format, title) and choose which ones to copy
- Set a default **save folder** and filename (remembered between sessions)
- Output as **MKV** (recommended) or **MP4**
- Watch FFmpeg progress in the built-in log panel
- FFmpeg is bundled — no separate install required for normal use

---

## Download

1. Open this repository’s **[Releases](https://github.com/CavemanTechandGamming/Subtitle-Muxer/releases)** page.
2. Download the zip for your OS:
   - **Windows** — `…-windows-portable` (single `.exe`) or `…-windows-installer` (folder)
   - **Mac** — `…-mac-apple-silicon` or `…-mac-intel`
   - **Linux** — `…-<distro>` (e.g. `…-ubuntu`)
3. Extract if needed, then run **Subtitle Muxer**. No separate FFmpeg install is required for normal use.

---

## How to use

1. Load the **Source** video that already has the subtitles you want.
2. Load the **Target** video you want to keep (for example your upscaled file).
3. Select the subtitle tracks to copy, or leave **Select All** checked.
4. Choose a **Destination** folder and filename (or click **Same as target**).
5. Pick **MKV** or **MP4**, then click **Mux Subtitles**.

That’s it — the target’s video and audio stay as-is; only the selected subtitle streams are added.

---

## Tips

- Prefer **MKV** when possible. Some subtitle formats (ASS, PGS, and others) do not copy cleanly into MP4.
- Soft subtitle *tracks* can be copied. Burned-in subtitles, or closed captions baked into the video stream, cannot be extracted this way.
- If a track does not appear in the list, that file likely has no separate subtitle streams.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Contributing

Want to build from source or send a pull request? See [CONTRIBUTING.md](CONTRIBUTING.md).
