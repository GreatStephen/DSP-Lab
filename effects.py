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
from wah_wah import wah_wah
from chorus import chorus
from flanger import flanger
from tremolo import tremolo

# ---------------------------- Parameters -----------------------------
BLOCKLEN   = 1024        # Number of frames per block
WIDTH       = 2         # Bytes per sample
CHANNELS    = 1         # Mono
RATE        = 8000      # Frames per second

MAXVALUE = 2**15-1  # Maximum allowed output signal value (because WIDTH = 2)

Ta = 1      # Decay time (seconds)
f0 = 440    # Frequency (Hz)

# Buffer to store past signal values. Initialize to zero.
BUFFER_LEN_CH =  2048          # Set buffer length.
BUFFER_LEN_FL = 1024
buffer_chorus, buffer_flanger = BUFFER_LEN_CH * [0], BUFFER_LEN_FL * [0]   # list of zeros

# Buffer (delay line) indices
kr_ch = 0  # read index
kw_ch = int(0.5 * BUFFER_LEN_CH)  # write index (initialize to middle of buffer)
kr_fl = 0  # read index
kw_fl = int(0.5 * BUFFER_LEN_FL)  # write index (initialize to middle of buffer)

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

output_gain_interval = 0.15

# for chrous
n = 0
# for overdrive
ring_mod_index = 0
# for reverb schroeder
n_sch, g_sch, d_sch, k_sch, states_list_sch = schroeder_pre(RATE)
# for reverb moorer
cd_moor, g1_moor, g2_moor, cg_moor, cg1_moor, ag_moor, ad_moor, k_moor, states_list_moor = moorer_pre(RATE)
# for reverb convolution
clicfile = 'impulse_room.wav'
imp_rc, keep_rc = clic_pre(clicfile, BLOCKLEN)
# for shelving
[b_base_shel, a_base_shel], states_base_shel = shelving_pre(RATE, "Base_Shelf")
[b_treb_shel, a_treb_shel], states_treb_shel = shelving_pre(RATE, "Treble_Shelf")
# tremolo2
trem = []
# wah wah
Fc_wah_wah = []
wah_wah_pair = [0, 0, 0]

#----------------------------------------- UI ---------------------------
CONTINUE = True
FROMMIC = False
ROBOTSTATUS = 0
RINGMODULESTATUS = 0
SCHROEDERSTATUS = 0
MOORERSTATUS = 0
REVERBCONVOLUTIONSTATUS = 0
TREMOLOSTATUS = 0
TREMOLO2STATUS = 0
WAHWAHSTATUS = 0
CHORUSSTATUS = 0
FLANGERSTATUS = 0


def keyPressed(event):
    global CONTINUE
    global a, b, output, states
    if event.char.lower() == 'q':
        print('Good bye')
        CONTINUE = False
    if not FROMMIC and event.char in keys:
        print('You pressed ' + event.char.lower())
        x[keys[event.char.lower()]][0] = 10000.0

def inputFromMic():
    global FROMMIC
    if FROMMIC:
        FROMMIC = False
        sourceInfo.set('Sound comes from keyboard')
    else:
        FROMMIC = True
        sourceInfo.set('Sound comes from Mic')

def robotSelection():
    global ROBOTSTATUS
    ROBOTSTATUS = int(robotStatus.get())

def ringmoduleSelection():
    global RINGMODULESTATUS
    RINGMODULESTATUS = int(ringmoduleStatus.get())

def schroederSelection():
    global SCHROEDERSTATUS
    SCHROEDERSTATUS = int(schroederStatus.get())

def moorerSelection():
    global MOORERSTATUS
    MOORERSTATUS = int(moorerStatus.get())

def reverbConvolutionSelection():
    global REVERBCONVOLUTIONSTATUS
    REVERBCONVOLUTIONSTATUS = int(reverbConvolutionStatus.get())

def tremoloSelection():
    global TREMOLOSTATUS
    TREMOLOSTATUS = int(tremoloStatus.get())

def tremolo2Selection():
    global TREMOLO2STATUS
    TREMOLO2STATUS = int(tremolo2Status.get())

def wahwahSelection():
    global WAHWAHSTATUS
    WAHWAHSTATUS = int(wahwahStatus.get())

def chorusSelection():
    global CHORUSSTATUS
    CHORUSSTATUS = int(chorusmoduleStatus.get())

def flangerSelection():
    global FLANGERSTATUS
    FLANGERSTATUS = int(flangermoduleStatus.get())

