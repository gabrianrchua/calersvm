import requests
from datetime import timedelta
from TTS.api import TTS
from pathlib import Path
from math import ceil
import subprocess
import os
import random

from util import log, validate_file_extension, get_video_length
from content_filter import clean_text
from normalize_videos import CLIP_LENGTH

XFADE_LENGTH = 1
SPEECH_SPEED = 1.5 # speed up / down audio retaining pitch, normal = 1.0, faster = 1.5
# min and max acceptable video length in seconds, set to -1 to disable
MIN_VIDEO_LENGTH = 20
MAX_VIDEO_LENGTH = 180

def format_timestamp(seconds: int) -> str:
  td = timedelta(seconds=seconds)
  millis = int(td.microseconds / 1000)
  return f"{td.seconds // 3600:02}:{(td.seconds % 3600) // 60:02}:{td.seconds % 60:02},{millis:03}"

# returns (srt_content, content_length)
def create_srt(word_timings: list[tuple[int, str]]) -> tuple[str, int]:
  srt_content = ""
  for i in range(len(word_timings)):
    start_time = word_timings[i][0]
    end_time = word_timings[i+1][0] if i+1 < len(word_timings) else start_time + 1
    srt_content += f"{i+1}\n{format_timestamp(start_time)} --> {format_timestamp(end_time)}\n{word_timings[i][1]}\n\n"
  return (srt_content, ceil(word_timings[-1][0] + 1))

# select a specified number of videos randomly until exhausted, then repeat
def select_videos(video_files: list[str], num_videos: int) -> list[str]:
  if len(video_files) == 0:
    raise ValueError("No videos were provided in video_files, please place videos in video/ folder and run the video normalizer")
  
  selected_items = []
  available_items = video_files[:]  # Copy of the original list
  
  while len(selected_items) < num_videos:
    if not available_items:
      available_items = video_files[:]  # Refill the list when it runs out
    
    to_pick = min(num_videos - len(selected_items), len(available_items))
    chosen = random.sample(available_items, to_pick)  # Pick unique items
    selected_items.extend(chosen)
    
    # Remove selected items from available pool
    for item in chosen:
      available_items.remove(item)

  return selected_items

# example:
# ffmpeg -i video/bkg.mp4 -i work/speech.wav -map 0:v -map 1:a -vf "subtitles=work/sub.srt:force_style='Fontsize=36,Alignment=10,Fontname=Roboto Black'" -t 11 -b:v 8M -b:a 192k work/fin.mp4
# enhanced:
# ffmpeg -i test/out2.wav -i "audio/El Pesaj y el Moro - Cumbia Deli.mp3" -i "video/splits/screen-20250319-105225_15.mp4" -i "video/splits/screen-20250315-125016_250.mp4" -i "video/splits/screen-20250319-104529_130.mp4" -filter_complex "[2:v][3:v]xfade=transition=fade:duration=1:offset=4[v23];[v23][4:v]xfade=transition=fade:duration=1:offset=8[v234];[v234]subtitles=test/sub.srt:force_style='Fontsize=30,Alignment=10,Fontname=Roboto Black,Outline=2,Shadow=4'[vout];[0:a][1:a]amix=inputs=2:duration=shortest:weights=5 1[aout]" -map "[vout]" -map "[aout]" test/final.mp4
def build_ffmpeg_command(video_files: list[str], speech_file: str, transcript_file: str, video_length: int, video_title: str, audio_file: str | None) -> list[str]:
  # stream order:
  # 0: speech_file
  # 1: audio_file <-- optional
  # 1+ or 2+: video_files

  num_videos = len(video_files)
  if num_videos == 0:
    raise ValueError("video_files list must have at least one background video")
  
  cmd = ["ffmpeg"]

  cmd.append("-i")
  cmd.append(f'"{speech_file}"')

  # background audio file
  if audio_file is not None:
    cmd.append("-i")
    cmd.append(f'"{audio_file}"')

  # background video clips
  for file in video_files:
    cmd.append("-i")
    cmd.append(f'"{file}"')

  # build complex filter
  cmd.append("-filter_complex")

  # video_files has 1 video --> no xfade, pass video feed directly
  # video_files has 2+ videos --> xfade pairs until last, then into vout
  filter_complex = ""
  semi_vout_name = ""
  aout_name = ""

  if num_videos == 1:
    semi_vout_name = "[1:v]" if audio_file is None else "[2:v]"
  else:
    offset_amount = CLIP_LENGTH - XFADE_LENGTH
    for i in range(num_videos - 1):
      #video = video_files[i]
      stream_index = i + 1 if audio_file is None else i + 2
      
      prev_stream = ""
      if i == 0:
        prev_stream = f"[{stream_index}:v]"
      else:
        prev_stream = f"[v{stream_index - 1}]"
      
      out_name = "[vfin]" if i + 2 == num_videos else f"[v{stream_index}]"

      filter_complex += f"{prev_stream}[{stream_index + 1}:v]xfade=transition=fade:duration={XFADE_LENGTH}:offset={offset_amount * (i + 1)}{out_name};"

    semi_vout_name = "[vfin]"
  
  filter_complex += f"{semi_vout_name}subtitles={transcript_file}:force_style='Fontsize=30,Alignment=10,Fontname=Roboto Black,Outline=2,Shadow=4'[vout];"
  
  if audio_file is not None:
    filter_complex += "[0:a][1:a]amix=inputs=2:duration=shortest:weights=5 1[aout]"
    aout_name = "[aout]"
  else:
    aout_name = "[0:a]"
  
  cmd.append(f'"{filter_complex}"')
  cmd.extend(["-map", "\"[vout]\"", "-map", f'"{aout_name}"', "-t", str(video_length), "-c:v", "libx264", "-c:a", "aac", "-f", "mp4", "-y", f"\"./out/{video_title}.mp4\""])

  return cmd

