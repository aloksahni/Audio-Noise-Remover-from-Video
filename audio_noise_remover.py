# ============================================================
# Project Title : Audio Noise Remover from Video
# Developed By  : Alok Sahni
# Course        : NIELIT 'O' Level Project
# Language Used : Python 3.x
# Tools         : Tkinter, MoviePy, SciPy, Noisereduce, FFmpeg
# ============================================================

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
from moviepy.editor import VideoFileClip
from scipy.io import wavfile
import noisereduce as nr
import tempfile
import subprocess
from playsound import playsound


class NoiseRemoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Noise Remover from Video")
        self.root.geometry("500x400")

        self.video_path = ""
        self.cleaned_audio_path = ""

        # Instruction label
        self.label = tk.Label(root, text="Select a video file (.mp4 / .mkv)",
                              font=("Arial", 12))
        self.label.pack(pady=10)

        # Browse button
        self.select_button = tk.Button(root, text="Browse",
                                       command=self.browse_file)
        self.select_button.pack(pady=5)

        # Progress bar
        self.progress = Progressbar(root, orient=tk.HORIZONTAL,
                                    length=300, mode='determinate')
        self.progress.pack(pady=10)

        # Clean Audio button
        self.clean_button = tk.Button(root, text="Clean Audio",
                                      command=self.clean_audio)
        self.clean_button.pack(pady=5)

        # Preview buttons
        self.preview_original_button = tk.Button(
            root, text="Preview Original Audio",
            command=self.preview_original_audio)
        self.preview_original_button.pack(pady=5)

        self.preview_cleaned_button = tk.Button(
            root, text="Preview Cleaned Audio",
            command=self.preview_cleaned_audio)
        self.preview_cleaned_button.pack(pady=5)

    def browse_file(self):
        """Let the user select an .mp4 / .mkv video file."""
        filetypes = [("Video files", "*.mp4 *.mkv")]
        self.video_path = filedialog.askopenfilename(
            title="Open Video File", filetypes=filetypes)
        if self.video_path:
            messagebox.showinfo("Selected",
                                f"File selected:\n{self.video_path}")

    def preview_original_audio(self):
        """Extract and play the original (noisy) audio."""
        if not self.video_path:
            messagebox.showwarning("No file",
                                   "Please select a video file first.")
            return
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        clip = VideoFileClip(self.video_path)
        clip.audio.write_audiofile(temp_audio.name, verbose=False, logger=None)
        clip.close()
        playsound(temp_audio.name)
        temp_audio.close()
        os.unlink(temp_audio.name)

    def preview_cleaned_audio(self):
        """Play the cleaned audio (after Clean Audio has been run)."""
        if not self.cleaned_audio_path:
            messagebox.showwarning("Not cleaned",
                                   "Please clean the audio first.")
            return
        playsound(self.cleaned_audio_path)

    def clean_audio(self):
        """Main routine: extract audio -> reduce noise -> re-merge with video."""
        if not self.video_path:
            messagebox.showwarning("No file",
                                   "Please select a video file first.")
            return

        self.progress['value'] = 10
        self.root.update_idletasks()

        temp_audio_path = None
        try:
            # 1. Extract audio from the video into a temp WAV file
            clip = VideoFileClip(self.video_path)
            temp_audio = tempfile.NamedTemporaryFile(delete=False,
                                                     suffix=".wav")
            temp_audio_path = temp_audio.name
            temp_audio.close()
            clip.audio.write_audiofile(temp_audio_path,
                                       verbose=False, logger=None)
            clip.close()

            self.progress['value'] = 30
            self.root.update_idletasks()

            # 2. Read WAV; convert stereo to mono if needed
            rate, data = wavfile.read(temp_audio_path)
            if len(data.shape) == 2:
                data = data.mean(axis=1)

            # 3. Use the first 5000 samples as the noise profile
            noise_sample = data[:5000]

            # 4. Reduce noise (spectral gating)
            reduced_noise = nr.reduce_noise(y=data, sr=rate,
                                            y_noise=noise_sample)

            # 5. Save cleaned audio as 16-bit WAV
            cleaned_audio_file = tempfile.NamedTemporaryFile(delete=False,
                                                             suffix=".wav")
            wavfile.write(cleaned_audio_file.name, rate,
                          reduced_noise.astype("int16"))
            self.cleaned_audio_path = cleaned_audio_file.name

            self.progress['value'] = 70
            self.root.update_idletasks()

            # 6. Re-merge cleaned audio into the video via FFmpeg
            output_video_path = (os.path.splitext(self.video_path)[0]
                                 + "_cleaned.mp4")
            ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"
            command = [
                ffmpeg_path, "-y",
                "-i", self.video_path,
                "-i", cleaned_audio_file.name,
                "-c:v", "copy",
                "-map", "0:v:0",
                "-map", "1:a:0",
                output_video_path
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                print("FFmpeg Error:", result.stderr)

            self.progress['value'] = 100
            self.root.update_idletasks()

            messagebox.showinfo(
                "Success",
                f"Cleaned video saved to:\n{output_video_path}")

        except Exception as e:
            messagebox.showerror("Error", str(e))

        finally:
            # Delete the temporary extracted-audio file
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.unlink(temp_audio_path)
                except Exception as cleanup_error:
                    print(f"Cleanup error: {cleanup_error}")


if __name__ == "__main__":
    root = tk.Tk()
    app = NoiseRemoverApp(root)
    root.mainloop()