# UI elements
root = Tk.Tk()
root.bind("<Key>", keyPressed)

# Frames
sourceFrame = Tk.Frame(root, bd=10)
sourceFrame.pack(side = Tk.BOTTOM)
overdriveFrame = Tk.Frame(root, bd=10)
overdriveFrame.pack(side = Tk.LEFT)
shelvingFrame = Tk.Frame(root, bd=10)
shelvingFrame.pack(side = Tk.LEFT)
robotizationFrame = Tk.Frame(root, bd=10)
robotizationFrame.pack(side = Tk.LEFT)
chorusFrame = Tk.Frame(root, bd=10)
chorusFrame.pack(side = Tk.LEFT)
flangerFrame = Tk.Frame(root, bd=10)
flangerFrame.pack(side = Tk.LEFT)
ringModulationFrame = Tk.Frame(root, bd=10)
ringModulationFrame.pack(side = Tk.LEFT)
schroederFrame = Tk.Frame(root, bd=10)
schroederFrame.pack(side = Tk.LEFT)
moorerFrame = Tk.Frame(root, bd=10)
moorerFrame.pack(side = Tk.LEFT)
reverbConvolutionFrame = Tk.Frame(root, bd=10)
reverbConvolutionFrame.pack(side = Tk.LEFT)
tremoloFrame = Tk.Frame(root, bd=10)
tremoloFrame.pack(side = Tk.LEFT)
tremolo2Frame = Tk.Frame(root, bd=10)
tremolo2Frame.pack(side = Tk.LEFT)
wahwahFrame = Tk.Frame(root, bd=10)
wahwahFrame.pack(side = Tk.LEFT)


# overdrive UI
sourceInfo = Tk.StringVar()
sourceInfo.set('Sound comes from keyboard')
OVERDRIVEINFO = Tk.Label(overdriveFrame, text='Overdrive Type', font='Helvetica 12 bold')
OVERDRIVEINFO.pack(side = Tk.TOP)
distortionType = Tk.Listbox(overdriveFrame, width=21)
distortionType.insert(Tk.END, 'None')
distortionType.insert(Tk.END, 'HardClipping')
distortionType.insert(Tk.END, 'SoftClipping')
distortionType.insert(Tk.END, 'SoftClippingExponential')
distortionType.insert(Tk.END, 'HalfWaveRectifier')
distortionType.insert(Tk.END, 'FullWaveRectifier')
distortionType.select_set(first=0)
distortionType.pack(side = Tk.TOP)
overdriveGain = Tk.DoubleVar()
overdriveGain.set(1)
OVERDRIVE_TEXT = Tk.Label(overdriveFrame, text = "Gain Interval", font='Helvetica')
OVERDRIVE_TEXT.pack()
OVERDRIVEGAIN = Tk.Scale(overdriveFrame, variable = overdriveGain, orient = Tk.HORIZONTAL, from_ = 0, to = 10, resolution = output_gain_interval)
OVERDRIVEGAIN.pack()

# source UI
SOURCEINFO = Tk.Label(sourceFrame, textvariable = sourceInfo, font='Helvetica 12')
SOURCEINFO.pack(side = Tk.TOP)
MIC = Tk.Button(sourceFrame, text = 'Source', command = inputFromMic, font='Helvetica 10')
MIC.pack(side = Tk.TOP)

# robotization UI
ROBOTINFO = Tk.Label(robotizationFrame, text='Robotization', font='Helvetica 12 bold')
ROBOTINFO.pack(side = Tk.TOP)
robotStatus = Tk.IntVar()
ROBOTOFF = Tk.Radiobutton(robotizationFrame, text='Off', variable=robotStatus, value=0, command=robotSelection)
ROBOTOFF.pack(side = Tk.TOP)
ROBOTON = Tk.Radiobutton(robotizationFrame, text='On', variable=robotStatus, value=1, command=robotSelection)
ROBOTON.pack(side = Tk.TOP)
robotGain = Tk.DoubleVar()
robotGain.set(1)
ROBOT_TEXT = Tk.Label(robotizationFrame, text = "Gain Interval", font='Helvetica')
ROBOT_TEXT.pack()
ROBOTGAIN = Tk.Scale(robotizationFrame, variable = robotGain, orient = Tk.HORIZONTAL, from_ = 0, to = 10, resolution = output_gain_interval)
ROBOTGAIN.pack()

