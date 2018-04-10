# =* coding:utf-8 *=

import os
import requests
import re

import subprocess

from echo_msk_personalno_webpage_parser import parse_page 


from utils import audio

from tqdm import tqdm # progressbar
import pandas
from multiprocessing.pool import ThreadPool

import wave

NUM_THREADS_PROCESSING = 1

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


def sample_text_dots(text): #разбивает текст на части по знакам препинания
    data = []
    pattern = re.compile("(?<!\d)[,.!?()]|[,.!?()](?!\d)")
    for line in text:
        s = [x for x in pattern.split(line) if x]
        for element in s:
            data.append(element)

    text = list(str(line).strip() for line in data if str(line).strip())
    
    return text

def sample_text_coef(text, min_len=5): #разбивает текст на части с заданным количеством слов min_len
    data = []

    for line in text:
        line = line.replace("\n", " ")
        line = line.replace(" ", " ") # replace diffrence space char
        
        line = re.sub(u'[^а-яё0-9 ]', '', line.strip().lower()).strip()

        line = line.split(' ')     
        k = 0
        s = ''

        for word in line:
            k = k + 1
            s = s + word + ' '
            if (k != 0 and k % min_len == 0) or word == line[-1]:
                data.append(str(s).strip())
                s = ''
    text = [line.strip() for line in data if line.strip()]

    return text

def get_ad_line_index(text_lines):
    before_ad_lines = []

    for i, line in enumerate(text_lines):
        if line == 'РЕКЛАМА' or line == 'НОВОСТИ':
            return i

    return -1

def create_force_align_map(audio_path, text_lines, output_map_path):
    text_path = audio_path+"_lines.txt"

    # write lines to text
    f = open(text_path, 'w')
    f.write('\n'.join(text_lines))
    f.close()

    p = subprocess.Popen(
        "venv/bin/python "
        + '-m aeneas.tools.execute_task '
        + audio_path+' '+text_path+' '
        + '"task_language=rus|os_task_file_format=txt|is_text_type=plain" '
        + output_map_path,

        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate()    

    if p.returncode != 0:
        print("FAILED to create forced alignment: "+str(err))
        return False
    return True

def cut_according_to_map(wave_obj, audio_path, map_path, output_dir_path):
    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path)

    m = pandas.read_table(map_path, sep=' ', quotechar='"').as_matrix()

    # audio_path_wav = os.path.join(audio_folder_path, "%i.wav" % file_id)
    # if not os.path.exists(audio_path_wav):
    #     convert_to_wav(audio_path_mp3, audio_path_wav)

    #pbar = tqdm(total=len(m))
    def cutter_thread_method(d):
        i, row = d        

        #pbar.update(1)

        part_id = row[0]
        start = row[1]
        end = row[2]

        if start >= end:
            return None

        transcript = row[3]

        # if not (type(transcript) is str):
        #     return None

        # transcript = transcript.decode('utf-8').replace("\n", " ").replace(' ', ' ')
        #print transcript.strip().lower()
        # transcript = re.sub(u'[^а-яё ]', '', transcript.strip().lower()).strip()
        #print transcript


        # if is_bad_subs(transcript):
        #     return None

        #stats_good_subs_count += 1
        audio_piece_path = os.path.join(output_dir_path, str(part_id) + ".wav")        

       

            
        if not os.path.exists(audio_piece_path):
             # try correct
            #corr = audio.try_correct_cut(wave_obj, start, end)
            #if corr:
            #    start, end = corr
            #audio.cut_audio_piece_to_wav(audio_path, audio_piece_path, start, end)

            audio.cut_wave(wave_obj, audio_piece_path, int(start*1000), int(end*1000))

        



            # if is_bad_piece(audio_piece_path, transcript):
            #     if os.path.exists(audio_piece_path):
            #         os.remove(audio_piece_path)
            #     return None

        #stats_good_piece_count += 1

        #file_size = os.path.getsize(audio_piece_path)

       # row = [audio_piece_path, str(file_size), transcript]

        return row

    pool = ThreadPool(NUM_THREADS_PROCESSING)
    pieces_rows = pool.map(cutter_thread_method, enumerate(m))

    
    #pieces_rows = [x for x in pieces_rows if x != None]


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

    # download audio
    audio_path = os.path.join(item_data_folder_path, item_name+"-audio.mp3")
    if not os.path.exists(audio_path):
        download_audio(audio_url, audio_path)    


    # PREPROCESS AUDIO
    # convert audio
    audio_path_wav = os.path.join(item_data_folder_path, item_name+"-audio.wav")
    if not os.path.exists(audio_path_wav):
        audio.convert_to_wav(audio_path, audio_path_wav)        

    # CUT COMMERTIALS


    # FORCE ALIGNMENT
    
    text_lines_coeff = sample_text_coef(text_lines, min_len=8)
    text_lines_punct = sample_text_dots(text_lines)

    for l in text_lines_punct:
        print l

    print("Creating map...")
    # map text to speech
    map_path = os.path.join(item_data_folder_path, item_name+("-fa_map.txt"))
    if not os.path.exists(map_path):
        create_force_align_map(audio_path_wav, text_lines_coeff, map_path)

    print("Map created: %s" % map_path)

    # load wave
    wave_obj = wave.open(audio_path_wav, 'r')

    # cut
    pieces_dir_path = os.path.join(item_data_folder_path, "pieces/")
    cut_according_to_map(wave_obj, audio_path_wav, map_path, pieces_dir_path)


    # cut first intro if exists
    # audio_path_next = os.path.join(item_data_folder_path, item_name+("-audio_%i.mp3" % process_step))
    # audio_fingerprint_finder.cut_ads(audio_path_prev, audio_path_next, before_seconds=60)


    # while 1:
    #     ad_line_index = get_ad_line_index(text_lines)
    #     if ad_line_index == -1:
    #         break

    #     print('ad_line_index: %i' % ad_line_index)

    #     #text_lines_before_ad = text_lines[:ad_line_index]

    #     # create map before ad
    #     output_map_path = os.path.join(item_data_folder_path, item_name+("-fa_map_%i.txt" % process_step))
    #     create_force_align_map(audio_path_next, text_lines, output_map_path)

    #     return

        
    #     del text_lines[ad_line_index]

    #     process_step += 1
    
    print('done')
    



parse_item("https://echo.msk.ru/programs/personalno/1825902-echo/")