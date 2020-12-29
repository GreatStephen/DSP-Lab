import math
import numpy as np

HardClipping = 1
SoftClipping = 2
SoftClippingExponential = 3
HalfWaveRectifier = 4
FullWaveRectifier = 5

def overdrive(y, distortionType, gain=1, MAXVALUE=2**15-1):
    if distortionType==HardClipping:
        threshold = 1000
        def HC(v):
            if v>threshold: return threshold
            elif v<-threshold: return -threshold
            else: return v
        y = list(map(HC, y))
    elif distortionType==SoftClipping:
        threshold1, threshold2 = 1/3, 2/3
        scale = 1000
        def HC(v):
            v = v/scale
            # print(v)
            if v>threshold2: return 1*scale
            elif v>threshold1: return int((3-(2-3*v)*(2-3*v))/3*scale)
            elif v<-threshold2: return -1*scale
            elif v<-threshold1: return int(-(3-(2+3*v)*(2+3*v))/3*scale)
            else: return int(2*v*scale)
        y = list(map(HC, y))
    elif distortionType==SoftClippingExponential:
        scale = 1000
        def HC(v):
            v = v/ scale
            # print(v)
            if v>0:
                return int((1-1/math.exp(v))*scale)
            else:
                return int((-1+math.exp(v))*scale)
        y = list(map(HC, y))
    elif distortionType==HalfWaveRectifier:
        def HC(v):
            if v>0:
                return v
            else:
                return 0
        y = list(map(HC, y))
    elif distortionType==FullWaveRectifier:
        y = list(map(lambda v:abs(v), y))        
    
    y = np.array(y)*gain
    y = np.clip(y, -MAXVALUE, MAXVALUE) # clipping
    y = y.astype(int) # convert to integer
    return y