from pathlib import Path
import subprocess
import os
from sys import exit as sysexit

from util import log, validate_file_extension, get_video_length, add_hwaccel_to_ffmpeg_command
from consts import CLIP_LENGTH, FPS, WIDTH, HEIGHT, FFMPEG_ACCELERATION

# widescreen (crop sides): ffmpeg -i screen-20250315-125016.mp4 -r 60 -vf 'crop=ih/16*9:ih,scale=1080:1920' ../video/bkg0.mp4
# naive scale: ffmpeg -i tmp.mp4 -r 60 -vf 'scale=1080:1920' bkg0.mp4

def render_video_split(filename: str, start_time: int, output_filename: str) -> None:
  try:
    # try widescreen crop first (better result)
    command = add_hwaccel_to_ffmpeg_command(["ffmpeg", "-ss", str(start_time), "-i", filename, "-r", str(FPS), "-t", str(CLIP_LENGTH), "-vf", f"crop=ih/16*9:ih,scale={WIDTH}:{HEIGHT}", output_filename], FFMPEG_ACCELERATION)
    subprocess.run(command, check=True)
  except subprocess.CalledProcessError as ex1:
    # try naive scale if fails
    try:
      # first, remove empty failed container
      try:
        os.remove(output_filename)
      except FileNotFoundError:
        # did not get created at all <-- okay
        pass
      # then run naive scale (simple squish)
      command = add_hwaccel_to_ffmpeg_command(["ffmpeg", "-ss", str(start_time), "-i", filename, "-r", str(FPS), "-t", str(CLIP_LENGTH), "-vf", f"scale={WIDTH}:{HEIGHT}", output_filename], FFMPEG_ACCELERATION)
      subprocess.run(command, check=True)
    except subprocess.CalledProcessError as ex2:
      log(f"Failed to split video '{filename}': {str(ex1)} {str(ex2)}", "E")
      return
  log(f"Successfully exported {filename} to {output_filename}")

def normalize_all():
  videos = []
  try:
    videos = os.listdir("./video")
  except FileNotFoundError:
    log("videos/ folder does not exist, please create the folder and place background videos there", "F")
    sysexit(1)

  videos = [video for video in videos if validate_file_extension(video)]

  log(f"Beginning processing of {len(videos)} videos: {videos}")

  # extract splits that already exist and skip later
  Path("./video/splits").mkdir(parents=True, exist_ok=True)
  existing_splits = os.listdir("./video/splits")
  existing_splits = list(set([video[:video.rfind("_")] + ".mp4" for video in existing_splits if video.rfind("_") != -1]))

  num_skipped = 0
  num_processed = 0

  # process all videos
  for i, video in enumerate(videos):
    log(f"Processing video {i+1}/{len(videos)}: {video}")
    if (video in existing_splits):
      log(f"Skipping, splits already exist for this video")
      num_skipped += 1
      continue
    video_name, _ = os.path.splitext(video)
    for j in range(CLIP_LENGTH, int(get_video_length("./video/" + video)) - CLIP_LENGTH, CLIP_LENGTH):
      render_video_split("./video/" + video, j, f"./video/splits/{video_name}_{j}.mp4")
    num_processed += 1
  
  log(f"Completed processing videos! Processed {num_processed} and skipped {num_skipped}")

if __name__ == "__main__":
  normalize_all()