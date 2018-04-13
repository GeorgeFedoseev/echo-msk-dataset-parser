import os
import sys

import echo_msk_personalno_parser
import echo_msk_personalno_webpage_urls_collector
import echo_msk_personalno_webpage_parser

from tqdm import tqdm

from multiprocessing.pool import ThreadPool


def parse():
    print 'starting parsing...'

    print 'get links updates..'
    urls = echo_msk_personalno_webpage_urls_collector.find_all_urls()
    print 'have %i urls total' % len(urls)

    parse.total_parsed_urls = 0
    parse.good_parsed_urls = 0

    def prepare_url_data(url):            

        parse.total_parsed_urls+=1
        item_name = echo_msk_personalno_parser.get_item_name_from_url(url)
        item_data_folder_path = echo_msk_personalno_parser.get_item_data_folder(url)
        if not os.path.exists(item_data_folder_path):
            os.makedirs(item_data_folder_path)    

        audio_path = os.path.join(item_data_folder_path, item_name+"-audio.mp3")
        if not os.path.exists(audio_path):
            # parse page to get audio url
            parse_res = echo_msk_personalno_webpage_parser.parse_page(url)
            if parse_res:
                parse.good_parsed_urls+=1
                audio_url, text_lines, cut_points = parse_res

                # download audio                
                if not os.path.exists(audio_path):
                    echo_msk_personalno_parser.download_audio(audio_url, audio_path)
        else:
            # already have audio - means all good
            parse.good_parsed_urls+=1

        if parse.total_parsed_urls > 0:
            print 'good/total = %.2f (%i/%i)' % (float(parse.good_parsed_urls)/parse.total_parsed_urls, parse.good_parsed_urls, parse.total_parsed_urls)

        parse.pbar.update(1)
            

    parse.pbar = tqdm(total=len(urls))
    NUM_THREADS = 3
    pool = ThreadPool(NUM_THREADS)
    pool.map(prepare_url_data, urls)
    #for url in urls:
    #    prepare_url_data(url)

    


    pass




if __name__ == "__main__":
    parse()


