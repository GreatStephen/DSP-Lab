import pyaudio
import wave
import struct
import math
import numpy as np
from scipy.signal import lfilter
import scipy.signal

def allpass(x, g, d, states):
    if g>=1:
        g=0.7
    b = np.array([g]+[0]*(d-1)+[1])
    a = np.array([1]+[0]*(d-1)+[g])
    y, states = lfilter(b, a, x, zi=states)
    y = np.array(y).astype(float)
    return [y, b, a], states

def seriescoefficients(b1, a1, b2, a2):
    b = np.convolve(b1, b2)
    a = np.convolve(a1, a2)
    return [b, a]

def schroeder_pre(RATE):
    n = 6
    g = 0.9
    d = (np.floor(0.05*RATE*np.random.rand(n))).astype(int)
    k = 0.2
    states_list = [np.zeros(tmp_d) for tmp_d in d]
    return n, g, d, k, states_list

def schroeder(x, n, g, d, k, states_list, gain=1, MAXVALUE=2**15-1):
    x = np.array(x)/MAXVALUE
    states_list_tmp = [0]*len(states_list)
    [y, b, a], states_list_tmp[0] = allpass(x, g, d[0], states_list[0])
    for i in range(1, n):
        [y, b1, a1], states_list_tmp[i] = allpass(y, g, d[i], states_list[i])
        [b, a] = seriescoefficients(b1, a1, b, a)
    y = np.array(y)
    y = y + k*x
    # y = y/np.max(y)        
    y = MAXVALUE*y*gain
    y = np.clip(y, -MAXVALUE, MAXVALUE) # clipping
    y = y.astype(int) # convert to integer

    return [y, b, a], states_list_tmp

if __name__ == '__main__':
    wavfile = 'acoustic.wav'
    output_wavfile = 'out_schroederreverb_python.wav'
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
    
    n, g, d, k, states_list = schroeder_pre(RATE)
    while len(binary_data) == WIDTH*BLOCKLEN:
        input_block = struct.unpack('h'*BLOCKLEN, binary_data)
                
        [output_block, b, a], states_list = schroeder(input_block, n, g, d, k, states_list)

        binary_data = struct.pack('h' * BLOCKLEN, *output_block) # Convert output value to binary data
        stream.write(binary_data) # Write binary data to audio stream
        # output_wf.writeframes(binary_data)# Write binary data to output wave file
        binary_data = wf.readframes(BLOCKLEN) # Get next frame from wave file

    print('* Finished')
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf.close() # Close wavefiles
    # output_wf.close()