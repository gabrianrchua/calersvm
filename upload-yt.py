from playwright.sync_api import sync_playwright, Page, Locator
import os
import shutil
from pathlib import Path

from consts import DESCRIPTION, UPLOAD_WAIT_TIME, UPLOAD_INTERVAL, UPLOAD_START_INDEX, UPLOAD_END_INDEX
from util import Log, validate_file_extension

def upload_one_video(page: Page, video_path: str) -> None:
  Log.info(f"Starting upload of {video_path}")

  # click create button
  Log.verbose("Clicking Create button in header")
  create_button: Locator = page.get_by_role("button", name="Create").first
  create_button.hover()
  create_button.click()

  # click upload videos button
  Log.verbose("Clicking Upload videos option in dropdown")
  upload_button: Locator = page.get_by_text("Upload videos")
  upload_button.hover()
  upload_button.click()

  # add file to file picker
  Log.verbose("Adding video file to upload picker")
  file_picker: Locator = page.locator('input[type="file"]')
  file_picker.set_input_files(video_path)

  # wait a moment for modal to update
  Log.verbose("Waiting 5s for upload modal to update")
  page.wait_for_timeout(5000)

  # fill description field
  Log.verbose("Filling description field")
  description_box: Locator = page.locator("div#textbox[aria-label='Tell viewers about your video (type @ to mention a channel)']")
  description_box.hover()
  description_box.click()
  description_box.fill(DESCRIPTION)

  # click coppa required radiobutton
  Log.verbose("Selecting not made for kids coppa radiobutton")
  coppa_radio: Locator = page.get_by_role("radio", name="No, it's not made for kids")
  coppa_radio.hover()
  coppa_radio.click()

  # click next 3 times
  Log.verbose("Clicking next 3 times")
  for i in range(3):
    next_button: Locator = page.get_by_role("button", name="Next", exact=True).first
    next_button.hover()
    next_button.click()
  
  # click public radiobutton
  Log.verbose("Selecting public release radiobutton")
  public_radio: Locator = page.get_by_role("radio", name="Public")
  public_radio.hover()
  public_radio.click()
  
  # wait 30s for upload
  Log.info(f"Waiting {UPLOAD_WAIT_TIME}s for upload...")
  page.wait_for_timeout(UPLOAD_WAIT_TIME * 1000)
  Log.info("Done waiting")

  # click publish button
  Log.verbose("Clicking Publish button")
  publish_button = page.get_by_role("button", name="Publish", exact=True).first
  publish_button.hover()
  publish_button.click()

  # wait a moment for the modal to appear
  Log.verbose("Waiting 5s for the final modal to appear")
  page.wait_for_timeout(5000)

  # click close button after publish
  Log.verbose("Clicking Close button")
  close_button: Locator = page.get_by_role("button", name="Close", exact=True).first
  close_button.hover()
  close_button.click()

  Log.info("Completed uploading!")

# uploads all videos in out/ ending in .mp4
def upload_all_videos() -> None:
  # get list of videos to upload
  videos: list[str] = []
  try:
    videos = os.listdir("./out")
  except FileNotFoundError:
    Log.fatal("out/ folder does not exist, please run the renderer first to get some output videos")
    return
  videos = [video for video in videos if validate_file_extension(video, [".mp4"])]

  # create out/done/ folder for completed uploads if not already exist
  Path("./out/done").mkdir(parents=True, exist_ok=True)

  # launch browser with persistent context
  with sync_playwright() as p:
    device = p.devices["Desktop Chrome HiDPI"]
    browser = p.chromium.launch_persistent_context(
      user_data_dir="./playwright-profile",
      headless=False,
      viewport=device["viewport"],
      user_agent=device["user_agent"],
      device_scale_factor=device["device_scale_factor"],
      is_mobile=device["is_mobile"],
      has_touch=device["has_touch"],
      args=["--disable-blink-features=AutomationControlled"]
    )

    # reuse first page, or create one
    page = browser.pages[0] if browser.pages else browser.new_page()
    
    # go to YT studio. this will auto redirect to log in if not logged in
    page.goto("https://studio.youtube.com")

    if page.url.startswith("https://accounts.google.com"):
      Log.info("Redirected to log in page; not logged in")
      input("Log into YouTube now manually, then press [Enter] to continue...")

    Log.info("Should be logged in!")

    start_index = UPLOAD_START_INDEX
    end_index = UPLOAD_END_INDEX if UPLOAD_END_INDEX != -1 and UPLOAD_END_INDEX < len(videos) else len(videos)
    Log.info(f"Rendering out {end_index - start_index} videos")

    # main loop to upload videos
    num_uploaded = 0
    for i in range(start_index, end_index):
      num_uploaded += 1
      video = videos[i]
      video_path = f"./out/{video}"
      Log.info(f"Beginning upload for video {num_uploaded}/{end_index - start_index}: '{video}'")

      # ensure file isn't empty
      if os.path.getsize(video_path) == 0:
        Log.warn(f"Skipping {video}, file is empty")
        # move file to done/ folder
        try:
          shutil.move(video_path, f"./out/done/{video}")
          Log.info(f"Moved {video} to out/done/ folder")
        except Exception as ex:
          Log.error(f"Failed to move {video} to done folder")
          Log.error(ex)
        continue

      # attempt upload and move to done/
      try:
        upload_one_video(page, video_path)
        Log.info(f"Completed uploading {video}")
        # move file to done/ folder
        try:
          shutil.move(video_path, f"./out/done/{video}")
          Log.info(f"Moved {video} to out/done/ folder")
        except Exception as ex:
          Log.error(f"Failed to move {video} to done folder")
          Log.error(ex)
      except Exception as ex:
        Log.error(f"Failed to upload {videos[i]}")
        Log.error(ex)
        # return to main page ("refresh")
        page.goto("https://studio.youtube.com")
      
      # wait for delay between uploads
      Log.info(f"Waiting {UPLOAD_INTERVAL}s before uploading next video")
      page.wait_for_timeout(UPLOAD_INTERVAL * 1000)

    Log.info(f"Completed uploading {end_index - start_index} videos!")
    browser.close()

if __name__ == "__main__":
  upload_all_videos()