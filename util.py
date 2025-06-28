from datetime import datetime
import os
import re
import subprocess
from enum import Enum

VIDEO_CONTAINERS = [".mp4", ".mov", ".mkv", ".avi", ".flv", ".webm", ".3gp"]
AUDIO_CONTAINERS = [".mp3", ".wav", ".aiff", ".flac", ".m4a", ".ogg", ".mka"]

class GpuDevice(Enum):
  CPU = 0 # CPU only, no hardware acceleration
  QSV = 1 # Intel QSV video
  CUDA = 2 # Nvidia NVENC / NVDEC
  AMF = 3 # AMD AMF (AMD GPU on Windows ONLY)
  VAAPI = 4 # VAAPI (Linux ONLY, AMD or Intel GPU)
  METAL = 5 # macOS ONLY

# based on GPU device, returns the associated decoder and encoder strings for ffmpeg
FFMPEG_ENCODER_STRINGS: dict[GpuDevice, tuple[str, str]] = {
  GpuDevice.CPU: ("", ""),
  GpuDevice.QSV: ("qsv", "h264_qsv"),
  GpuDevice.CUDA: ("cuda", "h264_nvenc"),
  GpuDevice.AMF: ("dxva2", "h264_amf"),
  GpuDevice.VAAPI: ("vaapi", "h264_vaapi"),
  GpuDevice.METAL: ("videotoolbox", "h264_videotoolbox")
}

# general validate file extension but defaults to video
def validate_file_extension(filename: str, valid_extensions: list[str]=VIDEO_CONTAINERS) -> bool:
  _, extension = os.path.splitext(filename)
  return extension.lower() in valid_extensions

# validate file extension for audio files, calls `validate_file_extension`
def validate_audio_extension(filename: str) -> bool:
  return validate_file_extension(filename, AUDIO_CONTAINERS)

# TODO: save logs to file
def log(str: str, level: str="I", show_timestamp: bool=True):
  if show_timestamp:
    print(f"[{level}] [{datetime.now().strftime('%m-%d-%y %H:%M:%S')}] {str}")
  else:
    print(f"[{level}] {str}")

def clean_file_name(filename: str, replacement_text: str="") -> str:
  # remove or replace invalid characters
  filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement_text, filename)
  
  # remove leading and trailing spaces and periods
  filename = filename.strip(' .')

  # remove reserved names (Windows)
  reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "LPT1", "LPT2", "LPT3"]
  if filename.upper() in reserved_names:
    filename = replacement_text + filename

  # remove names starting with a space or dot
  if filename.startswith(" ") or filename.startswith("."):
    filename = replacement_text + filename

  # remove names ending with a space or dot
  if filename.endswith(" ") or filename.endswith("."):
    filename = filename[:-1] + replacement_text

  return filename

# source: https://stackoverflow.com/a/3844467
# get length of video or audio file using ffmpeg in seconds
def get_video_length(filename: str) -> float:
  result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
  return float(result.stdout)

# replaces placeholders in the format `%tag` with corresponding keyword arguments.
def format_string(template: str, **kwargs) -> str:
  # match placeholders like %tag
  pattern = re.compile(r"%\w+")
  
  def replace_match(match):
    key = match.group()[1:] # remove leading '%'
    return kwargs.get(key, match.group()) # replace if key exists, else keep original
  
  return pattern.sub(replace_match, template)