# chorus UI
CHORUSINFO = Tk.Label(chorusFrame, text='Chorus', font='Helvetica 12 bold')
CHORUSINFO.pack(side = Tk.TOP)
chorusmoduleStatus = Tk.IntVar()
CHORUSOFF = Tk.Radiobutton(chorusFrame, text='Off', variable=chorusmoduleStatus, value=0, command=chorusSelection)
CHORUSOFF.pack(side = Tk.TOP)
CHORUSON = Tk.Radiobutton(chorusFrame, text='On', variable=chorusmoduleStatus, value=1, command=chorusSelection)
CHORUSON.pack(side = Tk.TOP)

# flanger UI
FLANGERINFO = Tk.Label(flangerFrame, text='Flanger', font='Helvetica 12 bold')
FLANGERINFO.pack(side = Tk.TOP)
flangermoduleStatus = Tk.IntVar()
FLANGEROFF = Tk.Radiobutton(flangerFrame, text='Off', variable=flangermoduleStatus, value=0, command=flangerSelection)
FLANGEROFF.pack(side = Tk.TOP)
FLANGERON = Tk.Radiobutton(flangerFrame, text='On', variable=flangermoduleStatus, value=1, command=flangerSelection)
FLANGERON.pack(side = Tk.TOP)

# ringModulation UI
RINGMODULATIONINFO = Tk.Label(ringModulationFrame, text='Ring Modulation', font='Helvetica 12 bold')
RINGMODULATIONINFO.pack(side = Tk.TOP)
ringmoduleStatus = Tk.IntVar()
RINGMODULATIONOFF = Tk.Radiobutton(ringModulationFrame, text='Off', variable=ringmoduleStatus, value=0, command=ringmoduleSelection)
RINGMODULATIONOFF.pack(side = Tk.TOP)
RINGMODULATIONON = Tk.Radiobutton(ringModulationFrame, text='On', variable=ringmoduleStatus, value=1, command=ringmoduleSelection)
RINGMODULATIONON.pack(side = Tk.TOP)
ringmoduleGain = Tk.DoubleVar()
ringmoduleGain.set(1)
RINGMODULATION_TEXT = Tk.Label(ringModulationFrame, text = "Gain Interval", font='Helvetica')
RINGMODULATION_TEXT.pack()
RINGMODULATIONGAIN = Tk.Scale(ringModulationFrame, variable = ringmoduleGain, orient = Tk.HORIZONTAL, from_ = 0, to = 10, resolution = output_gain_interval)
RINGMODULATIONGAIN.pack()

# schroeder UI
SCHROWDERINFO = Tk.Label(schroederFrame, text='Reverb Schroeder', font='Helvetica 12 bold')
SCHROWDERINFO.pack(side = Tk.TOP)
schroederStatus = Tk.IntVar()
SCHROWDEROFF = Tk.Radiobutton(schroederFrame, text='Off', variable=schroederStatus, value=0, command=schroederSelection)
SCHROWDEROFF.pack(side = Tk.TOP)
SCHROWDERON = Tk.Radiobutton(schroederFrame, text='On', variable=schroederStatus, value=1, command=schroederSelection)
SCHROWDERON.pack(side = Tk.TOP)
schroederGain = Tk.DoubleVar()
schroederGain.set(1)
SCHROWDER_TEXT = Tk.Label(schroederFrame, text = "Gain Interval", font='Helvetica')
SCHROWDER_TEXT.pack()
SCHROWDERGAIN = Tk.Scale(schroederFrame, variable = schroederGain, orient = Tk.HORIZONTAL, from_ = 0, to = 10, resolution = output_gain_interval)
SCHROWDERGAIN.pack()

# moorer UI
MOORERINFO = Tk.Label(moorerFrame, text='Reverb Moorer', font='Helvetica 12 bold')
MOORERINFO.pack(side = Tk.TOP)
moorerStatus = Tk.IntVar()
MOOREROFF = Tk.Radiobutton(moorerFrame, text='Off', variable=moorerStatus, value=0, command=moorerSelection)
MOOREROFF.pack(side = Tk.TOP)
MOORERON = Tk.Radiobutton(moorerFrame, text='On', variable=moorerStatus, value=1, command=moorerSelection)
MOORERON.pack(side = Tk.TOP)
moorerGain = Tk.DoubleVar()
moorerGain.set(1)
MOORERGAIN_TEXT = Tk.Label(moorerFrame, text = "Gain Interval", font='Helvetica')
MOORERGAIN_TEXT.pack()
MOORERGAIN = Tk.Scale(moorerFrame, variable = moorerGain, orient = Tk.HORIZONTAL, from_ = 0, to = 10, resolution = output_gain_interval)
MOORERGAIN.pack()

