# Ring Modulation with triangular wave

import pyaudio
import wave
import struct
import math
import numpy as np
from scipy.signal import lfilter
import scipy.signal

def tremolo2(x, trem_prev, gain=1, delta=5e-4, minf=-0.5, maxf=0.5, MAXVALUE=2**15-1):
    x = np.array(x)/MAXVALUE
    trem_prev = list(trem_prev)
    while len(trem_prev)<len(x):
        trem_prev += list(np.arange(minf, maxf, delta)) + list(np.arange(maxf, minf, -delta))
    trem = np.array(trem_prev[:len(x)])
    trem_next = np.array(trem_prev[len(x):])
    y = x*trem
    y = MAXVALUE*y*gain
    y = np.clip(y, -MAXVALUE, MAXVALUE) # clipping
    y = y.astype(int) # convert to integer
    return y, trem_next

if __name__ == '__main__':
    wavfile = 'acoustic.wav'
    output_wavfile = 'out_tremolo2_python.wav'
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

    trem = []
    while len(binary_data) == WIDTH*BLOCKLEN:
        input_block = struct.unpack('h'*BLOCKLEN, binary_data)
        
        output_block, trem = tremolo2(input_block, trem)
        
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