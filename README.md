# Completely automated low effort reddit short form video maker (CALERSVM)

**Important: This project is a work in progress!**

CALERSVM is a Python toolkit that automatically scrapes content from Reddit using Playwright and produces dozens of completely automated short form videos using Coqui TTS, Gentle, and `ffmpeg`. All you need to provide is a set of background videos (think Subway Surfers) and optionally some background audio tracks.

## Set Up

1. Clone this repo

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

7. (Optional) Configure content filter

   - Edit rules in `content_filter.py`
   - Add rules in the format `("*badword*", "substitution")`
   - Asterisk (`*`) characters in the pattern are wildcards and match any character. They can go at the beginning, end, or both!
   - If no rules are specified, the `better_profanity` package will still make profanities "\*\*\*\*", but no neat substitutions will be made.

## Usage

1. Record and copy (ideally vertical) background video clips into a folder called `video/`.

   - Vertical video clips will be squished into 9:16 (all content retained)
   - Horizontal video clips will be cropped into 9:16 (some content lost on the sides)
   - Ideas: Subway Surfers, Geometry Dash, Jetpack Joyride...
   - Each video will have several 5-second (by default) clips extracted from these videos.

2. (Optional but recommended) Record or download background audio / music and place in a folder called `audio/`.

   - Each video will have one randomly selected to play in the background.

3. Split video clips into 5-second (by default) clips using `prevideo.py`.

   - This uses `ffmpeg` and may take a long time.
   - You can safely add new videos to `video/` and run this script again. It will only split new video files.

```
python prevideo.py
```

4. Scrape Reddit with `scrape.py`.

   - You can configure which subreddit to use by supplying an argument at the bottom where `scrape_reddit()` is called. Example: `scrape_reddit("/r/mysubreddit")`.
   - Not all subreddits are supported, and text-only ones are best to use.
   - This will output a filename where the scraped content is saved. **Take note of this since we will need this later.** It'll be in the format `content/comments-mm-dd-yy-hh-mm-ss.json`

```
python scrape.py
```

5. Run [Gentle](https://github.com/strob/gentle) in Docker.

   - Gentle is the forced aligner I use to align the text to the TTS audio. It allows us to have subtitles on screen at the right time.
   - You may need to update the port at the bottom of `render_video.py` to `8765`, however I have found that Gentle actually runs on port `32768`.

```
docker run -P lowerquality/gentle
```

6. Configure `render_all_video.py` with which content to use and how many to render out

   - Change the call to `render_all_videos()` at the bottom with the path to your content json file from earlier.
   - You might want to try with 5-10 videos first. At the bottom of `render_all_video.py`, the start and end indices can be specified.
   - Example: `render_all_videos("./content/comments-04-21-25-20-33-37.json", "http://localhost:32768", 0, 10)`

7. Render all videos!

   - This uses `ffmpeg` to piece together several video clips, your background audio, generated TTS audio, and aligned subtitles.
   - This will take a very long time! Leave you computer running and grab something to eat. Or multiple things to eat...
   - In my experience, each video takes about 3-5 minutes to complete on CPU (8th gen laptop i5). Each scrape yields ~2000 comments. Not all of them are rendered (too long, too short), so I estimate on CPU this might take several days.
     - Hardware acceleration coming soon!

```
python render_all_video.py
```
