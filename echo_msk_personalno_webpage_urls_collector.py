import utils.csv_utils as csv_utils
from bs4 import BeautifulSoup as bs
import requests
import re

import datetime

#csv_utils.write_column_to_csv("test.csv", ['1', '2'])

BASE_URL = "https://echo.msk.ru"
PROGRAM_URL = "/programs/personalno"

URLS_CSV = "personalno.csv"


def get_number_of_pages():
    url = construct_archive_page_url(1)
    r = requests.get(url)
    soup = bs(r.text, 'html.parser')
    try:
        return int(soup.find("div", "pager")("a")[-2].text)
    except Exception as ex:
        print("Failed to get archive pages number: %s" % str(ex))
        return -1


def construct_archive_page_url(num):
    return "%s%s/archive/%i.html" % (BASE_URL, PROGRAM_URL, num)

def find_all_urls():
    all_urls = []

    #csv_utils.write_column_to_csv(URLS_CSV, [])

    n = get_number_of_pages()

    is_any_url_on_page_already_in_csv = False

    if n == -1:
        return all_urls
    for i in range(1, n+1):

        url = construct_archive_page_url(i)
        r = requests.get(url)
        soup = bs(r.text, 'html.parser')
        a_nodes = soup.find_all("a", "read iblock", href=re.compile(PROGRAM_URL))

        urls = []
        for a in a_nodes:
            url = BASE_URL + a["href"]
            
            if csv_utils.is_item_in_csv(URLS_CSV, url):
                is_any_url_on_page_already_in_csv = True
            else:
                print url
                urls.append(url)            

        print("parsed page %i of archive, found %i new items" % (i, len(urls)))
        all_urls += urls

        # append to csv
        csv_utils.append_column_to_csv(URLS_CSV, urls)

        if is_any_url_on_page_already_in_csv:
            # old pages started
            break

    print("total added %i urls" % len(all_urls))

    return csv_utils.get_column_csv(URLS_CSV, 0)

if __name__ == "__main__":
    find_all_urls()