# reverbConvolution UI
REVERBCONVOLUTIONINFO = Tk.Label(reverbConvolutionFrame, text='Reverb Convolution', font='Helvetica 12 bold')
REVERBCONVOLUTIONINFO.pack(side = Tk.TOP)
reverbConvolutionStatus = Tk.IntVar()
REVERBCONVOLUTIONOFF = Tk.Radiobutton(reverbConvolutionFrame, text='Off', variable=reverbConvolutionStatus, value=0, command=reverbConvolutionSelection)
REVERBCONVOLUTIONOFF.pack(side = Tk.TOP)
REVERBCONVOLUTIONON = Tk.Radiobutton(reverbConvolutionFrame, text='On', variable=reverbConvolutionStatus, value=1, command=reverbConvolutionSelection)
REVERBCONVOLUTIONON.pack(side = Tk.TOP)
reverbConvolutionGain = Tk.DoubleVar()
reverbConvolutionGain.set(1)
REVERBCONVOLUTIONGAIN_TEXT = Tk.Label(reverbConvolutionFrame, text = "Gain Interval", font='Helvetica')
REVERBCONVOLUTIONGAIN_TEXT.pack()
REVERBCONVOLUTIONGAIN = Tk.Scale(reverbConvolutionFrame, variable = reverbConvolutionGain, orient = Tk.HORIZONTAL, from_ = 0, to = 10, resolution = output_gain_interval)
REVERBCONVOLUTIONGAIN.pack()

# shelving UI
SHELVINGINFO = Tk.Label(shelvingFrame, text='Shelving', font='Helvetica 12 bold')
SHELVINGINFO.pack(side = Tk.TOP)
shelvingType = Tk.Listbox(shelvingFrame, width=15)
shelvingType.insert(Tk.END, 'None')
shelvingType.insert(Tk.END, 'Base Shelving')
shelvingType.insert(Tk.END, 'Treble Shelving')
shelvingType.select_set(first=0)
shelvingType.pack(side = Tk.TOP)
shelvingGain = Tk.DoubleVar()
shelvingGain.set(1)
SHELVINGGAIN_TEXT = Tk.Label(shelvingFrame, text = "Gain Interval", font='Helvetica')
SHELVINGGAIN_TEXT.pack()
SHELVINGGAIN = Tk.Scale(shelvingFrame, variable = shelvingGain, orient = Tk.HORIZONTAL, from_ = 0, to = 10, resolution = output_gain_interval)
SHELVINGGAIN.pack()

# tremolo UI
# TREMOLOINFO = Tk.Label(tremoloFrame, text='Tremolo', font='Helvetica 12 bold')
# TREMOLOINFO.pack(side = Tk.TOP)
# tremoloStatus = Tk.IntVar()
# TREMOLOOFF = Tk.Radiobutton(tremoloFrame, text='Off', variable=tremoloStatus, value=0, command=tremoloSelection)
# TREMOLOOFF.pack(side = Tk.TOP)
# TREMOLOON = Tk.Radiobutton(tremoloFrame, text='On', variable=tremoloStatus, value=1, command=tremoloSelection)
# TREMOLOON.pack(side = Tk.TOP)
# tremoloGain = Tk.DoubleVar()
# tremoloGain.set(1)
# TREMOLOGAIN_TEXT = Tk.Label(tremoloFrame, text = "Gain Interval", font='Helvetica')
# TREMOLOGAIN_TEXT.pack()
# TREMOLOGAIN = Tk.Scale(tremoloFrame, variable = tremoloGain, orient = Tk.HORIZONTAL, from_ = 0, to = 10, resolution = output_gain_interval)
# TREMOLOGAIN.pack()

# tremolo2 UI
TREMOLO2INFO = Tk.Label(tremolo2Frame, text='Tremolo2', font='Helvetica 12 bold')
TREMOLO2INFO.pack(side = Tk.TOP)
tremolo2Status = Tk.IntVar()
TREMOLO2OFF = Tk.Radiobutton(tremolo2Frame, text='Off', variable=tremolo2Status, value=0, command=tremolo2Selection)
TREMOLO2OFF.pack(side = Tk.TOP)
TREMOLO2ON = Tk.Radiobutton(tremolo2Frame, text='On', variable=tremolo2Status, value=1, command=tremolo2Selection)
TREMOLO2ON.pack(side = Tk.TOP)
tremolo2Gain = Tk.DoubleVar()
tremolo2Gain.set(1)
TREMOLO2GAIN_TEXT = Tk.Label(tremolo2Frame, text = "Gain Interval", font='Helvetica')
TREMOLO2GAIN_TEXT.pack()
TREMOLO2GAIN = Tk.Scale(tremolo2Frame, variable = tremolo2Gain, orient = Tk.HORIZONTAL, from_ = 0, to = 10, resolution = output_gain_interval)
TREMOLO2GAIN.pack()

