# picosdk_python_WSL_control_example
This is a jupyter example for controlling Picoscope to collect specific waveform and data. Specially developed for a positronium experiment in TDLI (Shanghai Jiao Tong University) by Beining Rao.

## First step
 At beginning, you should download the Picosdk package for python through the official Github link developed by Pico.
 
 The link:[Click here!](https://github.com/picotech/picosdk-python-wrappers/tree/master) :)

 Save this picosdk.ipynb in the picosdk-python-wrapper directory.

 The official github also offers some examples, but it seems not be suitable for WSL( especially Ubuntu22).

 ## Second step
 !!! This exmaple(picosdk.ipynb) is particulrally for WSL (Ubuntu). You should firstly share and attach picoscope to WSL system, and then run it.

 ## Notes
 This example shows how to give Channel A and B an "AND" logic as a trigger with the use of rapid capture, following with Channel C and D valid waveform selection with 1 microsecond time window in a temporary data buffer zone and then save them.
 **Note that in this case, an interpolation method was used to falsely increase the maximum resolution (4ns) of the four-channel simultaneous-enabled pico5444D.**

 Welcome to star my example!!!

## picoDAQAssistant lib (Meng)
Two examples are provided:  
`pico5000RapidBlock.py`: basically copy from Beining's `picosdk.ipynb` while using the library to save waveform to CERN ROOT file.  
The I/O structure is changed to numpy array instead of list to speed up data processing.

`pico3000aBlock.py`: a block example using ps3000 series. A shorter example for easier understanding of how to use this lib.

Detailed instruction to be finished yet..