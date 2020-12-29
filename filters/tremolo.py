import pyaudio
import struct
import math

def clip16( x ):
    # Clipping for 16 bits
    if x > 32767:
        x = 32767
    elif x < -32768:
        x = -32768
    else:
        x = x
    return(x)

BLOCKLEN   = 128        # Number of frames per block
WIDTH       = 2         # Bytes per sample
CHANNELS    = 1         # Mono
RATE        = 8000      # Frames per second

# Vibrato parameters
f0 = 2
W = 0.4   # W = 0 for no effect

alpha = 0.5

def tremolo(x0, n):
    # Get previous and next buffer values (since kr is fractional)
    y0 = []
    for i in range(len(x0)):
        # Compute output value using interpolation
        y0.append(int(clip16(x0[i] * (1 + alpha * math.sin( 2 * math.pi * f0 * n / RATE )))))

    return y0