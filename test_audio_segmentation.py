import matplotlib.pyplot as plt
from scipy.io import wavfile as wav

import wave

import numpy as np
import audioop

import webrtcvad

import datetime

WAV_FILE = 'data/test.wav'





BITRATE = 16
BYTE_WIDTH = BITRATE/8

SPEECH_DETECT_SEC = 0.01

def get_speech_int_array(wav_file_path):
    vad = webrtcvad.Vad(3)
    wave_obj = wave.open(WAV_FILE)
    rate = wave_obj.getframerate()
    totlal_samples = wave_obj.getnframes()
    _window_size = int(rate * SPEECH_DETECT_SEC)    

    wave_view_int = []
    while wave_obj.tell() < totlal_samples:
        try:
            wave_view_int.append(1 if vad.is_speech(wave_obj.readframes(_window_size), rate) else 0)
        except:
            print("error processing")
       
    return wave_view_int

def movingaverage(lst, N):    
    moving_aves = []

    for i, x in enumerate(lst):
        start = max(0, i - int(N/2))
        end = min(len(lst), i + int(N/2))         
        piece = lst[start:end]

        moving_aves.append(np.sum(piece)/len(piece))

    return moving_aves

def get_speech_intermittent_arr(wav_file):

    speech_intermittent = []
    rate, data = wav.read(WAV_FILE)
    length_sec = float(len(data))/rate
    total_average = np.average(np.abs(data))

    _WINDOW = 0.1
    _WINDOW_STEP = 0.05
    window_samples = _WINDOW_STEP*rate

    chunks_num = int(length_sec/_WINDOW_STEP)

    THRESH = 0.1

    vals = []   

    print "total_average: %f" % total_average

    for i in range(0, chunks_num):
        start = int(i*window_samples)
        end = int(i*window_samples+window_samples)
        chunk = data[start:end]
        vals.append(0 if np.average(np.abs(chunk))/total_average < THRESH else 1)

    vals_per_sec = 1.0/_WINDOW_STEP
    for i in range(0, int(length_sec)):
        start = int(i*vals_per_sec)
        end = int(i*vals_per_sec+vals_per_sec)
        speech_intermittent.append(0 if any([x == 0 for x in vals[start:end]]) else 1)



    return speech_intermittent



def get_speech_density_arr(wav_file):

    speech_detected_arr = get_speech_int_array(wav_file)

    print("speech_detected_arr len: %i" % len(speech_detected_arr))

    length_sec = int(len(speech_detected_arr)*SPEECH_DETECT_SEC)

    DENSITY_WINDOW_SEC = 5
    bin_size = int(float(DENSITY_WINDOW_SEC)/SPEECH_DETECT_SEC)
    speech_density = []

    bins_num = int(len(speech_detected_arr)/bin_size)

    for s in range(0, length_sec):
        center = int(float(s)/SPEECH_DETECT_SEC)
        width = int(DENSITY_WINDOW_SEC/SPEECH_DETECT_SEC)
        start = max(0, center-width/2)
        end = min(center+width/2, len(speech_detected_arr))

        speech_density.append(np.average(speech_detected_arr[start:end]))

    return speech_density

def get_speech_energy_arr(wav_file):
    speech_energy = []

    rate, data = wav.read(WAV_FILE)

    length_sec = int(float(len(data))/rate)

    total_average = np.average(np.abs(data))

    ENERGY_WINDOW_SEC = 2
    #print length_sec
    for s in range(0, length_sec):
        center = int(float(s)*rate)
        width = int(ENERGY_WINDOW_SEC*rate)
        start = max(0, center-width/2)
        end = min(center+width/2, len(data))
        speech_energy.append(abs(np.average(np.abs(data[start:end])))/total_average)

    return speech_energy

def get_intervals(wav_file):
    intervals = []

    speech_intermittent = get_speech_intermittent_arr(wav_file)
    speech_intermittent_ma = movingaverage(speech_intermittent, N=3)
    
    

    t_start = None
    prev_val = -1
    for t, x in enumerate(speech_intermittent_ma):

        if x != prev_val:
            if t_start != None:
                if t - t_start > 10:
                    intervals.append((t_start, t, prev_val))

            # start new interval
            t_start = t

        prev_val = x

    # concat intervals
    concat_intervals = []
    prev_interval = None
    t_start = 0
    for interval in intervals:
        val = interval[2]

        if prev_interval:
            prev_val = prev_interval[2]

            if val != prev_val:            
                # close current interval
                concat_intervals.append((t_start, prev_interval[1], prev_val))
                # start new interval
                t_start = interval[0]
        else:
            t_start = 0

        prev_interval = interval

    # close last interval
    concat_intervals.append((t_start, intervals[-1][1], prev_interval[2]))



    return concat_intervals


def get_val_for_t_in_intervals(t, intervals):
    for interval in intervals:
        if t >= interval[0] and t <= interval[1]:
            return interval[2]
    return 0

def intervals_to_bool_arr(intervals):
    arr = []
    if len(intervals) > 0:        
        max_t = intervals[-1][1]

        for t in range(0, max_t):
            arr.append(get_val_for_t_in_intervals(t, intervals))

    return arr

ENERGY_THRESH = 1.1
ENERGY_SMOOTH = 30
def get_commercial_intervals(wav_file):
    speech_energy = get_speech_energy_arr(wav_file)
    speech_energy_ma = movingaverage(speech_energy, N=ENERGY_SMOOTH)

    intervals = []

    

    t_start = None
    for t, x in enumerate(speech_energy_ma):

        if x > ENERGY_THRESH:
            if t_start == None:
                t_start = t
        else:
            if t_start != None:
                if t - t_start > 5: # longer than 5 sec
                    intervals.append((t_start, t))
                t_start = None
    return intervals



# speech_density = get_speech_density_arr(WAV_FILE)
# speech_density_ma = movingaverage(speech_density, N=100)
# plt.plot(speech_density_ma)


speech_energy = get_speech_energy_arr(WAV_FILE)
speech_energy_ma = movingaverage(speech_energy, N=ENERGY_SMOOTH)
plt.plot(speech_energy_ma)
#plt.plot([1 if x > ENERGY_THRESH else 0 for x in speech_energy_ma])

speech_intermittent = get_speech_intermittent_arr(WAV_FILE)
speech_intermittent_ma = movingaverage(speech_intermittent, N=5)
#plt.plot(speech_intermittent_ma, linestyle='-', marker='', markersize=0.5)


intervals = get_intervals(WAV_FILE)

plt.plot(intervals_to_bool_arr(intervals))


for interval in intervals:
    print "%s - %s: %i" % ( str(datetime.timedelta(seconds=interval[0])), str(datetime.timedelta(seconds=interval[1])), interval[2] )




# ads_intervals = get_commercial_intervals(WAV_FILE)
# for ad in ads_intervals:
#     print "%s - %s" % ( str(datetime.timedelta(seconds=ad[0])), str(datetime.timedelta(seconds=ad[1])) )

plt.show()


