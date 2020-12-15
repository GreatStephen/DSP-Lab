import pyaudio
import wave
import struct
import math
import numpy as np
from scipy.signal import lfilter
import scipy.signal

def lpcomb(x, g, g1, d, states):
    if g>=1:
        g=0.7
    if g1>=1:
        g1=0.7
    b = np.array([0]*d+[1]+[-g1])
    a = np.array([1]+[-g1]+[0]*(d-1)+[-g*(1-g1)])
    y, states = lfilter(b, a, x, zi=states)
    # y = lfilter(b, a, x)
    y = np.array(y).astype(float)
    return [y, b, a], states

def seriescoefficients(b1, a1, b2, a2):
    b = np.convolve(b1, b2)
    a = np.convolve(a1, a2)
    return [b, a]

def parallelcoefficients(b1, a1, b2, a2):
    b = np.convolve(b1, a2)+np.convolve(b2, a1)
    a = np.convolve(a1, a2)
    return [b, a]

def allpass(x, g, d, states):
    if g>=1:
        g=0.7
    b = np.array([g]+[0]*(d-1)+[1])
    a = np.array([1]+[0]*(d-1)+[g])
    y, states = lfilter(b, a, x, zi=states)
    # y = lfilter(b, a, x)
    y = np.array(y).astype(float)
    return [y, b, a], states

def moorer_pre(RATE):
    cd = (np.floor(0.05*RATE*np.random.rand(6))).astype(int)
    g1 = 0.5*np.array([1]*6)
    g2 = 0.5*np.array([1]*6)
    cg = g2*(1-g1)
    cg1 = g1
    ag = 0.7
    ad = int(0.08*RATE)
    k = 0.5
    gain = 0.8
    states_list = [np.zeros(tmp_d+1) for tmp_d in cd]+[np.zeros(ad)]
    return cd, g1, g2, cg, cg1, ag, ad, k, gain, states_list

def moorer(x, cg, cg1, cd, ag, ad, k, gain, states_list, MAXVALUE=2**15-1):
    x = np.array(x)/MAXVALUE

    [outcomb1, b1, a1], states_list[0] = lpcomb(x, cg[0], cg1[0], cd[0], states_list[0])
    [outcomb2, b2, a2], states_list[1] = lpcomb(x, cg[1], cg1[1], cd[1], states_list[1])
    [outcomb3, b3, a3], states_list[2] = lpcomb(x, cg[2], cg1[2], cd[2], states_list[2])
    [outcomb4, b4, a4], states_list[3] = lpcomb(x, cg[3], cg1[3], cd[3], states_list[3])
    [outcomb5, b5, a5], states_list[4] = lpcomb(x, cg[4], cg1[4], cd[4], states_list[4])
    [outcomb6, b6, a6], states_list[5] = lpcomb(x, cg[5], cg1[5], cd[5], states_list[5])

    apinput = outcomb1 + outcomb2 + outcomb3 + outcomb4 + outcomb5 + outcomb6

    [b, a] = parallelcoefficients(b1, a1, b2, a2)
    [b, a] = parallelcoefficients(b, a, b3, a3)
    [b, a] = parallelcoefficients(b, a, b4, a4)
    [b, a] = parallelcoefficients(b, a, b5, a5)
    [b, a] = parallelcoefficients(b, a, b6, a6)

    [y, b7, a7], states_list[6] = allpass(apinput, ag, ad, states_list[6])
    [b, a] = seriescoefficients(b, a, b7, a7)
    y = y + k*x
    # y = y/max(y)
    y = np.array(y).astype(float)
    y = MAXVALUE*y*gain
    y = np.clip(y, -MAXVALUE, MAXVALUE) # clipping
    y = y.astype(int) # convert to integer
    return [y, b, a], states_list

if __name__ == '__main__':
    wavfile = 'acoustic.wav'
    output_wavfile = 'out_moorerreverb_python.wav'
    wf = wave.open( wavfile, 'rb') # Open wave file (should be mono channel)

    CHANNELS        = wf.getnchannels()     # Number of channels
    RATE            = wf.getframerate()     # Sampling rate (frames/second)
    signal_length   = wf.getnframes()       # Signal length
    WIDTH           = wf.getsampwidth()     # Number of bytes per sample

    output_wf = wave.open(output_wavfile, 'w')      # wave file
    output_wf.setframerate(RATE)
    output_wf.setsampwidth(WIDTH)
    output_wf.setnchannels(CHANNELS)
    p = pyaudio.PyAudio()

    stream = p.open( # Open audio stream
        format      = p.get_format_from_width(WIDTH),
        channels    = CHANNELS,
        rate        = RATE,
        input       = False,
        output      = True)


    # BLOCKLEN = 148799
    BLOCKLEN = 128
    MAXVALUE = 2**15-1  # Maximum allowed output signal value (because WIDTH = 2)
    binary_data = wf.readframes(BLOCKLEN) # Get first set of frame from wave file

    cd, g1, g2, cg, cg1, ag, ad, k, gain, states_list = moorer_pre(RATE)
    
    # ------------------- separate frame -------------------
    while len(binary_data) == WIDTH*BLOCKLEN:
        input_block = struct.unpack('h'*BLOCKLEN, binary_data)
        
        [output_block, b, a], states_list = moorer(input_block, cg, cg1, cd, ag, ad, k, gain, states_list)

        binary_data = struct.pack('h' * BLOCKLEN, *output_block) # Convert output value to binary data
        stream.write(binary_data) # Write binary data to audio stream
        output_wf.writeframes(binary_data)# Write binary data to output wave file
        binary_data = wf.readframes(BLOCKLEN) # Get next frame from wave file

    print('* Finished')
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf.close() # Close wavefiles
    output_wf.close()