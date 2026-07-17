# Audio Noise Remover from Video — Web Front-End

Browser-based version of the NIELIT 'O' Level project by Alok Sahni.
Upload a video → noisy audio is extracted, cleaned by spectral gating,
and merged back → compare waveforms & audio in the page → download.

## Run

```bash
pip install -r requirements.txt
# FFmpeg must be installed (ffmpeg.org) — auto-detected on PATH
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Structure

- `app.py` — Flask backend (same 5-step pipeline as the desktop app)
- `templates/index.html` — front-end UI (drag-drop, pipeline steps, waveforms, players)
- `jobs/` — per-upload working folders (created automatically)
