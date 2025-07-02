from util import GpuDevice

# ---
# scrape / playwright related constants
# ---

# base url of reddit. probably don't need to change
BASE_URL = "https://old.reddit.com"

# which subreddit to scrape. text-based recommended
SUBREDDIT = "/r/AskReddit"

# gather only post body, or only comments?
# gathering post body only is good for story-type subreddits, comments only is good for asking-type subreddits
SCRAPE_ONLY_POST = False

# skip not safe for work posts (highly recommended)
SKIP_NSFW = True

# ---
# video related constants
# ---

# how long to make the crossfade in seconds
XFADE_LENGTH = 1

# multiplier to speed up / down audio retaining pitch, normal = 1.0, faster = 1.5
SPEECH_SPEED = 1.5

# min and max acceptable video length in seconds, set either / both to -1 to disable
MIN_VIDEO_LENGTH = 20
MAX_VIDEO_LENGTH = 180

# which device to use for ffmpeg encode/decode
FFMPEG_ACCELERATION: GpuDevice = GpuDevice.CPU

# ffmpeg video bitrate
FFMPEG_VIDEO_BITRATE = "10M"

# Coqui TTS model string. List available models using TTS().list_models()
TTS_MODEL = "tts_models/en/ljspeech/vits"

# idea: make each video have a unique title
# supported tags: %title %date %index %uuid %randnum %mystr
TITLE_FORMAT = "%title #reddit #shorts %index %date"
# content format supported tags: %title %content
CONTENT_FORMAT = "%title %content"

# how long each mini clip split should be
CLIP_LENGTH = 5

# desired resolution of mini clip splits
WIDTH = 1080
HEIGHT = 1920

# desired frame rate of mini clip splits
FPS = 60

# ---
# final render related constants
# ---

# base url of gentle forced aligner
GENTLE_URL = "http://localhost:32768"

# start and end indices of videos to render
# to render all, set start index to 0 and end index to -1
COMMENTS_START_INDEX = 0
COMMENTS_END_INDEX = -1

# path of the content you want to use
COMMENTS_FILE_PATH = "content/INSERT-FILE-NAME-HERE.json"