# Wah Wah UI
WAHWAHINFO = Tk.Label(wahwahFrame, text='Wah Wah', font='Helvetica 12 bold')
WAHWAHINFO.pack(side = Tk.TOP)
wahwahStatus = Tk.IntVar()
WAHWAHOFF = Tk.Radiobutton(wahwahFrame, text='Off', variable=wahwahStatus, value=0, command=wahwahSelection)
WAHWAHOFF.pack(side = Tk.TOP)
WAHWAHON = Tk.Radiobutton(wahwahFrame, text='On', variable=wahwahStatus, value=1, command=wahwahSelection)
WAHWAHON.pack(side = Tk.TOP)
wahwahGain = Tk.DoubleVar()
wahwahGain.set(1)
WAHWAHGAIN_TEXT = Tk.Label(wahwahFrame, text = "Gain Interval", font='Helvetica')
WAHWAHGAIN_TEXT.pack()
WAHWAHGAIN = Tk.Scale(wahwahFrame, variable = wahwahGain, orient = Tk.HORIZONTAL, from_ = 0, to = 10, resolution = output_gain_interval)
WAHWAHGAIN.pack()

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
    if distortionType.curselection() and distortionType.curselection()[0]:
        y = overdrive(y, distortionType.curselection()[0], float(overdriveGain.get()))

    # robotization
    if ROBOTSTATUS:
        y = robotization(y, triangle_window, float(robotGain.get()))

    # ring modulation
    if RINGMODULESTATUS:
        y, ring_mod_index = ring_mod(y, ring_mod_index, RATE, float(ringmoduleGain.get()))

    # for reverb schroeder
    if SCHROEDERSTATUS:
        [y, b, a], states_list_sch = schroeder(y, n_sch, g_sch, d_sch, k_sch, states_list_sch, float(schroederGain.get()))

    # reverb moorer
    if MOORERSTATUS:
        [y, b, a], states_list_moor = moorer(y, cg_moor, cg1_moor, cd_moor, ag_moor, ad_moor, k_moor, states_list_moor, float(moorerGain.get()))

    # reverb convoluton
    if REVERBCONVOLUTIONSTATUS:
        y, keep_rc = reverb_convolution(y, imp_rc, keep_rc, BLOCKLEN, float(reverbConvolutionGain.get()))

    # shelving: Base_Shelf or Treble_Shelf
    if shelvingType.curselection() and shelvingType.curselection()[0]:
        click = int(shelvingType.curselection()[0])
        if click == 1:
            y, states_base_shel = shelving(b_base_shel, a_base_shel, y, states_base_shel, float(shelvingGain.get()))
        elif click == 2:
            y, states_treb_shel = shelving(b_treb_shel, a_treb_shel, y, states_treb_shel, float(shelvingGain.get()))
        else:
            pass
    
    # tremolo
    # if TREMOLOSTATUS:
    #     y = tremolo(y, n)
    #     n += 1

    # tremolo2
    if TREMOLO2STATUS:
        y, trem = tremolo2(y, trem, float(tremolo2Gain.get()))

    # wah_wah
    if WAHWAHSTATUS:
        y, Fc_wah_wah, wah_wah_pair = wah_wah(y, Fc_wah_wah, RATE, wah_wah_pair, float(wahwahGain.get()))
    
    if CHORUSSTATUS:
        y, kr_ch, kw_ch, buffer_chorus = chorus(y, kr_ch, kw_ch, buffer_chorus, n)
        n += 1

    if FLANGERSTATUS:
        y, kr_fl, kw_fl, buffer_flanger = flanger(y, kr_fl, kw_fl, buffer_flanger, n)
        n += 1


    binary_data = struct.pack('h' * BLOCKLEN * CHANNELS, *y);    # Convert to binary binary data
    stream.write(binary_data, BLOCKLEN * CHANNELS)               # Write binary binary data to audio output

print('* Done.')

# Close audio stream
stream.stop_stream()
stream.close()
p.terminate()
