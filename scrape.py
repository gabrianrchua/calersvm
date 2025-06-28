from playwright.sync_api import sync_playwright
from datetime import datetime
import json
from pathlib import Path

from util import log
from consts import BASE_URL, SUBREDDIT, SKIP_NSFW

# scrape entire first page of reddit, each thread's first page of top level comments
# returns file name of where json data was saved
def scrape_reddit(subreddit: str="/r/AskReddit") -> str:
  threads = [] # list of dict {title, href}
  comments = [] # list of dict {title, comment_text}

  # launch playwright to scrape
  with sync_playwright() as p:
    log("Launching browser")
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(BASE_URL + subreddit)

    log("Fetching thread titles and links")
    raw_links = page.locator("a.title").all()
    for link in raw_links:
      threads.append({"title": link.text_content(), "href": link.get_attribute("href")})

    log("Starting main loop to gather top comments")
    for i in range(len(threads)):
      log(f"Gathering top comments in link {i+1}/{len(threads)}: {threads[i]['title']} at {BASE_URL + threads[i]['href']}")
      
      if "/comments/" not in threads[i]["href"]:
        log(f"Skipping, may be ad")
        continue
      
      if SKIP_NSFW and "/over18" in threads[i]["href"]:
        log(f"Skipping not safe for work post")

      page.goto(BASE_URL + threads[i]["href"])
      raw_top_comments = page.locator("div.sitetable.nestedlisting > * > div.entry.unvoted > * > div.usertext-body.may-blank-within.md-container").all()

      for comment in raw_top_comments:
        comment_text = comment.text_content()
        if comment_text is not None:
          comments.append({"title": threads[i]["title"], "comment_text": comment_text.strip()})
    
    browser.close()
    
  # create output directory if not exists
  Path("./content").mkdir(parents=True, exist_ok=True)

  # write out json file with content
  file_name = f"./content/comments-{datetime.now().strftime('%m-%d-%y-%H-%M-%S')}.json"
  log(f"Completed scraping comments, saving to '{file_name}'")

  with open(file_name, "w") as f:
    json.dump(comments, f)

  log("Successfully saved comments!")

  return file_name

if __name__ == "__main__":
  scrape_reddit(SUBREDDIT)