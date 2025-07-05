from datetime import datetime
import os
import re
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any, TextIO
import atexit

from consts import LOG_VERBOSITY

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

class Log:
  _log_file: TextIO | None = None

  _log_levels: dict[str, int] = {
    "verbose": 0,
    "info": 1,
    "warn": 2,
    "error": 3,
    "fatal": 4,
  }

  @staticmethod
  def _init_logger() -> None:
    if Log._log_file is not None:
      return
    
    Path("./logs").mkdir(parents=True, exist_ok=True)
    log_path: str = f"./logs/run-{datetime.now().strftime('%m-%d-%y-%H-%M-%S')}.txt"
    log_file = open(log_path, "a")
    atexit.register(log_file.close)
  
  @staticmethod
  def _should_log(level: str) -> bool:
    # should only log with level >= configured LOG_VERBOSITY, with default verbosity of "verbose"
    return Log._log_levels.get(level, 99) >= Log._log_levels.get(LOG_VERBOSITY, 0)

  @staticmethod
  def _log(message: Any, level: str="verbose", show_timestamp: bool=True) -> None:
    if not Log._should_log(level):
      return

    if Log._log_file is None:
      Log._init_logger()

    timestamp = datetime.now().strftime('%m-%d-%y %H:%M:%S')
    log_header = f"[{level[0].upper()}] [{timestamp}] " if show_timestamp else f"[{level[0].upper()}] "
    full_message = f"{log_header}{message}"

    print(full_message)

    if Log._log_file is not None:
      Log._log_file.write(full_message + "\n")
      Log._log_file.flush()
  
  @staticmethod
  def verbose(message: Any, show_timestamp: bool = True) -> None:
    Log._log(message, "verbose", show_timestamp)

  @staticmethod
  def info(message: Any, show_timestamp: bool = True) -> None:
    Log._log(message, "info", show_timestamp)

  @staticmethod
  def warn(message: Any, show_timestamp: bool = True) -> None:
    Log._log(message, "warn", show_timestamp)

  @staticmethod
  def error(message: Any, show_timestamp: bool = True) -> None:
    Log._log(message, "error", show_timestamp)

  @staticmethod
  def fatal(message: Any, show_timestamp: bool = True) -> None:
    Log._log(message, "fatal", show_timestamp)

# general validate file extension but defaults to video
def validate_file_extension(filename: str, valid_extensions: list[str]=VIDEO_CONTAINERS) -> bool:
  _, extension = os.path.splitext(filename)
  return extension.lower() in valid_extensions

# validate file extension for audio files, calls `validate_file_extension`
def validate_audio_extension(filename: str) -> bool:
  return validate_file_extension(filename, AUDIO_CONTAINERS)

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

# insert hardware acceleration components to ffmpeg command list
def add_hwaccel_to_ffmpeg_command(command: list[str], device: GpuDevice = GpuDevice.CPU) -> list[str]:
  if device == GpuDevice.CPU:
    return command

  if (device in FFMPEG_ENCODER_STRINGS):
    hwaccel, codec = FFMPEG_ENCODER_STRINGS[device]
    command.insert(1, "-hwaccel")
    command.insert(2, hwaccel)
    command.insert(len(command) - 1, "-c:v")
    command.insert(len(command) - 1, codec)
  
  return command
