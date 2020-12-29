import pyaudio, struct, wave, math
import numpy as np

def clip16( x ):    
    # Clipping for 16 bits
    if x > 32767:
        x = 32767
    elif x < -32768:
        x = -32768
    else:
        x = x        
    return (x)	

def robotization(y, window, gain, MAXVALUE=2**15-1):
    y_len = len(y)
    
    # window function
    y_fft = [val*win for val,win in zip(y, window)]
    y_fft = np.fft.fft(np.array(y_fft))
    y_output = []

    for i in range(len(y_fft)):
        freq = y_fft[i]
        amplitude = math.sqrt(freq.real**2 + freq.imag**2)
        y_output.append(int(amplitude))
    
    y_ifft = np.fft.ifft(y_output)
    y_ifft = list(map(lambda x: clip16(int(x.real)), y_ifft))
    y_ifft = np.array(y_ifft)
    y_ifft = y_ifft*gain
    y_ifft = np.clip(y_ifft, -MAXVALUE, MAXVALUE) # clipping
    y_ifft = y_ifft.astype(int) # convert to integer
    return y_ifft