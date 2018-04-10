import subprocess
import sys
import os

import re

from utils import audio

curr_dir_path = os.path.dirname(os.path.realpath(__file__))
TMP_DIR_PATH = os.path.join(curr_dir_path, "processing_tmp/")

AD_EXAMPLES_DIR_PATH = os.path.join(curr_dir_path, 'cut_audio_samples/')

AUDFPRING_DIR_PATH = os.path.join(curr_dir_path, "audfprint/")

ads_db_path = os.path.join(TMP_DIR_PATH, "ads.db")
audfprint_script_path = os.path.join(AUDFPRING_DIR_PATH, "audfprint.py")

map_file_path = os.path.join(TMP_DIR_PATH, "matches.txt")

if not os.path.exists(TMP_DIR_PATH):
    os.makedirs(TMP_DIR_PATH)
if not os.path.exists(AD_EXAMPLES_DIR_PATH):
    os.makedirs(AD_EXAMPLES_DIR_PATH)




def maybe_create_ad_db():
    if os.path.exists(ads_db_path):
        return

    print 'Create fingerprint db...'
        
    item_paths = []
    for item in os.listdir(AD_EXAMPLES_DIR_PATH):
        item_path = os.path.join(AD_EXAMPLES_DIR_PATH, item)

        try:
            audio.get_audio_length(item_path)
        except:
            print "maybe_create_ad_db: skip item: %s" % item_path
            continue

        item_paths.append(item_path)
    
    txt_paths_file_path = os.path.join(TMP_DIR_PATH, 'ad_examples_paths.txt')

    txt = open(txt_paths_file_path, 'w')
    txt.write('\n'.join(item_paths))
    txt.close()



    # create db
    p = subprocess.Popen(
        "venv/bin/python "
        + audfprint_script_path
        + " new"
        + " --dbase "+ads_db_path
        + " --density 150"
        + " --shifts 1"
        + " --samplerate 11025"
        + " --list "+txt_paths_file_path,
        
         shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate()
    print out

    if p.returncode != 0:
        raise Exception("failed ads db creating: "+err)

    



def precompute(input_path):
    print 'Precomputing for %s' %input_path

    name, ext = os.path.splitext(os.path.basename(input_path))
    output_file_path = os.path.join(TMP_DIR_PATH, name+'.afpt')

    

    if os.path.exists(output_file_path):
        print 'Already have precoputed file %s' % output_file_path
        return output_file_path

    p = subprocess.Popen(
        "venv/bin/python "
        + audfprint_script_path
        + " precompute"
        + " --precompdir "+TMP_DIR_PATH
        + " --density 150"
        + " --shifts 1"
        + " --samplerate 11025"
        + " --ncores 1"        
        + ' ' + input_path,
        #+ ' --opfile ' + map_file_path,
         shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate()
    print out

    if p.returncode != 0:
        raise Exception("failed precompute: "+err)

    return output_file_path


def find_audio_from_db(input_path):
    maybe_create_ad_db()

    precomputed_path = precompute(input_path)


    print 'Finding audio from fingerprint db in %s...' % input_path

    print 'using db %s' % ads_db_path


    matches_file_path = os.path.join(TMP_DIR_PATH, os.path.basename(input_path)+'_matches.txt')

    if not os.path.exists(matches_file_path):
        print 'Matching...'
        p = subprocess.Popen(
            "venv/bin/python "
            + audfprint_script_path
            + " match"
            + ' --find-time-range'
            + ' --max-matches 25'
            + " --dbase " + ads_db_path
            + " --ncores 1"
            + ' --sortbytime'
            + ' ' + precomputed_path,
            #+ ' --opfile ' + map_file_path,
             shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        out, err = p.communicate()
        print out


        if p.returncode != 0:
            raise Exception("failed matching: "+err)
            

        # write to file
        txt = open(matches_file_path, 'w')
        txt.write(out)
        txt.close()

        print 'Wrote matches from cache %s' % matches_file_path

    # read cached
    print 'Read matches from cache %s' % matches_file_path    
    txt = open(matches_file_path, 'r')
    out = txt.read()
    txt.close()   

    
    # match results
    regexp = re.compile(r'Matched[\s]*(?P<matched_duration>[0-9\.]+).*starting at[\s]*(?P<start_target>[0-9\.]*).*to time[\s]*(?P<start_piece>[0-9\.]*).*in.*\/(?P<ad_type>.*)\..*with[\s]*(?P<hashes_matched>[0-9]*).*of[\s]*(?P<hashes_total>[0-9]*)')    
    groups = [m.groupdict() for m in regexp.finditer(out)]
    

    # collect regions
    regions = []
    pointer = 0

    total_duration = audio.get_audio_length(input_path)

    while pointer < len(groups):
        m = groups[pointer]


        start = float(m['start_target'])
        end = float(m['start_target']) + float(m['matched_duration'])

       

        if 'intro' in m['ad_type']:
            if len(regions) == 0 and start < 2*60:
                # if first and not so far from beginning - cut from 0 to ad end
                # (case where there are ads in beginning and then headpiece)
                regions.append((
                    0,
                    end+1, # + 1 cause specific intro sound
                    m['ad_type']
                    ))        
            else:
                # else - just cut matched ad
                regions.append((
                    start,
                    end+1, # + 1 cause specific intro sound
                    m['ad_type']
                    ))

            pointer += 1

        else:
            raise Exception('WARNING: undefined ad type "%s"' % ad['type'])

    print 'fingerptited audio regions: %s' % str(regions)

    return regions


