import json
import re
from datetime import datetime
from uuid import uuid4
from random import randint, choice
from TTS.api import TTS
import os
from sys import exit as sysexit

from util import log, validate_audio_extension, validate_file_extension, clean_file_name, format_string, GpuDevice
from render_video import render_video
from consts import TITLE_FORMAT, CONTENT_FORMAT, FFMPEG_ACCELERATION, TTS_MODEL, GENTLE_URL, COMMENTS_START_INDEX, COMMENTS_END_INDEX, COMMENTS_FILE_PATH

# format title with supported tags by calling `format_string` internally
def format_title(title: str, index: int = 0, mystr: str = "") -> str:
  cur_date = datetime.now().strftime("%m-%d-%y")
  random_uuid = str(uuid4())
  random_num = randint(1000, 9999)
  return format_string(TITLE_FORMAT, title=title, date=cur_date, index=str(index), uuid=random_uuid, randnum=str(random_num), mystr=mystr)

# render all videos in the specified json file
def render_all_videos(json_file: str, gentle_url: str, start_index: int=0, end_index: int=-1):
  comments = [] # list with dict {title, comment_text}
  with open(json_file.strip(), "r") as f:
    comments = json.load(f)
  
  log(f"Loading video and audio pool")
  try:
    video_pool = ["./video/splits/" + video for video in os.listdir("./video/splits") if validate_file_extension(video)]
    if len(video_pool) == 0:
      raise FileNotFoundError()
  except FileNotFoundError:
    log(f"No background videos found at video/splits/, create video/ folder, add background clips, and preprocess into splits first", "F")
    sysexit(1)
  audio_pool = ["./audio/" + audio for audio in os.listdir("./audio") if validate_audio_extension(audio)]
  if len(audio_pool) == 0:
    log(f"No background audio found in audio/, videos will not have background music", "W")
  
  # initialize TTS engine, using cuda if available, otherwise only CPU supported
  log("Initializing TTS engine")
  if FFMPEG_ACCELERATION == GpuDevice.CUDA:
    log("Using CUDA for TTS, importing torch...")
    import torch
    if (torch.cuda.is_available()):
      tts = TTS(TTS_MODEL).to("cuda")
    else:
      log("CUDA was not available, falling back to CPU", level="W")
      tts = TTS(TTS_MODEL).to("cpu")
  else:
    log("Using CPU for TTS")
    tts = TTS(TTS_MODEL).to("cpu")
  log("Initialized TTS engine")

  end_index = end_index if end_index != -1 and end_index < len(comments) else len(comments)
  log(f"Rendering out {end_index - start_index} videos")

  num_rendered = 0
  for i in range(start_index, end_index):
    num_rendered += 1
    comment = comments[i]
    title = clean_file_name(format_title(comment["title"], i))
    content = format_string(CONTENT_FORMAT, title=title, content=comment["comment_text"])
    log(f"Rendering video {num_rendered}/{end_index - start_index}: '{title}'")
    try:
      render_video(gentle_url, content, tts, video_pool, choice(audio_pool), title)
    except Exception as ex:
      log(f"An error occurred trying to render video #{i} - {title}", "E")
      print(ex)
  
  log("Completed rendering all videos!")

if __name__ == "__main__":
  render_all_videos(COMMENTS_FILE_PATH, GENTLE_URL, COMMENTS_START_INDEX, COMMENTS_END_INDEX)