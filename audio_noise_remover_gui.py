# ============================================================
# Project Title : Audio Noise Remover from Video  (Modern GUI)
# Developed By  : Alok Sahni
# Course        : NIELIT 'O' Level Project
# Language Used : Python 3.x
# Tools         : CustomTkinter, MoviePy, SciPy, Noisereduce, FFmpeg
#
# A user-friendly redesign of the original Tkinter interface:
#   • modern dark theme with rounded cards and clear hierarchy
#   • drag-free 3-step flow: 1 Select  ->  2 Adjust  ->  3 Clean
#   • live status text + smooth progress bar
#   • background thread so the window never freezes
#   • FFmpeg auto-detected on Windows / Linux / Mac
#
# Install:  pip install customtkinter moviepy==1.0.3 scipy noisereduce playsound==1.2.2
# Run:      python audio_noise_remover_gui.py
# ============================================================

import os
import shutil
import tempfile
import threading
import subprocess
import tkinter as tk

import customtkinter as ctk
from tkinter import filedialog, messagebox

try:                                    # moviepy 1.x
    from moviepy.editor import VideoFileClip
except ImportError:                     # moviepy 2.x moved the module
    from moviepy import VideoFileClip
from scipy.io import wavfile
import noisereduce as nr
from playsound import playsound

# ---------- theme ----------
ctk.set_appearance_mode("dark")
ACCENT      = "#3fd6c0"   # teal  = clean signal
ACCENT_DARK = "#2aa896"
NOISY       = "#f0a63c"   # amber = noisy signal
BG_CARD     = "#1d2a47"
TXT_DIM     = "#8fa0c2"


class NoiseRemoverApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Audio Noise Remover from Video — Alok Sahni")
        self.geometry("640x640")
        self.resizable(False, False)
        self.configure(fg_color="#10182b")

        self.video_path = ""
        self.cleaned_audio_path = ""

        # ---------- header ----------
        ctk.CTkLabel(self, text="NIELIT 'O' LEVEL PROJECT · C INSTITUTE, BIKANER",
                     font=("Segoe UI", 11), text_color=TXT_DIM
                     ).pack(pady=(18, 0))
        ctk.CTkLabel(self, text="Audio Noise Remover from Video",
                     font=("Segoe UI", 26, "bold")
                     ).pack(pady=(2, 14))

        # ---------- card 1 : select ----------
        card1 = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=14)
        card1.pack(fill="x", padx=28, pady=6)
        ctk.CTkLabel(card1, text="STEP 1 · SELECT VIDEO",
                     font=("Segoe UI", 11, "bold"), text_color=ACCENT
                     ).pack(anchor="w", padx=18, pady=(12, 2))
        row = ctk.CTkFrame(card1, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 6))
        self.browse_btn = ctk.CTkButton(
            row, text="Browse…", width=120, corner_radius=8,
            fg_color=ACCENT, hover_color=ACCENT_DARK, text_color="#06251f",
            font=("Segoe UI", 13, "bold"), command=self.browse_file)
        self.browse_btn.pack(side="left")
        self.file_label = ctk.CTkLabel(
            row, text="No file selected  (.mp4 / .mkv)",
            font=("Segoe UI", 12), text_color=TXT_DIM, anchor="w")
        self.file_label.pack(side="left", padx=14, fill="x", expand=True)
        ctk.CTkLabel(card1, text="", height=4).pack()

        # ---------- card 2 : adjust ----------
        card2 = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=14)
        card2.pack(fill="x", padx=28, pady=6)
        ctk.CTkLabel(card2, text="STEP 2 · NOISE PROFILE",
                     font=("Segoe UI", 11, "bold"), text_color=ACCENT
                     ).pack(anchor="w", padx=18, pady=(12, 2))
        self.noise_val = tk.DoubleVar(value=0.5)
        srow = ctk.CTkFrame(card2, fg_color="transparent")
        srow.pack(fill="x", padx=18, pady=(0, 4))
        self.slider = ctk.CTkSlider(
            srow, from_=0.1, to=3.0, number_of_steps=29,
            variable=self.noise_val, progress_color=NOISY,
            button_color=NOISY, button_hover_color="#d18f2c",
            command=self.on_slider)
        self.slider.pack(side="left", fill="x", expand=True)
        self.slider_label = ctk.CTkLabel(srow, text="0.5 s",
                                         font=("Segoe UI", 12, "bold"),
                                         text_color=NOISY, width=48)
        self.slider_label.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(card2,
                     text="The first seconds of the recording are used as the "
                          "noise sample — keep speech out of this region.",
                     font=("Segoe UI", 11), text_color=TXT_DIM,
                     wraplength=540, justify="left"
                     ).pack(anchor="w", padx=18, pady=(0, 12))

        # ---------- card 3 : clean ----------
        card3 = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=14)
        card3.pack(fill="x", padx=28, pady=6)
        ctk.CTkLabel(card3, text="STEP 3 · CLEAN",
                     font=("Segoe UI", 11, "bold"), text_color=ACCENT
                     ).pack(anchor="w", padx=18, pady=(12, 2))
        self.clean_btn = ctk.CTkButton(
            card3, text="✨  Clean Audio", height=46, corner_radius=10,
            fg_color=ACCENT, hover_color=ACCENT_DARK, text_color="#06251f",
            font=("Segoe UI", 16, "bold"), command=self.start_cleaning)
        self.clean_btn.pack(fill="x", padx=18, pady=(4, 8))
        self.progress = ctk.CTkProgressBar(card3, height=10,
                                           progress_color=ACCENT)
        self.progress.set(0)
        self.progress.pack(fill="x", padx=18)
        self.status = ctk.CTkLabel(card3, text="Ready.",
                                   font=("Segoe UI", 12),
                                   text_color=TXT_DIM)
        self.status.pack(pady=(6, 12))

        # ---------- preview row ----------
        prow = ctk.CTkFrame(self, fg_color="transparent")
        prow.pack(fill="x", padx=28, pady=(8, 0))
        self.prev_orig_btn = ctk.CTkButton(
            prow, text="▶  Original Audio", corner_radius=8, height=38,
            fg_color="transparent", border_width=2, border_color=NOISY,
            text_color=NOISY, hover_color="#241f16",
            font=("Segoe UI", 13, "bold"),
            command=self.preview_original_audio)
        self.prev_orig_btn.pack(side="left", expand=True, fill="x",
                                padx=(0, 8))
        self.prev_clean_btn = ctk.CTkButton(
            prow, text="▶  Cleaned Audio", corner_radius=8, height=38,
            fg_color="transparent", border_width=2, border_color=ACCENT,
            text_color=ACCENT, hover_color="#12271f",
            font=("Segoe UI", 13, "bold"),
            command=self.preview_cleaned_audio)
        self.prev_clean_btn.pack(side="left", expand=True, fill="x",
                                 padx=(8, 0))

        ctk.CTkLabel(self,
                     text="Developed by Alok Sahni · Guide: Mr. Tarun Verma",
                     font=("Segoe UI", 10), text_color=TXT_DIM
                     ).pack(side="bottom", pady=10)

    # ---------- helpers ----------
    def on_slider(self, v):
        self.slider_label.configure(text=f"{float(v):.1f} s")

    @staticmethod
    def find_ffmpeg():
        found = shutil.which("ffmpeg")
        if found:
            return found
        windows_default = r"C:\ffmpeg\bin\ffmpeg.exe"
        if os.path.exists(windows_default):
            return windows_default
        return None

    def set_status(self, text, value=None, color=TXT_DIM):
        def _update():
            self.status.configure(text=text, text_color=color)
            if value is not None:
                self.progress.set(value)
        self.after(0, _update)

    def set_buttons(self, enabled):
        state = "normal" if enabled else "disabled"
        for b in (self.browse_btn, self.clean_btn,
                  self.prev_orig_btn, self.prev_clean_btn):
            b.configure(state=state)

    # ---------- actions ----------
    def browse_file(self):
        path = filedialog.askopenfilename(
            title="Open Video File",
            filetypes=[("Video files", "*.mp4 *.mkv")])
        if path:
            self.video_path = path
            mb = os.path.getsize(path) / 1048576
            self.file_label.configure(
                text=f"{os.path.basename(path)}  ({mb:.1f} MB)",
                text_color="#e8edf7")
            self.set_status("File selected — ready to clean.", 0)

    def preview_original_audio(self):
        if not self.video_path:
            messagebox.showwarning("No file",
                                   "Please select a video file first.")
            return
        threading.Thread(target=self._play_original, daemon=True).start()

    def _play_original(self):
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        clip = VideoFileClip(self.video_path)
        try:
            clip.audio.write_audiofile(temp_audio.name,
                                       verbose=False, logger=None)
        except TypeError:
            clip.audio.write_audiofile(temp_audio.name, logger=None)
        clip.close()
        playsound(temp_audio.name)
        temp_audio.close()
        os.unlink(temp_audio.name)

    def preview_cleaned_audio(self):
        if not self.cleaned_audio_path:
            messagebox.showwarning("Not cleaned",
                                   "Please clean the audio first.")
            return
        threading.Thread(target=playsound,
                         args=(self.cleaned_audio_path,),
                         daemon=True).start()

    def start_cleaning(self):
        if not self.video_path:
            messagebox.showwarning("No file",
                                   "Please select a video file first.")
            return
        if self.find_ffmpeg() is None:
            messagebox.showerror(
                "FFmpeg not found",
                "FFmpeg was not found on this system.\n"
                "Install it from ffmpeg.org, or place it at "
                "C:\\ffmpeg\\bin\\ffmpeg.exe")
            return
        self.set_buttons(False)
        threading.Thread(target=self.clean_audio, daemon=True).start()

    def clean_audio(self):
        temp_audio_path = None
        try:
            self.set_status("Step 1/5 · Extracting audio from video…", 0.10)
            clip = VideoFileClip(self.video_path)
            if clip.audio is None:
                clip.close()
                raise RuntimeError("This video has no audio track.")
            temp_audio = tempfile.NamedTemporaryFile(delete=False,
                                                     suffix=".wav")
            temp_audio_path = temp_audio.name
            temp_audio.close()
            try:
                clip.audio.write_audiofile(temp_audio_path,
                                           verbose=False, logger=None)
            except TypeError:
                clip.audio.write_audiofile(temp_audio_path, logger=None)
            clip.close()

            self.set_status("Step 2/5 · Reading audio data…", 0.30)
            rate, data = wavfile.read(temp_audio_path)
            if len(data.shape) == 2:
                data = data.mean(axis=1)

            secs = float(self.noise_val.get())
            n = max(1000, int(rate * secs))
            noise_sample = data[:n]

            self.set_status(f"Step 3/5 · Reducing noise "
                            f"(profile = first {secs:.1f}s)…", 0.50)
            reduced = nr.reduce_noise(y=data, sr=rate, y_noise=noise_sample)

            self.set_status("Step 4/5 · Saving cleaned audio…", 0.70)
            cleaned = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            wavfile.write(cleaned.name, rate, reduced.astype("int16"))
            self.cleaned_audio_path = cleaned.name

            self.set_status("Step 5/5 · Merging audio into video…", 0.85)
            output_video_path = (os.path.splitext(self.video_path)[0]
                                 + "_cleaned.mp4")
            command = [
                self.find_ffmpeg(), "-y",
                "-i", self.video_path,
                "-i", cleaned.name,
                "-c:v", "copy",
                "-map", "0:v:0",
                "-map", "1:a:0",
                output_video_path,
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("FFmpeg failed:\n"
                                   + result.stderr[-400:])

            self.set_status("Done — cleaned video saved. ✓", 1.0, ACCENT)
            self.after(0, lambda: messagebox.showinfo(
                "Success",
                f"Cleaned video saved to:\n{output_video_path}"))

        except Exception as e:
            self.set_status("Error — " + str(e)[:70], 0, "#ff7a7a")
            self.after(0, lambda e=e: messagebox.showerror("Error", str(e)))
        finally:
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.unlink(temp_audio_path)
                except Exception as cleanup_error:
                    print(f"Cleanup error: {cleanup_error}")
            self.after(0, lambda: self.set_buttons(True))


if __name__ == "__main__":
    app = NoiseRemoverApp()
    app.mainloop()
