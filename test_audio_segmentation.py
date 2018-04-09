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
    #print("framerate: %i" % rate)
    totlal_samples = wave_obj.getnframes()
    #print("totlal_samples: %i" % totlal_samples)
    #print("length in sec: %f" % (float(totlal_samples)/rate))
    _window_size = int(rate * SPEECH_DETECT_SEC)
    #wave.setpos(start*samples_per_second)

    wave_view_int = []
    while wave_obj.tell() < totlal_samples:
        try:
            wave_view_int.append(1 if vad.is_speech(wave_obj.readframes(_window_size), rate) else 0)
        except:
            print("error processing")
        #try:
            #wave_obj.setpos(wave_obj.tell() + _window_size)   
        #except:
        #    break

    return wave_view_int

def _movingaverage(lst, N):
    cumsum, moving_aves = [0], []

    for i, x in enumerate(lst, 1):
        cumsum.append(cumsum[i-1] + x)
        if i>=N:
            moving_ave = (cumsum[i] - cumsum[i-N])/N
            #can do stuff with moving_ave here
            moving_aves.append(moving_ave)

    return moving_aves

def movingaverage(lst, N):    
    moving_aves = []

    for i, x in enumerate(lst):
        start = max(0, i - int(N/2))
        end = min(len(lst), i + int(N/2))         
        piece = lst[start:end]

        moving_aves.append(np.sum(piece)/len(piece))

    return moving_aves


    



def get_speech_density_arr(wav_file):

    speech_detected_arr = get_speech_int_array(wav_file)

    print("speech_detected_arr len: %i" % len(speech_detected_arr))

    length_sec = int(len(speech_detected_arr)*SPEECH_DETECT_SEC)

    DENSITY_WINDOW_SEC = 5
    bin_size = int(float(DENSITY_WINDOW_SEC)/SPEECH_DETECT_SEC)
    speech_density = []

    bins_num = int(len(speech_detected_arr)/bin_size)

    for s in range(0, length_sec):
        start = int(float(s)/SPEECH_DETECT_SEC)
        end = start + int(DENSITY_WINDOW_SEC/SPEECH_DETECT_SEC)

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
        start = int(float(s)*rate)
        end = start + int(ENERGY_WINDOW_SEC*rate)        
        speech_energy.append(abs(np.average(np.abs(data[start:end])))/total_average)

    return speech_energy


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



speech_density = get_speech_density_arr(WAV_FILE)
speech_density_ma = movingaverage(speech_density, N=100)
plt.plot(speech_density_ma)


speech_energy = get_speech_energy_arr(WAV_FILE)
speech_energy_ma = movingaverage(speech_energy, N=ENERGY_SMOOTH)
plt.plot(speech_energy_ma)
plt.plot([1 if x > ENERGY_THRESH else 0 for x in speech_energy_ma])

ads_intervals = get_commercial_intervals(WAV_FILE)
for ad in ads_intervals:
    print "%s - %s" % ( str(datetime.timedelta(seconds=ad[0])), str(datetime.timedelta(seconds=ad[1])) )

plt.show()


