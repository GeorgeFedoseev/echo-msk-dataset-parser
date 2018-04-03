# =* coding:utf-8 *=

from bs4 import BeautifulSoup

def extract_text(soup, directory):
    ads_count = 0
    div_teg = soup.find("div", "typical dialog _ga1_on_ contextualizable include-relap-widget")
    if not div_teg:
        print('failed\n')
        return False, ads_count
    p_list = div_teg.find_all('p')
    isB = False
    for p in p_list:
        if (p.find('b')):
            isB = True
            break
    if not isB:
        print('failed\n')
        return False, ads_count
    else:
        text = []
        with open(directory + '/text.txt', 'w', encoding='utf-8') as f:
        #with open(directory + '/text.txt', 'w') as f:
            for p in p_list:
                b = p.find('b')
                if b:
                    line = str(p.text).replace(b.text, '')
                else:
                    line = str(p.text)
                if not 'НОВОСТИ' in line and not 'РЕКЛАМА' in line:
                    text.append(line)
                    f.write(line)
                else:
                    ads_count = ads_count + 1
        f.close()
        print("done")
        return text, ads_count


def extract_audio_url(soup, directory):
    href = soup.find("a", "load iblock", href=re.compile("^https://cdn.echo.msk.ru/snd/"))["href"]
    print("found audio url: %s" % href)
    return href