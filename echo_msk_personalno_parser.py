import os
import requests

from echo_msk_personalno_webpage_parser import parse_page 
import audio_fingerprint_finder

curr_dir_path = os.path.dirname(os.path.realpath(__file__))
data_path = os.path.join(curr_dir_path, "data/personalno/")


def get_item_name_from_url(url):
    return [x for x in url.split('/') if x.strip() != ""][-1]

def get_item_data_folder(url):
    name = get_item_name_from_url(url)
    return os.path.join(data_path, name+'/')

def download_audio(url, audio_path):
    print('downloading %s' % url)
    audio = requests.get(url)
    with open(audio_path, 'wb') as f:
        f.write(audio.content)
    f.close()
    print('downloaded')



def parse_item(url):
    res = parse_page(url)

    if not res:
        print('Failed to parse item with url: %s' % url)
        return False

    audio_url, text_lines, cut_points_count = res

    item_name = get_item_name_from_url(url)
    item_data_folder_path = get_item_data_folder(url)
    if not os.path.exists(item_data_folder_path):
        os.makedirs(item_data_folder_path)

    audio_path = os.path.join(item_data_folder_path, item_name+"-audio.mp3")

    if not os.path.exists(audio_path):
        download_audio(audio_url, audio_path)

    

    # cut first intro if exists
    audio_path_1 = os.path.join(item_data_folder_path, item_name+"-audio_1.mp3")
    audio_fingerprint_finder.cut_ads(audio_path, audio_path_1, before_seconds=60)


    



parse_item("https://echo.msk.ru/programs/personalno/1452184-echo/")