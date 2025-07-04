from playwright.sync_api import sync_playwright, Page, Locator
import os
import shutil
from pathlib import Path

from consts import DESCRIPTION, UPLOAD_WAIT_TIME, UPLOAD_INTERVAL, UPLOAD_START_INDEX, UPLOAD_END_INDEX
from util import log, validate_file_extension

def upload_one_video(page: Page, video_path: str):
  log(f"Starting upload of {video_path}")

  # click create button
  create_button: Locator = page.get_by_role("button", name="Create").all()[0]
  create_button.hover()
  create_button.click()

  # click upload videos button
  upload_button: Locator = page.get_by_text("Upload videos")
  upload_button.hover()
  upload_button.click()

  # add file to file picker
  file_picker: Locator = page.locator('input[type="file"]')
  file_picker.set_input_files(video_path)

  # wait a moment for modal to update
  page.wait_for_timeout(5000)

  # fill description field
  description_box = page.locator("div#textbox[aria-label='Tell viewers about your video (type @ to mention a channel)']")
  description_box.hover()
  description_box.click()
  description_box.fill(DESCRIPTION)

  # click coppa required radiobutton
  coppa_radio: Locator = page.get_by_role("radio", name="No, it's not made for kids")
  coppa_radio.hover()
  coppa_radio.click()

  # click next 3 times
  for i in range(3):
    next_button: Locator = page.get_by_role("button", name="Next", exact=True).all()[0]
    next_button.hover()
    next_button.click()
  
  # click public radiobutton
  public_radio: Locator = page.get_by_role("radio", name="Public")
  public_radio.hover()
  public_radio.click()
  
  # wait 30s for upload
  log(f"Waiting {UPLOAD_WAIT_TIME}s for upload...")
  page.wait_for_timeout(UPLOAD_WAIT_TIME * 1000)
  log("Done waiting")

  # click publish button
  publish_button = page.get_by_role("button", name="Publish", exact=True).all()[0]
  publish_button.hover()
  publish_button.click()

  # click close button after publish
  page.wait_for_timeout(5000) # wait a moment for the modal to appear
  close_button: Locator = page.get_by_role("button", name="Close", exact=True).all()[0]
  close_button.hover()
  close_button.click()

  log("Completed uploading!")

# uploads all videos in out/ ending in .mp4
def upload_all_videos() -> None:
  # get list of videos to upload
  videos: list[str] = []
  try:
    videos = os.listdir("./video")
  except FileNotFoundError:
    log("out/ folder does not exist, please run the renderer first to get some output videos", "F")
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
      log("Redirected to log in page; not logged in")
      input("Log into YouTube now manually, then press [Enter] to continue...")

    log("Should be logged in!")

    start_index = UPLOAD_START_INDEX
    end_index = UPLOAD_END_INDEX if UPLOAD_END_INDEX != -1 and UPLOAD_END_INDEX < len(videos) else len(videos)
    log(f"Rendering out {end_index - start_index} videos")

    # main loop to upload videos
    num_uploaded = 0
    for i in range(start_index, end_index):
      num_uploaded += 1
      video = videos[i]
      video_path = f"./out/{video}"
      log(f"Beginning upload for video {num_uploaded}/{end_index - start_index}: '{video}'")

      try:
        upload_one_video(page, video_path)
        log(f"Completed uploading {video}")
        # move file to done/ folder
        try:
          shutil.move(video_path, f"./out/done/{video}")
          log(f"Moved {video} to out/done/ folder")
        except Exception as ex:
          log(f"Failed to move {video} to done folder", "E")
          log(ex, "E")
      except Exception as ex:
        log(f"Failed to upload {videos[i]}", "E")
        log(ex, "E")
      
      # wait for delay between uploads
      log(f"Waiting {UPLOAD_INTERVAL}s before uploading next video")
      page.wait_for_timeout(UPLOAD_INTERVAL * 1000)

    browser.close()

if __name__ == "__main__":
  upload_all_videos()