import pyaudio, struct
import numpy as np
from scipy import signal
from math import sin, cos, pi
import tkinter as Tk   
import math 
from overdrive import overdrive
from robotization import robotization
from ring_mod import ring_mod
from moorer import moorer, moorer_pre
from reverb_convolution import reverb_convolution, clic_pre
from shelving import shelving, shelving_pre
from reverb_schroeder import schroeder, schroeder_pre
from tremolo2 import tremolo2
# from chorus import chorus

# ---------------------------- Parameters -----------------------------
BLOCKLEN   = 128        # Number of frames per block
WIDTH       = 2         # Bytes per sample
CHANNELS    = 1         # Mono
RATE        = 8000      # Frames per second

MAXVALUE = 2**15-1  # Maximum allowed output signal value (because WIDTH = 2)

Ta = 1      # Decay time (seconds)
f0 = 440    # Frequency (Hz)

# Buffer to store past signal values. Initialize to zero.
BUFFER_LEN =  2048          # Set buffer length.
buffer = BUFFER_LEN * [0]   # list of zeros

# Buffer (delay line) indices
kr = 0  # read index
kw = int(0.5 * BUFFER_LEN)  # write index (initialize to middle of buffer)

# Pole radius and angle
r = 0.01**(1.0/(Ta*RATE))       # 0.01 for 1 percent amplitude

# triangle window
triangle_window = [1-abs(2*i/(BLOCKLEN-1) - 1) for i in range(BLOCKLEN)]

ORDER = 2   # filter order
states, x, output = [], [], []
for i in range(13):
    states.append(np.zeros(ORDER))
    x.append(np.zeros(BLOCKLEN))
    output.append(np.zeros(BLOCKLEN))

keys = {'a':0, 'z':1, 's':2, 'x':3, 'd':4, 'c':5, 'f':6, 'v':7, 'g':8, 'b':9, 'h':10, 'n':11, 'j':12}


CONTINUE = True
FROMMIC = False

# for chrous
n = 0
# for overdrive
ring_mod_index = 0
# for reverb schroeder
n_sch, g_sch, d_sch, k_sch, states_list_sch = schroeder_pre(RATE)
# for reverb moorer
cd_moor, g1_moor, g2_moor, cg_moor, cg1_moor, ag_moor, ad_moor, k_moor, gain_moor, states_list_moor = moorer_pre(RATE)
# for reverb convolution
clicfile = 'impulse_room.wav'
imp_rc, keep_rc = clic_pre(clicfile, BLOCKLEN)
# for shelving
shel_type = 'Treble_Shelf' # Base_Shelf or Treble_Shelf
[b_shel, a_shel], states_shel = shelving_pre(RATE, shel_type)
# tremolo2
trem = []


#----------------------------------------- UI ---------------------------
def keyPressed(event):
    global CONTINUE
    global a, b, output, states
    if event.char == 'q':
        print('Good bye')
        CONTINUE = False
    if not FROMMIC and event.char in keys:
        print('You pressed ' + event.char)
        x[keys[event.char]][0] = 10000.0

def inputFromMic():
    global FROMMIC
    if FROMMIC:
        FROMMIC = False
        sourceInfo.set('Sound comes from keyboard')
    else:
        FROMMIC = True
        sourceInfo.set('Sound comes from Mic')

# UI elements
root = Tk.Tk()
root.bind("<Key>", keyPressed)
sourceInfo = Tk.StringVar()
sourceInfo.set('Sound comes from keyboard')
overdriveInfo = Tk.StringVar()
overdriveInfo.set('Select the overdrive type')
SOURCEINFO = Tk.Label(root, textvariable = sourceInfo)
OVERDRIVEINFO = Tk.Label(root, textvariable = overdriveInfo)
MIC = Tk.Button(root, text = 'Source', command = inputFromMic)
distortionType = Tk.Listbox(root)
distortionType.insert(Tk.END, 'None')
distortionType.insert(Tk.END, 'HardClipping')
distortionType.insert(Tk.END, 'SoftClipping')
distortionType.insert(Tk.END, 'SoftClippingExponential')
distortionType.insert(Tk.END, 'HalfWaveRectifier')
distortionType.insert(Tk.END, 'FullWaveRectifier')
distortionType.select_set(first=0)

MIC.pack(side = Tk.BOTTOM)
SOURCEINFO.pack(side = Tk.BOTTOM)
distortionType.pack(side = Tk.BOTTOM)
OVERDRIVEINFO.pack(side = Tk.BOTTOM)

print('Press keys "azsxdcfvgbhnj" for sound.')
print('Press "q" to quit')


#--------------------------------------------- Stream -------------------------
# Open the audio output stream
p = pyaudio.PyAudio()
PA_FORMAT = pyaudio.paInt16
stream = p.open(
        format      = PA_FORMAT,
        channels    = CHANNELS,
        rate        = RATE,
        input       = True,
        output      = True,
        frames_per_buffer = 128)
# specify low frames_per_buffer to reduce latency


#---------------------------------------------- Main Loop --------------
while CONTINUE:
    root.update()
    if not FROMMIC:
        res = np.zeros(BLOCKLEN)
        for i in range(13):
            fk = math.pow(2, float(i)/13) * f0
            om1 = 2.0 * pi * float(fk)/RATE
            a = [1, -2*r*cos(om1), r**2]
            b = [r*sin(om1)]
            [output[i], states[i]] = signal.lfilter(b, a, x[i], zi = states[i])
            x[i][0] = 0.0
            res = np.array(res) + np.array(output[i])
        # Clipping
        y = np.clip(res.astype(int), -MAXVALUE, MAXVALUE)  
    else:
        input_bytes = stream.read(BLOCKLEN)
        y = struct.unpack('h' * BLOCKLEN * CHANNELS, input_bytes)


    # y is the input

    # overdrive
    # y = overdrive(y, distortionType.curselection()[0])

    # robotization
    # y = robotization(y, triangle_window, 5)
    
    # Tianshu
    # y, kr, kw, buffer = chorus(y, kr, kw, buffer, n)
    # n += 1

    # ring modulation
    # y, ring_mod_index = ring_mod(y, ring_mod_index, RATE)

    # for reverb schroeder
    # [y, b, a], states_list_sch = schroeder(y, n_sch, g_sch, d_sch, k_sch, states_list_sch)

    # reverb moorer
    # [y, b, a], states_list_moor = moorer(y, cg_moor, cg1_moor, cd_moor, ag_moor, ad_moor, k_moor, gain_moor, states_list_moor)

    # reverb convoluton
    # y, keep_rc = reverb_convolution(y, imp_rc, keep_rc, BLOCKLEN)

    # shelving: Base_Shelf or Treble_Shelf
    # y, states_shel = shelving(b_shel, a_shel, y, states_shel)

    # tremolo2
    # y, trem = tremolo2(y, trem)


    binary_data = struct.pack('h' * BLOCKLEN * CHANNELS, *y);    # Convert to binary binary data
    stream.write(binary_data, BLOCKLEN * CHANNELS)               # Write binary binary data to audio output

print('* Done.')

# Close audio stream
stream.stop_stream()
stream.close()
p.terminate()
