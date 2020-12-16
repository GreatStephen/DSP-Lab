import pyaudio
import wave
import struct
import math
import numpy as np
from scipy.signal import lfilter
import scipy.signal


def shelving_pre(RATE, dtype):
    if dtype not in ["Base_Shelf", "Treble_Shelf"]: return

    if dtype == 'Base_Shelf':
        G = 4
        fc = 500
        Q = 3
    else:
        G = 4
        fc = 700
        Q = 3

    K = math.tan((math.pi * fc)/RATE)
    V0 = 10**(G/20)
    root2 = 1/Q
    if V0 < 1: V0 = 1/V0
    if G > 0 and dtype == "Base_Shelf":
        b0 = (1 + np.sqrt(V0)*root2*K + V0*(K**2)) / (1 + root2*K + (K**2))
        b1 =             (2 * (V0*(K**2) - 1) ) / (1 + root2*K + (K**2))
        b2 = (1 - np.sqrt(V0)*root2*K + V0*(K**2)) / (1 + root2*K + (K**2))
        a1 =                (2 * ((K**2) - 1) ) / (1 + root2*K + (K**2))
        a2 =             (1 - root2*K + (K**2)) / (1 + root2*K + (K**2))
    elif G < 0 and dtype == "Base_Shelf":
        b0 =             (1 + root2*K + (K**2)) / (1 + root2*np.sqrt(V0)*K + V0*(K**2))
        b1 =                (2 * ((K**2) - 1) ) / (1 + root2*np.sqrt(V0)*K + V0*(K**2))
        b2 =             (1 - root2*K + (K**2)) / (1 + root2*np.sqrt(V0)*K + V0*(K**2))
        a1 =             (2 * (V0*(K**2) - 1) ) / (1 + root2*np.sqrt(V0)*K + V0*(K**2))
        a2 = (1 - root2*np.sqrt(V0)*K + V0*(K**2)) / (1 + root2*np.sqrt(V0)*K + V0*(K**2))
    elif G > 0 and dtype == "Treble_Shelf":
        b0 = (V0 + root2*np.sqrt(V0)*K + (K**2)) / (1 + root2*K + (K**2))
        b1 =             (2 * ((K**2) - V0) ) / (1 + root2*K + (K**2))
        b2 = (V0 - root2*np.sqrt(V0)*K + (K**2)) / (1 + root2*K + (K**2))
        a1 =              (2 * ((K**2) - 1) ) / (1 + root2*K + (K**2))
        a2 =           (1 - root2*K + (K**2)) / (1 + root2*K + (K**2))
    elif G < 0 and dtype == "Treble_Shelf":
        b0 =               (1 + root2*K + (K**2)) / (V0 + root2*np.sqrt(V0)*K + (K**2))
        b1 =                  (2 * ((K**2) - 1) ) / (V0 + root2*np.sqrt(V0)*K + (K**2))
        b2 =               (1 - root2*K + (K**2)) / (V0 + root2*np.sqrt(V0)*K + (K**2))
        a1 =             (2 * (((K**2))/V0 - 1) ) / (1 + root2/np.sqrt(V0)*K + ((K**2))/V0)
        a2 = (1 - root2/np.sqrt(V0)*K + ((K**2))/V0) / (1 + root2/np.sqrt(V0)*K + ((K**2))/V0)
    else:
        b0 = V0
        b1 = 0
        b2 = 0
        a1 = 0
        a2 = 0
    a = [  1, a1, a2]
    b = [ b0, b1, b2]
    
    states = np.zeros(len(b)-1)
    return [b, a], states

def shelving(b, a, input_block, states, MAXVALUE=2**15-1):
    input_block = np.array(input_block)/MAXVALUE
    output_block, states = lfilter(b, a, input_block, zi=states)
    output_block = MAXVALUE*output_block
    output_block = np.clip(output_block, -MAXVALUE, MAXVALUE) # clipping
    output_block = output_block.astype(int) # convert to integer
    return output_block, states

if __name__ == '__main__':
    wavfile = 'acoustic.wav'
    dtype = 'Treble_Shelf' # Base_Shelf or Treble_Shelf
    
    output_wavfile = 'out_bassshelf_python.wav' if dtype == 'Base_Shelf' else 'out_treblehelf_python.wav'
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

    [b, a], states = shelving_pre(RATE, dtype)
    while len(binary_data) == WIDTH*BLOCKLEN:
        input_block = struct.unpack('h'*BLOCKLEN, binary_data)

        output_block, states = shelving(b, a, input_block, states)
        
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