# Completely automated low effort reddit short form video maker (CALERSVM)

**Important: This project is a work in progress!**

CALERSVM is a Python toolkit that automatically scrapes content from Reddit using Playwright and produces dozens of completely automated short form videos using Coqui TTS, Gentle, and `ffmpeg`. All you need to provide is a set of background videos (think Subway Surfers) and optionally some background audio tracks.

## Set Up

1. Clone or download this repo

2. (Recommended) Download and install Anaconda and set up Python 3.11

   - Alternatively, download Python 3.11 directly and set up a venv (not configured here)

```
conda create -n "calersvm" python=3.11
conda activate calersvm
```

3. Install project requirements using pip

```
pip install -r requirements.txt
```

4. Install Playwright Chromium browser

```
playwright install-deps
playwright install chromium
```

5. Install `ffmpeg` if you don't have it already

<details>
<summary>Linux: Debian and derivatives</summary>
<pre>
sudo apt install ffmpeg
</pre>
</details>

<details>
<summary>Linux: RHEL, Fedora, CentOS</summary>
<pre>
sudo dnf install ffmpeg
</pre>
</details>

<details>
<summary>Linux: Arch</summary>
<pre>
sudo pacman -S ffmpeg
</pre>
</details>

<details>
<summary>Windows</summary>
<a href="https://www.ffmpeg.org/download.html#build-windows">www.ffmpeg.org</a>
</details>

<details>
<summary>macOS: Homebrew</summary>
<pre>
brew install ffmpeg
</pre>
</details>

<details>
<summary>macOS: Static builds</summary>
<a href="https://www.ffmpeg.org/download.html#build-mac">www.ffmpeg.org</a>
</details>

6. Install Docker if you don't have it already

   - If on Linux, recommended to use [Docker Engine](https://docs.docker.com/engine/install/)
   - If on macOS or Windows, use [Docker Desktop](https://docs.docker.com/desktop/)

7. (Optional, highly recommended) Configure hardware accelerated video encoding and decoding in `consts.py`

   - This will be used by `ffmpeg` and can drastically reduce the time it takes to render a video. The total time can easily be cut in half per video!
   - In `render_video.py`, specify your applicable `GpuDevice` based on your hardware and operating system.
     - `GpuDevice.CPU`: Disables GPU accelerated video encode/decode. The slowest option but is (basically) guaranteed to work on any system. Try any other option if possible.
     - `GpuDevice.QSV`: Intel Quick Sync Video. Use if you have an Intel processor with an iGPU or an Intel Arc GPU on Windows or Linux.
     - `GpuDevice.CUDA`: Nvidia NVENC / NVDEC. Use if you have an Nvidia processor on Windows or Linux.
       - _Bonus: if you use CUDA, Coqui TTS will also use your Nvidia card, speeding up speech generation._
     - `GpuDevice.AMF`: AMD Advanced Media Framework. Use if you have an AMD GPU on Windows.
     - `GpuDevice.VAAPI`: Video Acceleration API. Use if you have an Intel or AMD GPU on Linux.
     - `GpuDevice.METAL`: Videotoolbox on Mac. Use if you have any Mac computer.

| GPU/OS | Windows | Linux   | macOS   |
| ------ | ------- | ------- | ------- |
| Intel  | `QSV`   | `QSV`   | `METAL` |
| Nvidia | `CUDA`  | `CUDA`  | `METAL` |
| AMD    | `AMF`   | `VAAPI` | `METAL` |
| No GPU | `CPU`   | `CPU`   | `CPU`   |

8. (Optional) Configure content filter

   - Edit rules in `content_filter.py`
   - Add rules in the format `("*badword*", "substitution")`
   - Asterisk (`*`) characters in the pattern are wildcards and match any character. They can go at the beginning, end, or both!
   - If no rules are specified, the `better_profanity` package will still change any profanities to `"beep"`, but no custom substitutions will be made.

## Usage

1. Record and copy (ideally vertical) background video clips into a folder called `video/`

   - Vertical video clips will be squished into 9:16 (all content retained)
   - Horizontal video clips will be cropped into 9:16 (some content lost on the sides)
   - Ideas: Subway Surfers, Geometry Dash, Jetpack Joyride...
   - Each video will have several 5-second (by default) clips extracted from these videos.

2. (Optional but recommended) Record or download background audio / music and place in a folder called `audio/`

   - Each video will have one randomly selected to play in the background.

3. Split and normalize video clips into 5-second (by default) clips using `normalize_videos.py`

   - This uses `ffmpeg` and may take a long time.
   - You can safely add new videos to `video/` and run this script again. It will only split new video files.

```
python normalize_videos.py
```

4. Scrape Reddit with `scrape.py`.

   - This uses Playwright to get the all the top comments from all the threads on the first page.
   - You can configure which subreddit to use by editing `SUBREDDIT=` in `consts.py`.
     - Example: `SUBREDDIT = "/r/mysubreddit"`
   - Not all subreddits are supported or tested, and text-only ones are best to use.
   - This will output a filename where the scraped content is saved. It'll be in the format `content/comments-mm-dd-yy-hh-mm-ss.json`.
   - Copy this file name into `COMMENTS_FILE_PATH=` in `consts.py` so the system knows which file to use during rendering.
     - Example: `COMMENTS_FILE_PATH = "content/comments-06-25-25-21-39-09.json"`

```
python scrape.py
```

5. Run [Gentle](https://github.com/strob/gentle) in Docker.

   - Gentle is the forced aligner I use to align the text to the TTS audio. It allows us to have subtitles on screen at the right time.
   - You may need to update the port in the `GENTLE_URL=` field in `consts.py` to `8765`, however I have found that Gentle actually runs on port `32768`.
     - Example: `GENTLE_URL = "http://localhost:32768"`
   - You may also be able to run it on bare metal or as the standalone Mac application (untested). Be sure to update the URL.

```
docker run -P lowerquality/gentle
```

6. Configure `consts.py` with which content to use and how many to render out.

   - This will be used in the next step when you run `render_all_video.py`
   - Example:
     - `COMMENTS_START_INDEX = 0`
     - `COMMENTS_END_INDEX = -1`
     - `COMMENTS_FILE_PATH = "content/comments-06-25-25-21-39-09.json"`
   - You might want to try with 10-20 videos first to make sure it works. Set the start and end indices to something like 0 and 20.
   - If you haven't already, add the file path to the comments file you want to render.

7. Render all videos using `render_all_video.py`!

   - This uses `ffmpeg` to piece together several video clips, your background audio, generated TTS audio, and aligned subtitles.
   - This will take a very long time! Leave you computer running and grab something to eat. Or multiple things to eat...
   - In my experience, each video takes about 3-5 minutes to complete on CPU (i5-8350U). Each scrape yields ~2000 comments. Not all of them are rendered (too long, too short), so I estimate on CPU this might take several days.
   - When you're ready to render ALL videos in the content file, set the end index in `COMMENTS_END_INDEX` in `consts.py` to `-1`

```
python render_all_video.py
```
