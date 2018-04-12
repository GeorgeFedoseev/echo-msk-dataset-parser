import os
import sys

import echo_msk_personalno_parser
import echo_msk_personalno_webpage_urls_collector



def parse():
    print 'starting parsing...'

    print 'get links updates..'
    echo_msk_personalno_webpage_urls_collector.find_all_urls()

    


    pass




if __name__ == "__main__":
    parse()


