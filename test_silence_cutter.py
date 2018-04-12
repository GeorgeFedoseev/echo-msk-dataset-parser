# =* coding: utf-8 *=

import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from utils import audio as audio_utils

import wave
import webrtcvad

data_path = os.path.join(os.getcwd(), 'data/test_silence_cutter')
test_file_path = os.path.join(data_path, 'test3.wav')
output_file_path = os.path.join(data_path, 'trimmed.wav')



def trim_silence(wave, output_file_path):
    vad = webrtcvad.Vad(3)   


    VAD_WINDOW_SEC = 0.01
    samples_per_second = wave.getframerate()
    samples_per_frame = int(VAD_WINDOW_SEC*samples_per_second)
    total_samples = wave.getnframes()


    #print('samples_step: %i' % samples_per_frame)
    wave_view_str = ""
    wave_view_int = []
    while wave.tell() < total_samples:
        #wave_view_str += "1" if vad.is_speech(wave.readframes(samples_to_get), sample_rate) else "0"
        try:
            wav_samples = wave.readframes(samples_per_frame)
            val = 1 if vad.is_speech(wav_samples, samples_per_second) else 0
            wave_view_int.append(val)       
            wave_view_str += str(val)
           #print "current_pos: %i" % wave.tell()
        except Exception as ex:
            print("Exception: "+str(ex))
            return []

    print wave_view_str
    #return wave_view_int 


trim_silence(wave.open(test_file_path), output_file_path)