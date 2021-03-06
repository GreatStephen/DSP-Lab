# Guitar Simulator - An Application of Real-Time Signal Processing

## Description

This is a simple guitar simulator that applies multiple filters and further generates the synthesis wave file in real-time. We first built multiple filters, including delaying (chorus, flanger, vibrato), modulation (ring, tremolo), non-linear processing (distortion), time-varying (wah-wah), and some special effects (reverberation). All these filter functions can be found in `filters`. Then, we constructed a GUI interface as the graph below to further synthesize and control each wave file. Note that there are two options for the source sounds, the piano click sounds, and the microphone input.

<p align = 'center'>
<img src = 'https://raw.githubusercontent.com/GreatStephen/DSP-Lab/main/docs/GUI_interface.PNG'>
</p>

For more information about the therories of these filters, please click the [report paper](https://github.com/GreatStephen/DSP-Lab/blob/main/docs/DSP_proj_report.pdf/).

## Local Deployment

Clone the repository:

    git clone https://github.com/GreatStephen/DSP-Lab.git

Install the dependecies from `requirements.txt`:

    pip install -r requirements.txt

Run the program:

    python effect.py

If you have questions, feel free to leave a message [here](https://github.com/GreatStephen/DSP-Lab/issues).