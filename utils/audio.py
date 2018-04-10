import subprocess

import wave
import webrtcvad
import numpy as np

def get_audio_length(input_file):    
    result = subprocess.Popen('ffprobe -i '+input_file+' -show_entries format=duration -v quiet -of csv="p=0"', stdout=subprocess.PIPE,stderr=subprocess.STDOUT, shell=True)
    output = result.communicate()

    return float(output[0])


def apply_bandpass_filter(in_path, out_path):
    # ffmpeg -i input.wav -acodec pcm_s16le -ac 1 -ar 16000 -af lowpass=3000,highpass=200 output.wav
    p = subprocess.Popen(["ffmpeg", "-y",
         "-acodec", "pcm_s16le",
         "-i", in_path,    
         "-acodec", "pcm_s16le",
         "-ac", "1",
         "-af", "lowpass=3000,highpass=200",
         "-ar", "16000",         
         out_path
         ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate()

    if p.returncode != 0:
        raise Exception("Failed to apply bandpass filter: %s" % str(err))

def correct_volume(in_path, out_path, db=-10):
    # sox input.wav output.wav gain -n -10
    p = subprocess.Popen(["sox",
         in_path,             
         out_path,
         "gain",
         "-n", str(db)
         ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate()

    if p.returncode != 0:
        raise Exception("Failed to correct volume: %s" % str(err))


def convert_to_wav(in_audio_path, out_audio_path):
    print 'converting %s to big wav' % in_audio_path
    p = subprocess.Popen(["ffmpeg", "-y",
         "-i", in_audio_path,         
         "-acodec", "pcm_s16le",
         "-ac", "1",
         "-af", "lowpass=3000,highpass=200",
         "-ar", "16000",
         out_audio_path
         ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate()

    try:
        p.kill()
    except:
        pass

    if p.returncode != 0:
        print("failed_ffmpeg_conversion "+str(err))
        return False
    return True

def concatinate_files(ffmpeg_list_file_path, output_path):
    print 'Concatinate files...'

    # ffmpeg -i "concat:input1.mpg|input2.mpg|input3.mpg" -c copy output.mpg
    # ffmpeg -f concat -safe 0 -i mylist.txt -c copy output

    p = subprocess.Popen(["ffmpeg", "-y",
         "-f", "concat",
         "-safe", "0",
         "-i", ffmpeg_list_file_path,
         "-c", "copy",         
         output_path
         ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate()

    #print out

    if p.returncode != 0:
        print("failed_ffmpeg_concat "+str(err))
        return False
    return True

def cut_wave(wave_obj, outfilename, start_ms, end_ms):
    width = wave_obj.getsampwidth()
    rate = wave_obj.getframerate()
    fpms = rate / 1000 # frames per ms
    length = (end_ms - start_ms) * fpms
    start_index = start_ms * fpms

    #print 'cut_wave: %i - %i' % (start_ms, end_ms)

    out = wave.open(outfilename, "w")
    out.setparams((wave_obj.getnchannels(), width, rate, length, wave_obj.getcomptype(), wave_obj.getcompname()))
    
    wave_obj.rewind()
    anchor = wave_obj.tell()
    wave_obj.setpos(anchor + start_index)
    out.writeframes(wave_obj.readframes(length))

def cut_audio_piece_to_wav(in_audio_path, out_audio_path, start_sec, end_sec):
    p = subprocess.Popen(["ffmpeg", "-y",
         "-i", in_audio_path,
         "-ss", str(start_sec),
         "-to", str(end_sec),
         "-acodec", "pcm_s16le",
         "-ac", "1",
         "-af", "lowpass=3000,highpass=200",
         "-ar", "16000",        
         out_audio_path
         ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate()

    try:
        p.kill()
    except:
        pass

    if p.returncode != 0:
        print("failed_ffmpeg_conversion "+str(err))
        return False
    return True


def write_wave_array_to_wav(output_path, ):
    CHANNELS = 1
    BITWIDTH = 16
    SAMPLERATE = 16000

    outfile = wave.open(output_path, mode='wb')
    outfile.setparams((CHANNELS, BITWIDTH/8, SAMPLERATE, 0, 'NONE', 'not compressed'))
    outfile.writeframes(gensine(440, 1).tostring())    
    outfile.close()


# CUT CORRECTION

SPEECH_FRAME_SEC = 0.02
CHECK_FRAMES_NUM = 3

def get_speech_int_array(wave, start, end):
    vad = webrtcvad.Vad(2)

    samples_per_second = wave.getframerate()

    #print "Framerate: %i" % samples_per_second

    samples_per_frame = int(SPEECH_FRAME_SEC*samples_per_second)
    
    #print "Samples per frame: %i" % samples_per_frame

    wave.setpos(start*samples_per_second)

    wave_view_int = []
    while wave.tell() < end*samples_per_second:
        #wave_view_str += "1" if vad.is_speech(wave.readframes(samples_to_get), sample_rate) else "0"
        try:
            wave_view_int.append(1 if vad.is_speech(wave.readframes(samples_per_frame), samples_per_second) else 0)       
            wave.setpos(wave.tell() + samples_per_frame)   
        except Exception as ex:
            print("Exception: "+str(ex))
            return []

    return wave_view_int 

def has_speech(wave, start, end):
    speech_array = get_speech_int_array(wave, start, end)
    return np.sum(speech_array) > 0

def starts_with_speech(wave, start, end):
    speech_array = get_speech_int_array(wave, start, end)
    #print 'start2: '+(''.join([str(x) for x in speech_array]))
    return np.sum(speech_array[:CHECK_FRAMES_NUM]) > 0

def ends_with_speech(wave, start, end): 
    speech_array = get_speech_int_array(wave, start, end)
    #print 'end2: '+(''.join([str(x) for x in speech_array]))
    return np.sum(speech_array[-CHECK_FRAMES_NUM:]) > 0

def starts_or_ends_during_speech(wave, start, end):
    speech_array = get_speech_int_array(wave, start, end)
    #print_speech_int_array(speech_array)
    #print(len(speech_array))
    return np.sum(speech_array[-CHECK_FRAMES_NUM:]) > 0 or np.sum(speech_array[:CHECK_FRAMES_NUM]) > 0


MAX_ALLOWED_CORRECTION_SEC = 0.3
CORRECTION_WINDOW_SEC = SPEECH_FRAME_SEC*5 # needs to be multiple of whats used in VAD
def try_correct_cut(wave, start, end):
    if not starts_or_ends_during_speech(wave, start, end):
        return start, end

    #print 'try correct cut'

    #print_speech_int_array(get_speech_int_array(wave, start-MAX_ALLOWED_CORRECTION_SEC, end+MAX_ALLOWED_CORRECTION_SEC))

    corrected_start = start   
    corrected_end = end

    need_start_correction = starts_with_speech(wave, start, end)

    
    if need_start_correction:               
        #print("correct start")
        # try go forward
        while need_start_correction and corrected_start <= start + MAX_ALLOWED_CORRECTION_SEC:            
            corrected_start += CORRECTION_WINDOW_SEC
            need_start_correction = starts_with_speech(wave, corrected_start, end)

        # DISABLE backwards correction for start cause many bad samples with extra word on start
        if need_start_correction:
            #try go backwards
            corrected_start = start
            while need_start_correction and corrected_start >= start - MAX_ALLOWED_CORRECTION_SEC:            
                corrected_start -= CORRECTION_WINDOW_SEC
                need_start_correction = starts_with_speech(wave, corrected_start, end)

    if need_start_correction:
        return None



    need_end_correction = ends_with_speech(wave, start, end)
    

    if need_end_correction:
        #print("correct end")
        # try go forward
        while need_end_correction and corrected_end <= end + MAX_ALLOWED_CORRECTION_SEC:            
            corrected_end += CORRECTION_WINDOW_SEC
            need_end_correction = ends_with_speech(wave, corrected_start, corrected_end)

        if need_end_correction:
            # try go backwards
            corrected_end = end
            while need_end_correction and corrected_end >= end - MAX_ALLOWED_CORRECTION_SEC:            
                corrected_end -= CORRECTION_WINDOW_SEC
                need_end_correction = ends_with_speech(wave, corrected_start, corrected_end)

    if need_end_correction:
        #print 'FAILED to corrected_end'
        return None

    if corrected_start > corrected_end:
        return None

    #print 'SUCCESS corrected: %f-%f -> %f-%f' % (start, end, corrected_start, corrected_end)

    return (corrected_start, corrected_end)


def print_speech_int_array(speech_int_array):
    print ''.join([str(x) for x in speech_int_array])


def print_speech_frames(wave, start, end):

    wave_view_int = get_speech_int_array(wave, start, end)

    print_speech_int_array(wave_view_int)


    start_view = wave_view_int[:3]
    end_view = wave_view_int[-3:]

    #print  'start: '+(''.join([str(x) for x in start_view]))
    #print  'end: '+(''.join([str(x) for x in end_view]))

    is_speech_on_start = np.sum(start_view)  > 0
    is_speech_on_end = np.sum(end_view)  > 0

    

    #print 'is_speech_on_start: '+str(is_speech_on_start) 
    #print 'is_speech_on_end: '+str(is_speech_on_end)

    return is_speech_on_start or is_speech_on_end