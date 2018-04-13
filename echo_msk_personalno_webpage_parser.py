# =* coding:utf-8 *=

from bs4 import BeautifulSoup as bs
import requests

import sys

import re

reload(sys)
sys.setdefaultencoding("utf-8")

import os

import const

WEBPAGE_CACHE_DIR = os.path.join(const.TMP_DIR_PATH, "webpages_cache/")
if not os.path.exists(WEBPAGE_CACHE_DIR):
    os.makedirs(WEBPAGE_CACHE_DIR)



def get_content_soup(soup):
    return soup.find("div", "typical dialog _ga1_on_ contextualizable include-relap-widget")

def is_good_page(soup):
    content_element = get_content_soup(soup)
    if not content_element:
        print('cant find content element')
        return False
    else:
        print('found content element, textlen: %i' % len(content_element.get_text()))

        # check if have bold speakers names
        b_count = 0
        p_count = 0
        for p in content_element.find_all('p'):
            p_count += 1
            if p.find('b'):
                b_count += 1

        bp_ratio = float(b_count)/p_count
        print('b_count/p_count = %f' % bp_ratio)

        if bp_ratio < 0.3:
            return False


    return True

        


def find_speaker_name(soup):
    matches = re.findall(u'[А-ЯЁ][А-ЯЁ .]{3,}', soup.text)
    if len(matches) > 0:
        print matches[0]



def extract_text(soup):
    if not is_good_page(soup):
        print 'BAD PAGE'
        return None

    print 'GOOD PAGE'

    content_el = get_content_soup(soup)

    text_lines = []

    cut_points = 0

    for p in content_el.find_all('p'):
        txt = p.text.strip()

        if txt == "":
            continue

        # remove bold speaker name
        if p.find('b'):
            speaker_name = p.find('b').text.strip()
            txt = txt.replace(speaker_name, '')

        # checks
        if 'РЕКЛАМА' in txt:
            cut_points += 1

            #if txt.strip() != 'РЕКЛАМА':
             #   raise Exception("'РЕКЛАМА' in txt and txt != 'РЕКЛАМА'")

        elif 'НОВОСТИ' in txt:
            cut_points += 1

            #if txt.strip() != 'НОВОСТИ':
            #    raise Exception("'НОВОСТИ' in txt and txt != 'НОВОСТИ'")
        else:
            text_lines.append(txt)

    return text_lines, cut_points

    


def extract_audio_url(soup):
    href = soup.find("a", "load iblock", href=re.compile("^https://cdn.echo.msk.ru/snd/"))["href"]    
    return href

def get_cached_webpage_text(url):
    filename = url.replace(':', '_').replace('/', '_')+".txt"
    cached_file_path = os.path.join(WEBPAGE_CACHE_DIR, filename)

    txt = ''

    if os.path.exists(cached_file_path):        
        f = open(cached_file_path, 'r')
        txt = f.read()
        f.close()
    else:
        r = requests.get(url)
        txt = r.text
        f = open(cached_file_path, 'w')
        f.write(txt)
        f.close()

    return txt

def parse_page(url):
    print 'parsing page %s' % url

    txt = get_cached_webpage_text(url)
    soup = bs(txt, 'html.parser')

    res = extract_text(soup)
    if res:
        text_lines, cut_points = res

        print('text_lines: %i' % len(text_lines))
        print('cut_points: %i' % cut_points)
        audio_url = extract_audio_url(soup)
        print('audio_url: %s' % audio_url)

        return audio_url, text_lines, cut_points

    return None
    
    
        


if __name__ == "__main__":
    parse_page("https://echo.msk.ru/programs/personalno/1452184-echo/")




