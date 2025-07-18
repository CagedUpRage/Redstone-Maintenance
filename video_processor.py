import os
import subprocess
import cv2

# === CONFIG ===
video_path = "input.mp4"
output_dir = "output"
frames_dir = os.path.join(output_dir, "frames")
audio_path = os.path.join(output_dir, "audio.wav")
fps_interval = 0.5  # Extract one frame every 2 seconds (0.5 fps)

# === SETUP ===
os.makedirs(frames_dir, exist_ok=True)

# === STEP 1: Extract Frames with FFmpeg ===
def extract_frames(video_path, frames_dir, fps_interval):
    print("[*] Extracting frames...")
    command = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"fps={fps_interval}",
        os.path.join(frames_dir, "frame_%04d.jpg")
    ]
    subprocess.run(command)
    print("[✓] Frames extracted.")

# === STEP 2: Extract Audio with FFmpeg ===
def extract_audio(video_path, audio_path):
    print("[*] Extracting audio...")
    command = [
        "ffmpeg",
        "-i", video_path,
        "-q:a", "0",
        "-map", "a",
        audio_path
    ]
    subprocess.run(command)
    print("[✓] Audio extracted.")

# === STEP 3: Preview Extracted Frames with OpenCV (Optional) ===
def preview_frames(frames_dir):
    print("[*] Previewing frames...")
    frame_files = sorted(os.listdir(frames_dir))
    for file in frame_files:
        path = os.path.join(frames_dir, file)
        img = cv2.imread(path)
        if img is not None:
            cv2.imshow("Frame", img)
            if cv2.waitKey(500) & 0xFF == ord('q'):
                break
    cv2.destroyAllWindows()
# === MAIN ===
if __name__ == "__main__":
    extract_frames(video_path, frames_dir, fps_interval)
    extract_audio(video_path, audio_path)
    preview_frames(frames_dir)

