import os
import csv

import sys

sys.path.insert(0,os.getcwd()) 

import const

import csv_utils

def show_global_stats():


    curr_dir_path = os.getcwd()

    
    videos_data_dir = os.path.join(curr_dir_path, "data/")


    stats_total_duration = 0.0
    stats_videos_folders_count = 0

    stats_total_samples_count = 0
    stats_good_samples_count = 0
    

    

    

    if os.path.exists(videos_data_dir):
    
        

        for item in os.listdir(videos_data_dir):
            item_path = os.path.join(videos_data_dir, item)

            if not os.path.isdir(item_path):
                continue

            stats_videos_folders_count+=1

            stats_path = os.path.join(item_path, "stats.csv")

            if not os.path.exists(stats_path):
                #print 'WARNING: no stats for video '+item
                continue

            
            stats_csv = csv_utils.read_all(stats_path) 
            stats = stats_csv[1]
            stats_total_duration += float(stats[0])            

            if len(stats) > 2:
                stats_good_samples_count += int(stats[1])

            if len(stats) > 3:
                stats_total_samples_count += int(stats[2])


    # print stats

    print '[PARSING STATS]'    

    print "stats_total_samples_count: " + str(stats_total_samples_count)
    print "stats_good_samples_count: " + str(stats_good_samples_count)

    if stats_total_samples_count > 0:
        print "good_samples_percentage: "+str(float(stats_good_samples_count)/stats_total_samples_count*100)+'%'

    print "stats_total_duration: " + format(stats_total_duration/3600, '.2f')+" hours"

if __name__ == '__main__':
    show_global_stats()
        
