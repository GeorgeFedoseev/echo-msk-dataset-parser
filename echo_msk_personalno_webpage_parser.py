# =* coding:utf-8 *=

from bs4 import BeautifulSoup as bs
import requests

import sys

import re

reload(sys)
sys.setdefaultencoding("utf-8")


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

    for p in content_el.find_all('p'):
        txt = p.text.strip()

        if txt == "":
            continue

        # remove bold speaker name
        if p.find('b'):
            speaker_name = p.find('b').text.strip()
            txt = txt.replace(speaker_name, '')

        print txt


            
    


def extract_audio_url(soup, directory):
    href = soup.find("a", "load iblock", href=re.compile("^https://cdn.echo.msk.ru/snd/"))["href"]
    print("found audio url: %s" % href)
    return href

def parse_page(url):
    print 'parsing page %s' % url

    r = requests.get(url)
    soup = bs(r.text, 'html.parser')

    text = extract_text(soup)

    if text:
        pass
    
        


if __name__ == "__main__":
    parse_page("https://echo.msk.ru/programs/personalno/2163304-echo/")




