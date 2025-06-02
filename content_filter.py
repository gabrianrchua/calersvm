import re
from fnmatch import fnmatchcase
from better_profanity import profanity

substitutions = [
  ("kill", "unalive"),
  ("idk", "I don't know"),
  ("omg", "oh my god"),
  ("brb", "be right back"),
  ("gtg", "got to go"),
  ("ttyl", "talk to you later"),
  ("btw", "by the way"),
  ("imo", "in my opinion"),
  ("oml", "oh my lord"),
  ("omd", "oh my days"),
  ("imho", "in my humble opinion"),
  ("mb", "my bad"),
  ("fyi", "for your information"),
  ("tbh", "to be honest"),
  ("srs", "serious"),
  ("srsly", "seriously"),
  ("smh", "shaking my head"),
  ("gib", "give"),
  ("js", "just"),
  ("ikr", "I know right"),
  ("ik", "I know"),
  ("idek", "I don't even know"),
  ("np", "no problem"),
  ("ty", "thank you"),
  ("thx", "thanks"),
  ("yw", "you're welcome"),
  ("afaik", "as far as I know"),
  ("asap", "as soon as possible"),
  ("bbl", "be back later"),
  ("bfn", "bye for now"),
  ("bff", "best friends forever"),
  ("dm", "direct message"),
  ("hmu", "hit me up"),
  ("jk", "just kidding"),
  ("lmk", "let me know"),
  ("nvm", "never mind"),
  ("rn", "right now"),
  ("wbu", "what about you"),
  ("wyd", "what are you doing"),
  ("wym", "what do you mean"),
  ("omw", "on my way"),
  ("pov", "point of view"),
  ("rofl", "rolling on the floor laughing"),
  ("stfu", "shut the frick up"),
  ("icl", "I can't lie"),
  ("pmo", "pisses me off"),
  ("sus", "suspicious"),
  ("tmi", "too much information"),
  ("wth", "what the heck"),
  ("wtf", "what the frick"),
  ("xd", "laughing"),
  ("xoxo", "hugs and kisses"),
  ("irl", "in real life"),
  ("afaik", "as far as I know"),
  ("fml", "frick my life"),
  ("faq", "frequently asked questions"),
  ("gg", "good game"),
  ("glhf", "good luck, have fun"),
  ("wp", "well played"),
  ("afk", "away from keyboard"),
  ("b/c", "because"),
  ("bc", "because"),
  ("dm", "direct message"),
  ("gr8", "great"),
  ("mfw", "my face when"),
  ("tfw", "that feeling when"),
  ("icymi", "in case you missed it"),
  ("imo", "in my opinion"),
  ("imho", "in my humble opinion"),
  ("tl;dr", "too long didn't read"),
  ("tldr", "too long didn't read"),
  ("idgaf", "I don't give a frick"),
  ("ts", "this stuff"),
  ("g2g", "got to go"),
  ("gtg", "got to go"),
  ("b4", "before"),
  ("cya", "see you"),
  ("pls", "please"),
  ("thx", "thanks"),
  ("u", "you"),
  ("ur", "your"),
  ("r", "are"),
  ("yolo", "you only live once"),
  ("ggwp", "good game well played"),
  ("icymi", "in case you missed it"),
  ("smol", "small"),
  ("sm", "so much"),
  ("fr", "for real"),
  ("oop", "oops"),
  ("yeet", "throw"),
  ("ngl", "not gonna lie"),
  ("mhm", "yes"),
  ("idc", "I don't care"),
  ("ilu", "I love you"),
  ("ily", "I love you"),
  ("btw", "by the way"),
  ("wyd", "what are you doing"),
  ("wbu", "what about you"),
]

def clean_text(text: str) -> str:
  words = text.split()
    
  def replace_word(word):
    lower_word = word.lower()
    for pattern, substitute in substitutions:
      lower_pattern = pattern.lower()
      if fnmatchcase(lower_word, lower_pattern):
        final_substitute = substitute
        # *word*
        if lower_pattern[0] == "*" and lower_pattern[-1] == "*":
          final_substitute = f"\\1{substitute}\\2"
        # *word
        elif lower_pattern[0] == "*":
          final_substitute = f"\\1{substitute}"
        # word*
        elif lower_pattern[-1] == "*":
          final_substitute = f"{substitute}\\1"

        return re.sub(re.escape(lower_pattern).replace('\\*', '(.*)'), final_substitute, word, flags=re.IGNORECASE)
    return word
    
  pre_text = ' '.join(replace_word(word) for word in words)

  # just in case: catch remaining words with package
  return profanity.censor(pre_text).replace("****", "beep")