def build_ffmpeg_audio_speed_command(speech_file: str, output_file_name: str, rate: float = SPEECH_SPEED) -> None:
  cmd = ["ffmpeg", "-i", f'"{speech_file}"', "-af", f"atempo={rate}", "-y", f'"{output_file_name}"']
  return cmd

def render_video(gentle_url: str, content: str, tts: TTS, video_files: list[str], audio_file: str | None, video_title: str, censor_text: bool = True) -> None:
  # create working directory if not exists
  Path("./work").mkdir(parents=True, exist_ok=True)

  # apply content filter if requested
  if censor_text:
    content = clean_text(content)

  # write transcript file
  with open("./work/speech.txt", "w") as f:
    f.write(content)

  # generate speech using provided TTS
  log("Generating speech using TTS")
  #tts = TTS("tts_models/en/ljspeech/vits").to("cpu")
  tts.tts_to_file(text=content, file_path="./work/speech_pre.wav")
  log("Completed generating speech")

  # apply audio speed mulitplier with ffmpeg
  log(f"Applying audio multiplier of {SPEECH_SPEED}x")
  cmd = build_ffmpeg_audio_speed_command("./work/speech_pre.wav", "./work/speech.wav", SPEECH_SPEED)
  log("Calling ffmpeg: " + " ".join(cmd))
  try:
    subprocess.run(" ".join(cmd), cwd=os.getcwd(), shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  except subprocess.CalledProcessError as e:
    log("Error applying audio speed with ffmpeg: " + str(e), "E")
    print(e.output)
    return

  # check audio length and reject if too long / short
  speech_length = get_video_length("./work/speech.wav")
  if (MIN_VIDEO_LENGTH != -1 and speech_length < MIN_VIDEO_LENGTH) or (MAX_VIDEO_LENGTH != -1 and speech_length > MAX_VIDEO_LENGTH):
    log(f"Rejected, video length of {speech_length}s was outside desired length of {MIN_VIDEO_LENGTH}-{MAX_VIDEO_LENGTH}s")
    return

  # align text using gentle
  # open files in binary mode
  with open("./work/speech.wav", "rb") as speech_file, open("./work/speech.txt", "r") as transcript_file:
    files = {
      "audio": ("speech.wav", speech_file, "audio/wav"),
      "transcript": ("speech.txt", transcript_file, "text/plain"),
    }
    request_url = gentle_url + "/transcriptions?async=false"
    log("Aligning speech text using " + request_url)
    response = requests.post(request_url, files=files)
    log("Completed aligning text")

  aligned_words = response.json()["words"]
  words_timing = [] # list of tuple (start_time, word)

  for word in aligned_words:
    # if failed to align, just skip word
    if "start" in word and "word" in word:
      words_timing.append((word["start"], word["word"]))

  # generate SRT for subtitles
  log("Generating SRT")
  srt_text, vid_length = create_srt(words_timing)

  with open("./work/sub.srt", "w", encoding="utf-8") as f:
    f.write(srt_text)

  log("SRT saved")
  
  # build ffmpeg command and call
  num_videos_needed = ceil(vid_length / (CLIP_LENGTH - XFADE_LENGTH))
  cmd = build_ffmpeg_command(select_videos(video_files, num_videos_needed), "./work/speech.wav", "./work/sub.srt", vid_length, video_title, audio_file)
  Path("./out").mkdir(parents=True, exist_ok=True)
  log("Calling ffmpeg: " + " ".join(cmd))
  try:
    subprocess.run(" ".join(cmd), cwd=os.getcwd(), shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  except subprocess.CalledProcessError as e:
    log("Error exporting video with ffmpeg: " + str(e), "E")
    print(e.output)
    return

  log("Done! Exported video to " + f"./out/{video_title}.mp4")

if __name__ == "__main__":
  video_pool = ["./video/splits/" + video for video in os.listdir("./video/splits") if validate_file_extension(video)]
  render_video("http://localhost:32768", "Hello world! This is a test! It is working very good. idk man idc what's going on with 2/3rds of the population. You know, this is a very long piece of text. I wonder how long the resuling video will be then. I don't really know man. I guess we'll have to see.", TTS("tts_models/en/ljspeech/vits").to("cpu"), video_pool, "./audio/Traverse The Sky - Asher Fulero.mp3", "faster")