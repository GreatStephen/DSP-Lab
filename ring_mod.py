import pyaudio
import wave
import struct
import math
import numpy as np
from scipy.signal import lfilter
import scipy.signal

def ring_mod(x, index, RATE, Fc=440, MAXVALUE=2**15-1):
    x = np.array(x)/MAXVALUE
    index_array = np.arange(index, index+len(x))
    carrier = np.sin(2*math.pi*index_array*(Fc/RATE))
    output_block = x*carrier
    output_block = MAXVALUE*output_block
    output_block = np.clip(output_block, -MAXVALUE, MAXVALUE) # clipping
    output_block = output_block.astype(int) # convert to integer
    return output_block, index_array[-1]+1

if __name__ == '__main__':
    wavfile = 'acoustic.wav'
    output_wavfile = 'out_ringmod_python.wav'
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

    # ------------------- separate frame -------------------
    index = 0
    while len(binary_data) == WIDTH*BLOCKLEN:
        input_block = struct.unpack('h'*BLOCKLEN, binary_data)
        
        output_block, index = ring_mod(input_block, index, RATE)
        
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