# Guitar Simulator - An Application of Real-Time Signal Processing

## Description

This is a simple guitar simulator that apply multiple filters and further generate the synthesis wave file. We first built multiple filters, including delaying (chorus, flanger, vibrato), modulation (ring, tremolo), non-linear processing (distortion), time varying (wah-wah) and some special effects (reverberation). All these filter function can be found in `filters`. Then, we constructed a GUI interface as the graph below to further synthesis and control each wave file. Note that there are two options for the source sounds, the piano click sounds and the microphone input.

<p align = 'center'>
<img src = 'https://github.com/samsh19/ML_project/blob/main/data/compare_images/polor_bear_japan_paint_wave_compare.png?raw=true'>
</p>

For more informatin in the therories for these filters, please click the [report paper](https://github.com/GreatStephen/DSP-Lab/docs/DSPLab_report.pdf/).

## Local Deployment

Clone the repository:

    git clone https://github.com/GreatStephen/DSP-Lab.git

Install the dependecies from `requirements.txt`:

    pip install -r requirements.txt

Run the program:

    python effect.py

If you have questions, feel free to leave a message [here](https://github.com/GreatStephen/DSP-Lab/issues).