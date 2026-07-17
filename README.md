# Audio Noise Remover from Video 🎬🔊

A Python desktop application that **extracts the audio from a video, removes background noise, and re-embeds the cleaned audio back into the video** — all with one click, fully offline.

> Developed by **Alok Sahni** as the project for the **NIELIT 'O' Level Examination**, under the guidance of **Mr. Tarun Verma** (C Institute, Bikaner, Rajasthan).

---

## ✨ Features

- Simple **Tkinter GUI** — no command line or DSP knowledge required
- Supports **.mp4** and **.mkv** input files
- **Spectral-gating noise reduction** using the `noisereduce` library
- **Preview original vs cleaned audio** directly inside the app
- Output is a **complete playable video** (`<name>_cleaned.mp4`), not just an audio file
- Video stream is **copied without re-encoding** (fast, no quality loss)
- 100% **local processing** — no uploads, no privacy concerns

## 🖥️ How It Works

```
Select video ──► MoviePy extracts audio (WAV)
             ──► SciPy reads WAV, stereo → mono
             ──► First 5000 samples taken as noise profile
             ──► noisereduce removes noise (spectral gating)
             ──► Cleaned 16-bit WAV saved
             ──► FFmpeg merges cleaned audio + original video
             ──► Output: <name>_cleaned.mp4
```

## 🛠️ Tech Stack

| Tool / Library | Purpose |
| --- | --- |
| Python 3.x | Programming language |
| Tkinter | GUI interface |
| MoviePy | Extracting audio from video |
| scipy.io.wavfile | Reading/writing WAV audio |
| noisereduce | Noise reduction |
| playsound | Audio preview |
| FFmpeg | Re-merging audio into video |

## 📋 Requirements

- Windows 10 or above
- Python 3.7+
- [FFmpeg](https://ffmpeg.org/download.html) installed at `C:\ffmpeg\bin\ffmpeg.exe` (or edit `ffmpeg_path` in the code)

## 🚀 Installation & Usage

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/Audio-Noise-Remover.git
cd Audio-Noise-Remover

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python audio_noise_remover.py
```

Then in the app: **Browse** → select a video → **Clean Audio** → the cleaned video is saved next to the original as `<name>_cleaned.mp4`.

## 📄 Documentation

- [Project Report (PDF)](docs/Project_Report.pdf) — full NIELIT 'O' Level project report
- [Project Presentation (PPTX)](docs/Project_Presentation.pptx) — 21-slide presentation

## ⚠️ Known Limitations

- Noise profile is always taken from the **first 5000 samples** (assumes the recording starts with noise only)
- FFmpeg path is **hard-coded for Windows**
- Processing is synchronous — the GUI may freeze on long videos
- No formal quality metrics (SNR); verification is by listening comparison

## 🔮 Future Scope

- User-selectable noise sample region
- Automatic cross-platform FFmpeg detection
- Background threading for a responsive GUI
- Batch processing of multiple videos
- Before/after waveform visualisation

## 👤 Author

**Alok Sahni**
NIELIT 'O' Level Candidate — C Institute, Bikaner, Rajasthan
Guide: Mr. Tarun Verma (A Level NIELIT, M.Sc. Computer Science, MGSU Bikaner)

## 📜 License

This project is licensed under the [MIT License](LICENSE).
