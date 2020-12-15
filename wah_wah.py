import pyaudio
import wave
import struct
import math
import numpy as np
import scipy.signal

def wah_wah(x, Fc_prev, RATE, last_pair, damp=0.05, minf=500, maxf=3000, Fw=2000, MAXVALUE=2**15-1):
    x = np.array(x)/MAXVALUE
    
    delta = Fw/RATE
    while len(Fc_prev)<len(x):
        Fc_prev += list(np.arange(minf, maxf, delta)) + list(np.arange(maxf, minf, -delta))
    Fc = Fc_prev[:len(x)]
    Fc_next = Fc_prev[len(x):]

    F1 = 2*math.sin((math.pi*Fc[0])/RATE)
    yb = np.zeros(len(x)+1)
    yl = np.zeros(len(x)+1)
    yh = np.zeros(len(x)+1)

    yh[0] = last_pair[0]
    yb[0] = last_pair[1]
    yl[0] = last_pair[2]
    for n in range(1, len(x)):
        yh[n] = x[n] - yl[n-1] - 2*damp*yb[n-1]
        yb[n] = F1*yh[n] + yb[n-1]
        yl[n] = F1*yb[n] + yl[n-1]    
        F1 = 2*math.sin((math.pi*Fc[n])/RATE)
    # yb = yb/np.max(np.abs(yb))
    yb = np.array(yb[1:])
    yb = MAXVALUE*yb
    yb = np.clip(yb, -MAXVALUE, MAXVALUE) # clipping
    yb = yb.astype(int) # convert to integer
    return yb, Fc_next, [yh[-1], yb[-1], yl[-1]]

if __name__ == '__main__':
    wavfile = 'acoustic.wav'
    output_wavfile = 'out_wah_python.wav'
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

    BLOCKLEN = 148799
    BLOCKLEN = 128
    MAXVALUE = 2**15-1  # Maximum allowed output signal value (because WIDTH = 2)
    binary_data = wf.readframes(BLOCKLEN) # Get first set of frame from wave file

    # ------------------- all frame at once -------------------
    # Fc = []
    # input_block = struct.unpack('h'*BLOCKLEN, binary_data)
    # input_block = np.array(input_block)/RATE
    # output_block, Fc = wah_wah(input_block, Fc, RATE)
    # output_block = output_block/5
    # output_block = MAXVALUE*output_block # divide 10 due to too loud
    # output_block = np.clip(output_block, -MAXVALUE, MAXVALUE) # clipping
    # output_block = output_block.astype(int) # convert to integer
    # binary_data = struct.pack('h'*BLOCKLEN, *output_block) # Convert output value to binary data
    # stream.write(binary_data) # Write binary data to audio stream
    # output_wf.writeframes(binary_data)# Write binary data to output wave file

    Fc = []
    st = [0, 0, 0]
    while len(binary_data) == WIDTH*BLOCKLEN:
        input_block = struct.unpack('h'*BLOCKLEN, binary_data)
        
        output_block, Fc, st = wah_wah(input_block, Fc, RATE, st)
        
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