import math

HardClipping = 1
SoftClipping = 2
SoftClippingExponential = 3
HalfWaveRectifier = 4
FullWaveRectifier = 5

def overdrive(y, distortionType):
    if distortionType==HardClipping:
        threshold = 2000
        def HC(v):
            if v>threshold: return threshold
            elif v<-threshold: return -threshold
            else: return v
        y = list(map(HC, y))
        # print(x)
    elif distortionType==SoftClipping:
        threshold1, threshold2 = 1/3, 2/3
        scale = 6000
        def HC(v):
            v = v/scale
            # print(v)
            if v>threshold2: return 1*scale
            elif v>threshold1: return int((3-(2-3*v)*(2-3*v))/3*scale)
            elif v<-threshold2: return -1*scale
            elif v<-threshold1: return int(-(3-(2+3*v)*(2+3*v))/3*scale)
            else: return int(2*v*scale)
        y = list(map(HC, y))
        # print(x)
    elif distortionType==SoftClippingExponential:
        def HC(v):
            v = v/ 3000
            # print(v)
            if v>0:
                return int((1-1/math.exp(v))*3000)
            else:
                return int((-1+math.exp(v))*3000)
        y = list(map(HC, y))
        # print(x)
    elif distortionType==HalfWaveRectifier:
        def HC(v):
            if v>0:
                return v
            else:
                return 0
        y = list(map(HC, y))
    elif distortionType==FullWaveRectifier:
        y = list(map(lambda v:abs(v), y))        
    
    return y