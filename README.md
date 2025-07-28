# picosdk_python_WSL_control_example
This is an jupyter example for controlling Picoscope to collect specific waveform and data. Specially developed for a positronium experiment in TDLI (Shanghai Jiao Tong University) by Beining Rao.

## First step
 At beginning, you should download the Picosdk package for python through the official Github link developed by Pico.
 
 The link:[Click here!](https://github.com/picotech/picosdk-python-wrappers/tree/master) :)

 Save this picosdk.ipynb in the picosdk-python-wrapper directory.

 ## Second step
 !!! This exmaple(picosdk.ipynb) is particulrally for WSL (Ubuntu). You should firstly share and attach picoscope to WSL system then run it.

 ## Notes
 This example shows how to give Channel A and B an "AND" logic as a trigger with use rapid capture, following with Channel C and D valid waveform selection with 1 microsecond time window in a temporary data buffer zone and then save them.
 **Note that in this case, an interpolation method was used to falsely increase the maximum resolution (4ns) of the four-channel simultaneous-enabled pico5444D.**

 Welcome to star my example!!!
