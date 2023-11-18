# This script is now runnable on Google collab as well and could be useful as scraping/translation bot.

# installing packages:
# !pip install googletrans==4.0.0rc1
# !pip install news-please
# !pip install feedparser
# !pip install -U easynmt
# !pip install sacremoses

from googletrans import Translator
from newsplease import NewsPlease
from textwrap import wrap
from easynmt import EasyNMT
from torch import cuda
import feedparser as fp
import csv

device = 'cuda' if cuda.is_available() else None
translator = Translator() # carry-over from local implementation, where translator object has to be created, however works on Jupyter too
opus = EasyNMT('opus-mt', device = device)
m2m = EasyNMT('m2m_100_418m', device = device)


def rss_pars(url, max):
    # takes two arguments, rss feed url and how many links should be scrapped 
    try:   
        d = fp.parse(url)
        link_list = []
        for i in range(max):
            print("RSS feed link valid! \"{tph}\" will be included!\n".format(tph = d.entries[i].title))
            if (d.entries[i].link is not None):
                link_list.append(d.entries[i].link)
            else:
                print("RSS feed link invalid or missing! \"{tph}\" will be skipped!\n".format(tph = d.entries[i].title))            
    except:
        print("RSS feed parsing failed!\n")
        exit(1)
    
    return link_list

def dig_art(url):
    try:
        article = NewsPlease.from_url(url)
        maintext = article.maintext
        title = article.title
    except:
        print("Article parsing failed!\n")
        exit(1)
       
    return [title, maintext, trans_goog(maintext), trans_opus(maintext), trans_m2m(maintext), url] #TODO bad return

def trans_goog(text):
    split_text = wrap(text, 500)
    translated = []
    for t in split_text:
        translation = translator.translate(t, dest='cs', src='en')
        translated.append(translation.text)
    return ' '.join(translated)

def trans_opus(text):
    cuda.empty_cache()
    translation = opus.translate(text, target_lang = "cs", show_progress_bar = True, max_length=len(text)+1, batch_size=8) # Can recommend setting the max_length to the lenght of the input
    # the key to overcoming the CUDA/RAM limitations I found to be to pick the right batch_size
    return translation

def trans_m2m(text):
    cuda.empty_cache()
    # now usable with the 1.2b parameter model as well, however the quality difference seemed neglible to me with noticably longer runtimes
    translation = m2m.translate(text, target_lang = "cs", show_progress_bar = True, max_length=len(text)+1, batch_size=8)
    return translation

def write_csv(llist):
    with open("file.csv", "w", newline="") as file:
        writer = csv.writer(file)
        header = ["title", "original_text", "google_translate", "opus-mt", "facebook_m2m", "url"]
        writer.writerow(header)
        for i in range(len(llist)):
            writer.writerow(llist[i])

def main():
    cuda.empty_cache() 
    url_list = rss_pars("http://rss.cnn.com/rss/edition.rss", 20) # Can be substituted with any suitable RSS news feed
    comp = [] # while it can be useful to convert to pd dataframe in many cases, for this purpose Python built-in "list of lists" will suffice
    for i in url_list:
        comp.append(dig_art(i))
    write_csv(comp)

if __name__ == "__main__":
    main()