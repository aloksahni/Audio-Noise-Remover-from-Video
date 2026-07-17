# ============================================================
# Project Title : Audio Noise Remover from Video — Web Front-End
# Developed By  : Alok Sahni
# Course        : NIELIT 'O' Level Project (front-end version)
# Stack         : Flask + MoviePy + SciPy + Noisereduce + FFmpeg
#
# Run:  python app.py   →  open http://127.0.0.1:5000
# ============================================================

import os
import shutil
import uuid
import subprocess

from flask import (Flask, render_template, request, jsonify,
                   send_from_directory)
from werkzeug.utils import secure_filename
from scipy.io import wavfile
import noisereduce as nr

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOBS_DIR = os.path.join(BASE_DIR, "jobs")
os.makedirs(JOBS_DIR, exist_ok=True)

ALLOWED_EXT = {".mp4", ".mkv"}
MAX_SIZE_MB = 500

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_SIZE_MB * 1024 * 1024


def find_ffmpeg():
    """Locate FFmpeg on any OS; fall back to the classic Windows path."""
    found = shutil.which("ffmpeg")
    if found:
        return found
    windows_default = r"C:\ffmpeg\bin\ffmpeg.exe"
    if os.path.exists(windows_default):
        return windows_default
    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    # ---- validate input ----
    if "video" not in request.files:
        return jsonify(error="No file uploaded."), 400
    f = request.files["video"]
    ext = os.path.splitext(f.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify(error="Only .mp4 and .mkv files are supported."), 400

    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        return jsonify(error="FFmpeg was not found on this system. "
                             "Install it from ffmpeg.org."), 500

    try:
        noise_secs = float(request.form.get("noise_secs", "0.5"))
    except ValueError:
        noise_secs = 0.5
    noise_secs = min(max(noise_secs, 0.1), 5.0)

    # ---- per-job working folder ----
    job = uuid.uuid4().hex[:12]
    jdir = os.path.join(JOBS_DIR, job)
    os.makedirs(jdir, exist_ok=True)
    in_name = secure_filename(f.filename) or ("input" + ext)
    in_path = os.path.join(jdir, in_name)
    f.save(in_path)

    try:
        # 1. Extract audio with FFmpeg directly (mono 16-bit WAV).
        #    Much lower memory than MoviePy and one less failure point.
        original_wav = os.path.join(jdir, "original.wav")
        r = subprocess.run(
            [ffmpeg, "-y", "-i", in_path, "-vn",
             "-ac", "1", "-acodec", "pcm_s16le", original_wav],
            capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(original_wav):
            return jsonify(error="Could not extract audio: "
                                 + r.stderr[-300:]), 400

        # 2. Read WAV (already mono)
        rate, data = wavfile.read(original_wav)
        if len(data.shape) == 2:                       # safety net
            data = data.mean(axis=1)
        data = data.astype("float32")

        # 3. Noise profile from the first N seconds
        n = max(1000, int(rate * noise_secs))
        noise_sample = data[:n]

        # 4. Chunked noise reduction — bounds memory on long videos.
        #    Each 30-second block is cleaned against the same noise
        #    profile, so results match single-pass processing.
        import numpy as np
        chunk_len = rate * 30
        cleaned_parts = []
        total = len(data)
        for start in range(0, total, chunk_len):
            block = data[start:start + chunk_len]
            cleaned_parts.append(
                nr.reduce_noise(y=block, sr=rate, y_noise=noise_sample))
            print(f"[job {job}] cleaned "
                  f"{min(start + chunk_len, total) * 100 // total}%",
                  flush=True)
        reduced = np.concatenate(cleaned_parts)
        del cleaned_parts, data

        # 5. Save cleaned audio (16-bit WAV)
        cleaned_wav = os.path.join(jdir, "cleaned.wav")
        wavfile.write(cleaned_wav, rate,
                      np.clip(reduced, -32768, 32767).astype("int16"))
        del reduced

        # 6. Merge cleaned audio back into the video
        out_name = os.path.splitext(in_name)[0] + "_cleaned.mp4"
        out_path = os.path.join(jdir, out_name)
        command = [
            ffmpeg, "-y",
            "-i", in_path,
            "-i", cleaned_wav,
            "-c:v", "copy",
            "-map", "0:v:0",
            "-map", "1:a:0",
            out_path,
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify(error="FFmpeg failed: "
                                 + result.stderr[-300:]), 500

        return jsonify(
            job=job,
            original_audio=f"/media/{job}/original.wav",
            cleaned_audio=f"/media/{job}/cleaned.wav",
            cleaned_video=f"/media/{job}/{out_name}",
            video_name=out_name,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()            # full details in the terminal
        return jsonify(error=type(e).__name__ + ": " + str(e)), 500


@app.route("/health")
def health():
    import scipy, noisereduce
    return jsonify(ok=True, ffmpeg=find_ffmpeg(),
                   scipy=scipy.__version__)


@app.route("/media/<job>/<path:name>")
def media(job, name):
    jdir = os.path.join(JOBS_DIR, secure_filename(job))
    return send_from_directory(jdir, name)


if __name__ == "__main__":
    import webbrowser
    import threading as _t
    print("=" * 52)
    print("  Audio Noise Remover — web front-end")
    print("  FFmpeg :", find_ffmpeg() or "NOT FOUND (install from ffmpeg.org)")
    print("  Open   : http://127.0.0.1:5000")
    print("=" * 52)
    _t.Timer(1.2, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
