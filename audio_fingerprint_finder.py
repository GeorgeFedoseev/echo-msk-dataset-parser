import subprocess
import sys
import os

import re

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


def concatinate(input_paths, output_path):
    print 'Concatinate %i files' % len(input_paths) 



    # ffmpeg -i "concat:input1.mpg|input2.mpg|input3.mpg" -c copy output.mpg
    p = subprocess.Popen(["ffmpeg", "-y",
         "-i", 'concat:'+'|'.join(input_paths),
         "-c", 'copy',         
         output_path
         ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate()

    if p.returncode != 0:
        print("failed_ffmpeg_concat "+str(err))
        return False
    return True


def cut_piece(input_path, start, end, output_path):
    p = subprocess.Popen(["ffmpeg", "-y",
         "-i", input_path,
         "-ss", str(start),
         "-to", str(end),        
         output_path
         ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate()

    if p.returncode != 0:
        print("failed_ffmpeg_conversion "+str(err))
        return False
    return True

def maybe_create_ad_db():
    if os.path.exists(ads_db_path):
        return

    print 'Create ads fingerprint db...'
        
    item_paths = []
    for item in os.listdir(AD_EXAMPLES_DIR_PATH):
        item_path = os.path.join(AD_EXAMPLES_DIR_PATH, item)

        try:
            get_audio_length(item_path)
        except:
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

def get_audio_length(input_file):    
    result = subprocess.Popen('ffprobe -i '+input_file+' -show_entries format=duration -v quiet -of csv="p=0"', stdout=subprocess.PIPE,stderr=subprocess.STDOUT, shell=True)
    output = result.communicate()

    return float(output[0])

def find_ads(input_path, input_audio_path, before_seconds=-1):
    maybe_create_ad_db()

    print 'Finding ads in %s...' % input_path

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
            + ' ' + input_path,
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

    print 'Read matches from cache %s' % matches_file_path
    # read cached
    txt = open(matches_file_path, 'r')
    out = txt.read()
    txt.close()   

  
    regexp = re.compile(r'Matched[\s]*(?P<matched_duration>[0-9\.]+).*starting at[\s]*(?P<start_target>[0-9\.]*).*to time[\s]*(?P<start_piece>[0-9\.]*).*in.*\/(?P<ad_type>.*)\..*with[\s]*(?P<hashes_matched>[0-9]*).*of[\s]*(?P<hashes_total>[0-9]*)')    
    groups = [m.groupdict() for m in regexp.finditer(out)]
    
    ads = []



    pointer = 0

    total_duration = get_audio_length(input_audio_path)

    while pointer < len(groups):
        m = groups[pointer]


        start = float(m['start_target'])
        end = float(m['start_target']) + float(m['matched_duration'])

        if before_seconds != -1 and end > before_seconds:
            break

        if 'intro' in m['ad_type']:
            if len(ads) == 0 and start < 2*60:
                # if first and not so far from beginning - cut from 0 to ad end
                # (case where there are ads in beginning and then headpiece)
                ads.append({
                    'start': 0,
                    'end': end,
                    'type': m['ad_type']
                    })        
            else:
                # else - just cut matched ad
                ads.append({
                    'start': start,
                    'end': end,
                    'type': m['ad_type']
                    })

            pointer += 1

        else:
            raise Exception('WARNING: undefined ad type "%s"' % ad['type'])

    print 'ads regions: %s' % str(ads)

    return ads


def get_regions_to_save(input_file, before_seconds=-1):
    total_duration = get_audio_length(input_file)
    precomputed_path = precompute(input_file)
    ads_regions = find_ads(precomputed_path, input_file, before_seconds)

    save_regions = []

    for i, ad in enumerate(ads_regions):        

        region_start = 0 if i == 0 else ads_regions[i-1]['end']
        region_end = ad['start']

        region_duration = region_end - region_start

        if region_duration < 5:
            continue

        save_regions.append({
            'start': region_start,
            'end': region_end
            })
        

    # add last region
    if len(ads_regions) > 0:
        region_start = ads_regions[-1]['end']
        region_end = total_duration

        region_duration = region_end - region_start

        if not(region_duration < 5):            
            save_regions.append({
                'start': region_start,
                'end': region_end
                })

    else:
        save_regions.append({
                'start': 0,
                'end': total_duration
                })


    print '%i save regions: %s' % (len(save_regions), str(save_regions))

    return save_regions

def cut_ads(input_file_path, output_file_path, before_seconds=-1):  



    print 'Processing %s' % input_file_path  
    regions_to_merge = get_regions_to_save(input_file_path, before_seconds)
    print 'Merging pieces without ads...'

    piece_paths = []
    for i, region in enumerate(regions_to_merge):
        name, ext = os.path.splitext(os.path.basename(input_file_path))
        piece_path = os.path.join(TMP_DIR_PATH, name+"-piece"+str(i)+'-'+str(region['start'])+'-'+str(region['end'])+'.'+ext)
        if not os.path.exists(piece_path):
            cut_piece(input_file_path, region['start'], region['end'], piece_path)
        piece_paths.append(piece_path)

    concatinate(piece_paths, output_file_path)

