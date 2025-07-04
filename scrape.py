from playwright.sync_api import sync_playwright
from datetime import datetime
import json
from pathlib import Path
import emoji
import re

from util import Log
from consts import BASE_URL, SUBREDDIT, SKIP_NSFW, SCRAPE_ONLY_POST

# helper function to remove emojis and links and strip whitespace
def clean_text_content(text: str) -> str:
  # replace emojis with "<emoji name> emoji"
  return emoji.demojize(re.sub(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*)", "", text), delimiters=("", " emoji ")).replace("_", " ").strip()

# scrape entire first page of reddit, each thread's first page of top level comments
# returns file name of where json data was saved
def scrape_reddit(subreddit: str="/r/AskReddit") -> str:
  threads: list[dict[str, str]] = [] # list of dict {title, href}
  comments: list[dict[str, str]] = [] # list of dict {title, comment_text}

  # launch playwright to scrape
  with sync_playwright() as p:
    Log.info("Launching browser")
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(BASE_URL + subreddit)

    Log.info("Fetching thread titles and links")
    raw_links = page.locator("a.title").all()
    for link in raw_links:
      href = link.get_attribute("href")
      text = link.text_content()
      if href is not None and text is not None:
        threads.append({"title": text, "href": href})

    if SCRAPE_ONLY_POST:
      Log.info("Starting main loop to gather post contents")
    else:
      Log.info("Starting main loop to gather top comments")
    
    for i in range(len(threads)):
      Log.info(f"Gathering {'post content' if SCRAPE_ONLY_POST else 'top comments'} in link {i+1}/{len(threads)}: {threads[i]['title']} at {BASE_URL + threads[i]['href']}")
      
      if "/comments/" not in threads[i]["href"]:
        Log.info(f"Skipping, may be ad")
        continue
      
      if SKIP_NSFW and "/over18" in threads[i]["href"]:
        Log.info(f"Skipping not safe for work post")

      page.goto(BASE_URL + threads[i]["href"])
      
      if SCRAPE_ONLY_POST:
        post_body = page.locator("div.sitetable.linklisting > * > div.entry.unvoted > div.expando > form > div.usertext-body.may-blank-within.md-container")
        post_body_text = post_body.text_content()
        if post_body_text is not None:
          comments.append({"title": threads[i]["title"], "comment_text": clean_text_content(post_body_text)})
      else:
        raw_top_comments = page.locator("div.sitetable.nestedlisting > * > div.entry.unvoted > * > div.usertext-body.may-blank-within.md-container").all()

        for comment in raw_top_comments:
          comment_text = comment.text_content()
          if comment_text is not None:
            comments.append({"title": threads[i]["title"], "comment_text": clean_text_content(comment_text)})
    
    browser.close()
    
  # create output directory if not exists
  Path("./content").mkdir(parents=True, exist_ok=True)

  # write out json file with content
  file_name = f"./content/comments-{subreddit.replace('/r/', '')}-{datetime.now().strftime('%m-%d-%y-%H-%M-%S')}.json"
  Log.info(f"Completed scraping comments, saving to '{file_name}'")

  with open(file_name, "w") as f:
    json.dump(comments, f)

  Log.info("Successfully saved content!")

  return file_name

if __name__ == "__main__":
  scrape_reddit(SUBREDDIT)