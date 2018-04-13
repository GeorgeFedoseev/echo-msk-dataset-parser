import os

import audio_fingerprint_finder
from utils import audio
import audio_intermittent_segmentation
import datetime

import wave

import const




def get_regions_to_save(input_file):
    total_duration = audio.get_audio_length(input_file)    
    regions_to_cut = get_regions_to_cut(input_file)



    save_regions = []

    for i, region in enumerate(regions_to_cut):        

        region_start = 0 if i == 0 else regions_to_cut[i-1][1]
        region_end = region[0]

        region_duration = region_end - region_start

        if region_duration < 5:
            continue

        save_regions.append((region_start, region_end, 'save'))
        

    # add last region
    if len(regions_to_cut) > 0:
        region_start = regions_to_cut[-1][1]
        region_end = total_duration

        region_duration = region_end - region_start

        if not(region_duration < 5):            
            save_regions.append((region_start, region_end, 'save'))

    else:
        save_regions.append((0, total_duration, 'save'))


    print '%i save regions: %s' % (len(save_regions), str(save_regions))

    return save_regions

def region_str(region):
    return "%s - %s: %s" % ( str(datetime.timedelta(seconds=region[0])), str(datetime.timedelta(seconds=region[1])), str(region[2]) )

def print_regions(regions):
    for region in regions:
        print region_str(region)    

def find_region_near_time(t, regions, max_distance):
    for r in regions:
        # if t inside region
        if t >= r[0] and t <= r[1]:
            #print "inside"
            return r
        # if t before
        if abs(r[0] - t) < max_distance:
            #print "after"
            return r
        # if t after
        if abs(t - r[1]) < max_distance:
            #print "before"
            return r
    return None

def get_regions_to_cut(wav_path):
    fngpt_regions = audio_fingerprint_finder.find_audio_from_db(wav_path)
    intrmttnt_regions = audio_intermittent_segmentation.get_commertial_intervals(wav_path)
    intrmttnt_regions = [r for r in intrmttnt_regions if r[2] == 1]

    print "Fingerprint regions:"
    print_regions(fngpt_regions)
    print "Audio_intermittent regions:"
    print_regions(intrmttnt_regions)


    print "---------"
    regions_to_cut = []

    used_fngpt_regions = []
    for ir in intrmttnt_regions:
        print "for region %s" % region_str(ir)
        # find close to end intro
        #print "for time %s" % str(datetime.timedelta(seconds=ir[1]))
        start = ir[0]
        end = ir[1]
        intro_r = find_region_near_time(end, fngpt_regions, 30)
        if intro_r:
            print "found fngpt region %s" % region_str(intro_r)
            end = intro_r[1]
            if intro_r[0] < start:
                start = intro_r[0]

            used_fngpt_regions.append(intro_r)

            regions_to_cut.append((start, end, 'commertial'))
        else:
            # didnt find intro finishing commertial
            # accept it only if its in the end
            # and cut till the end
            total_duration = audio.get_audio_length(wav_path)
            if abs(end - total_duration) < 20:
                end = total_duration
                regions_to_cut.append((start, end, 'commertial'))

        

        print "======="

    # also add unused intermittent regions to cut just intro
    not_used_fngpt_regions = [r for r in fngpt_regions if not any([x[0] == r[0] for x in used_fngpt_regions])]
    regions_to_cut.extend(not_used_fngpt_regions)
    if len(not_used_fngpt_regions) > 0:
        print('also added %i not used fingerprint regions' % len(not_used_fngpt_regions))


    print "commertial regions: "
    print_regions(regions_to_cut)

    return regions_to_cut




def cut_commertials(input_file_path, output_file_path):  

    print 'Processing %s' % input_file_path  
    regions_to_merge = get_regions_to_save(input_file_path)
    print 'Merging pieces without ads...'

    wave_obj = wave.open(input_file_path)

    piece_paths = []
    for i, region in enumerate(regions_to_merge):
        name, ext = os.path.splitext(os.path.basename(input_file_path))
        piece_path = os.path.join(const.TMP_DIR_PATH, name+"-piece"+str(i)+'-'+str(region[0])+'-'+str(region[1])+ext)
        print piece_path
        if not os.path.exists(piece_path):
            audio.cut_wave(wave_obj, piece_path, int(region[0]*1000), int(region[1]*1000))
        piece_paths.append(piece_path)

    # generate txt file with pathes to concat
    list_txt_path = os.path.join(const.TMP_DIR_PATH, name+"-concat-list.txt")
    f = open(list_txt_path, 'w')
    for path in piece_paths:
        f.write('file %s\n' % path)
    f.close()

    audio.concatinate_files(list_txt_path, output_file_path)




if __name__ == "__main__":
    WAV_FILE = 'data/test3.wav'
    NOT_ADS_FILE = 'data/no_ads.wav'
    #get_regions_to_cut(WAV_FILE)
    cut_commertials(WAV_FILE, NOT_ADS_FILE)
