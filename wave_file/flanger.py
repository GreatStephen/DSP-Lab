import pyaudio
import wave
import struct
import math
import numpy as np
from myfunctions import clip16

# Vibrato parameters
f0 = 2
W = 0.4   # W = 0 for no effect

# Buffer to store past signal values. Initialize to zero.
BUFFER_LEN =  1024          # Set buffer length.
buffer = BUFFER_LEN * [0]   # list of zeros

# Buffer (delay line) indices
kr = 0  # read index
kw = int(0.5 * BUFFER_LEN)  # write index (initialize to middle of buffer)

def flanger(x0, kr, kw, buffer, n, RATE, gain=1, MAXVALUE=2**15-1):
    # Get previous and next buffer values (since kr is fractional)
    y0 = []
    for i in range(len(x0)):
        kr_prev = int(math.floor(kr))
        frac = kr - kr_prev    # 0 <= frac < 1
        kr_next = kr_prev + 1
        if kr_next == BUFFER_LEN:
            kr_next = 0

        # Compute output value using interpolation
        y0.append(int(clip16(x0[i] + 0.5*((1-frac) * buffer[kr_prev] + frac * buffer[kr_next]))))

        # Update buffer
        buffer[kw] = x0[i]

        # Increment read index
        kr = kr + 1 - W * (1 - math.cos( 2 * math.pi * f0 * n / RATE ))
        # Note: kr is fractional (not integer!)

        # Ensure that 0 <= kr < BUFFER_LEN
        if kr >= BUFFER_LEN:
            # End of buffer. Circle back to front.
            kr = kr - BUFFER_LEN

        # Increment write index    
        kw = kw + 1
        if kw == BUFFER_LEN:
            # End of buffer. Circle back to front.
            kw = 0
    y0 = np.array(y0)
    y0 = y0*gain
    y0 = np.clip(y0, -MAXVALUE, MAXVALUE) # clipping
    y0 = y0.astype(int) # convert to integer
    return y0, kr, kw, buffer