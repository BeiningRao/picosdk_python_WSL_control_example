# picosdk python control class guildance and example
This is a jupyter example for controlling Picoscope to collect specific waveform and data. Specially developed for a positronium experiment in TDLI (Shanghai Jiao Tong University) by Beining Rao. Improved by University of Tokyo Meng Lv and TDLI Junkai Ng.

## preparation: Connect Picoscope to WSL(eg.Ubuntu) [Thanks to Junkai to complete this guildance!]
### Install picoScope SDK and picosdk-python-wrappers in WSL
PicoSDK is a toolkit of C drivers that allow you to control your PicoScope using any programming language. With PicoSDK you can create custom programs to collect and analyze data from the scope. picosdk-python-wrappers are direct wrappers for each driver function in the PicoSDK, the calling to the C functions are done with ctypes.

Please follow this instructions: picosdk-python-wrappers/ps5000aExamples/ps5000aStreamingExample.py at master · picotech/picosdk-python-wrappers · GitHub

Note: There is currently a continuos develpment of pyPicoSDK, as on 24 Oct 2025, it do now support 5000 series. To compare, picosdk-python-wrappers are direct wrappers for each driver function in the PicoSDK, while pyPicoSDK is an updated wrapper that bundles all of the direct wrappers together into one group. It also adds built-in helper functions that reduce the complexity of some of the functions of PicoScopes (more pythonic). See 
https://www.picotech.com/library/knowledge-bases/oscilloscopes/pypicosdk-get-started
and
https://github.com/picotech/pyPicoSDK

for more information. Please download the ps5000a branch for using pyPicoSDK.

references:

https://blog.csdn.net/gitblog_01028/article/details/141293910

### Setup usb binding to wsl
follow the instructions from microsoft to install the USBIPD tools: Connect USB devices | Microsoft Learn (you can simply run `winget install --interactive --exact dorssel.usbipd-win` from windows terminal)


### Attach USB to WSL
Before attaching your USB device, ensure that a WSL command line is open. This will keep the WSL 2 lightweight VM active.

You will also need to run PowerShell as administrator.

#### 1.) `usbipd list`

you will see the bus, state (shared / not shared), like this:

​​​​<img width="1112" height="222" alt="image" src="https://github.com/user-attachments/assets/541eb8a0-0a44-45ca-8169-43d724feb00b" />




#### 2.） Connect and share the USB device `usbipd bind --busid <busid>`

note: share = bind in usbipd lingo

you should see something like this:

<img width="1111" height="217" alt="image" src="https://github.com/user-attachments/assets/d6d7918d-0527-48be-9d4d-53184e2f183e" />




#### 3.) Attach the USB device to WSL. `usbipd attach --wsl --busid  <busid>'

you will heard windows USB connected sound, and see the following output:

<img width="1197" height="150" alt="image" src="https://github.com/user-attachments/assets/3198e7f0-fc8d-45f8-a274-f0877b2f575c" />


notes:

a) you do not need administrator privellege after this step.

b) you need to attach the device every time you restart wsl (it seems like the bind step is not required every time)



#### 4.) In WSL, verify the connected devices `lsusb`

you will see the following:

<img width="1143" height="96" alt="image" src="https://github.com/user-attachments/assets/ccd6cfd0-d794-4ab0-b85b-ced756a5d698" />


You will also see the following on the windows terminal:

<img width="1101" height="210" alt="image" src="https://github.com/user-attachments/assets/f6aaca6b-0692-4086-9552-7e1ece633ec1" />




#### 5.) After use, run `usbipd detach --busid <busid>` and `usbipd unbind --busid <busid>`.

Reference: Connect USB devices | Microsoft Learn
 
 ## Notes
 This example shows how to give Channel A and B an "AND" logic as a trigger with the use of rapid capture, following with Channel C and D valid waveform selection with 1 microsecond time window in a temporary data buffer zone and then save them.
 **Note that in this case, an interpolation method was used to falsely increase the maximum resolution (4ns) of the four-channel simultaneous-enabled pico5444D.**



## picoDAQAssistant lib (Meng)
Two examples are provided:  
`pico5000RapidBlock.py`: basically copy from Beining's `picosdk.ipynb` while using the library to save waveform to CERN ROOT file.  
The I/O structure is changed to numpy array instead of list to speed up data processing.

`pico3000aBlock.py`: a block example using ps3000 series. A shorter example for easier understanding of how to use this lib.

Detailed instruction to be finished yet..

## single channel signal collection code for Ps5000a(Beining)
Added at 12/19/2025.A jupyter temple based on picoDAQAssistant. Notes that the time resolution for one channel is 1ns, but for two channels, it should be 2ns.
