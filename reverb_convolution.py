import pyaudio
import wave
import struct
import math
import numpy as np
from scipy.signal import lfilter
import scipy.signal
from scipy.fft import fft, ifft

def clic_pre(filename, BLOCKLEN, MAXVALUE=2**15-1):
    cf = wave.open(filename, 'rb')
    Fs_imp            = cf.getframerate()     # Sampling rate (frames/second)
    binary_data_imp = cf.readframes(1000000)  # get the maximum len 2205
    binary_data_imp_len = len(binary_data_imp)//2
    input_block_imp = struct.unpack('h'*binary_data_imp_len, binary_data_imp) # all cf frame data
    input_block_imp = np.array(input_block_imp)/MAXVALUE
    keep = np.zeros(BLOCKLEN+binary_data_imp_len-1)
    return input_block_imp, keep

def reverb_convolution(x, h, keep, BLOCKLEN, MAXVALUE=2**15-1):
    x = np.array(x)/MAXVALUE
    Ly = len(x)+len(h)-1
    Ly2_idx = 0
    while 2**Ly2_idx<=Ly:
        Ly2_idx+=1
    Ly2 = 2**Ly2_idx
    X = fft(x, Ly2)
    H = fft(h, Ly2)
    X = np.array(X)
    H = np.array(H)
    Y = X*H
    y = np.real(ifft(Y, Ly2))
    y = y[:Ly]
    # y = y/np.max(np.abs(y))
    y = MAXVALUE*y
    keep = y+keep
    y = keep[:BLOCKLEN]
    keep = np.concatenate((keep[BLOCKLEN:], np.zeros(BLOCKLEN)), axis=None)
    y = np.clip(y, -MAXVALUE, MAXVALUE) # clipping
    y = y.astype(int) # convert to integer
    return y, keep

if __name__ == '__main__':
    wavfile = 'acoustic.wav'
    output_wavfile = 'out_IRreverb_python.wav'
    wf = wave.open(wavfile, 'rb')
    
    CHANNELS        = wf.getnchannels()     # Number of channels
    Fs            = wf.getframerate()     # Sampling rate (frames/second)
    signal_length   = wf.getnframes()       # Signal length
    WIDTH           = wf.getsampwidth()     # Number of bytes per sample

    output_wf = wave.open(output_wavfile, 'w')      # wave file
    output_wf.setframerate(Fs)
    output_wf.setsampwidth(WIDTH)
    output_wf.setnchannels(CHANNELS)
    p = pyaudio.PyAudio()

    stream = p.open( # Open audio stream
        format      = p.get_format_from_width(WIDTH),
        channels    = CHANNELS,
        rate        = Fs,
        input       = False,
        output      = True)

    MAXVALUE = 2**15-1  # Maximum allowed output signal value (because WIDTH = 2)
    # BLOCKLEN = 148799
    BLOCKLEN = 128
    binary_data = wf.readframes(BLOCKLEN) # Get first set of frame from wave file

    clicfile = 'impulse_room.wav'
    input_block_imp, keep = clic_pre(clicfile, BLOCKLEN)
    while len(binary_data) == WIDTH*BLOCKLEN:
        input_block = struct.unpack('h'*BLOCKLEN, binary_data)
        
        output_block, keep = reverb_convolution(input_block, input_block_imp, keep, BLOCKLEN)

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