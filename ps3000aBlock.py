import ctypes
from picosdk.ps3000a import ps3000a as ps
import numpy as np
import matplotlib.pyplot as plt
from picosdk.functions import mV2adc, adc2mV, assert_pico_ok
import uproot
import time
import picoDAQAssistant
import importlib

# Create chandle and status ready for use
status = {}
chandle = ctypes.c_int16()

# Opens the device/s
status["openunit"] = ps.ps3000aOpenUnit(ctypes.byref(chandle), None)

try:
    assert_pico_ok(status["openunit"])
except:

    # powerstate becomes the status number of openunit
    powerstate = status["openunit"]

    # If powerstate is the same as 282 then it will run this if statement
    if powerstate == 282:
        # Changes the power input to "PICO_POWER_SUPPLY_NOT_CONNECTED"
        status["ChangePowerSource"] = ps.ps3000aChangePowerSource(chandle, 282)
        # If the powerstate is the same as 286 then it will run this if statement
    elif powerstate == 286:
        # Changes the power input to "PICO_USB3_0_DEVICE_NON_USB3_0_PORT"
        status["ChangePowerSource"] = ps.ps3000aChangePowerSource(chandle, 286)
    else:
        raise

    assert_pico_ok(status["ChangePowerSource"])

# Set up channel A
chA_channel_No = ps.PS3000A_CHANNEL["PS3000A_CHANNEL_A"]
chA_range = ps.PS3000A_RANGE["PS3000A_2V"]
chA_coupling = ps.PS3000A_COUPLING["PS3000A_DC"]
chA_enabled = 1  # off: 0, on: 1
chA_analog_offset = 0 # in V
status["setChA"] = ps.ps3000aSetChannel(chandle, chA_channel_No, chA_enabled, chA_coupling, chA_range, chA_analog_offset)
assert_pico_ok(status["setChA"])

# Set up channel B
chB_channel_No = ps.PS3000A_CHANNEL["PS3000A_CHANNEL_B"]
chB_range = ps.PS3000A_RANGE["PS3000A_500MV"]
chB_coupling = ps.PS3000A_COUPLING["PS3000A_DC"]
chB_enabled = 0  # off: 0, on: 1
chB_analog_offset = 0 # in V
status["setChB"] = ps.ps3000aSetChannel(chandle, chB_channel_No, chB_enabled, chB_coupling, chB_range, chB_analog_offset)
assert_pico_ok(status["setChB"])

# Set up channel C
chC_channel_No = ps.PS3000A_CHANNEL["PS3000A_CHANNEL_C"]
chC_range = ps.PS3000A_RANGE["PS3000A_500MV"]
chC_coupling = ps.PS3000A_COUPLING["PS3000A_DC"]
chC_enabled = 0  # off: 0, on: 1
chC_analog_offset = 0 # in V
status["setChC"] = ps.ps3000aSetChannel(chandle, chC_channel_No, chC_enabled, chC_coupling, chC_range, chC_analog_offset)
assert_pico_ok(status["setChC"])

# Set up channel D
chD_channel_No = ps.PS3000A_CHANNEL["PS3000A_CHANNEL_D"]
chD_range = ps.PS3000A_RANGE["PS3000A_500MV"]
chD_coupling = ps.PS3000A_COUPLING["PS3000A_DC"]
chD_enabled = 0  # off: 0, on: 1
chD_analog_offset = 0 # in V
status["setChD"] = ps.ps3000aSetChannel(chandle, chD_channel_No, chD_enabled, chD_coupling, chD_range, chD_analog_offset)
assert_pico_ok(status["setChD"])

# Sets up single trigger
trigger_enable = 1  # 0 to disable, any other number to enable
trigger_channel = chA_channel_No

trigger_level_mV = 80
# Finds the max ADC count
# Handle = chandle
# Value = ctype.byref(maxADC)
maxADC = ctypes.c_int16()
status["maximumValue"] = ps.ps3000aMaximumValue(chandle, ctypes.byref(maxADC))
assert_pico_ok(status["maximumValue"])
trigger_level_ADC = mV2adc(trigger_level_mV, chA_range, maxADC)

trigger_type = ps.PS3000A_THRESHOLD_DIRECTION["PS3000A_RISING"]
trigger_delay = 0   # Number of sample
auto_trigger = 1000 # autotrigger wait time (in ms)
status["trigger"] = ps.ps3000aSetSimpleTrigger(chandle, trigger_enable, chA_channel_No, trigger_level_ADC, trigger_type, trigger_delay, auto_trigger)
assert_pico_ok(status["trigger"])

# Setting the number of sample to be collected
preTriggerSamples = 50
postTriggerSamples = 100
maxsamples = preTriggerSamples + postTriggerSamples

# Gets timebase innfomation
# WARNING: When using this example it may not be possible to access all Timebases as all channels are enabled by default when opening the scope.  
# To access these Timebases, set any unused analogue channels to off.
# Handle = chandle
# Timebase = 2 = timebase
# Nosample = maxsamples
# TimeIntervalNanoseconds = ctypes.byref(timeIntervalns)
# MaxSamples = ctypes.byref(returnedMaxSamples)
# Segement index = 0
# timebase = 252  # Sampling interval = (n-2) * 8ns
timebase = 0
timeIntervalns = ctypes.c_float()
returnedMaxSamples = ctypes.c_int16()
status["GetTimebase"] = ps.ps3000aGetTimebase2(chandle, timebase, maxsamples, ctypes.byref(timeIntervalns), 1, ctypes.byref(returnedMaxSamples), 0)
assert_pico_ok(status["GetTimebase"])

# Creates a overlow location for data
overflow = ctypes.c_int16()
# Creates converted types maxsamples
cmaxSamples = ctypes.c_int32(maxsamples)

# Create buffers ready for assigning pointers for data collection
bufferAMax = np.zeros(shape=maxsamples, dtype=np.int16)
bufferBMax = np.zeros(shape=maxsamples, dtype=np.int16)
bufferCMax = np.zeros(shape=maxsamples, dtype=np.int16)
bufferDMax = np.zeros(shape=maxsamples, dtype=np.int16)
bufferAMin = np.zeros(shape=maxsamples, dtype=np.int16)
bufferBMin = np.zeros(shape=maxsamples, dtype=np.int16)
bufferCMin = np.zeros(shape=maxsamples, dtype=np.int16)
bufferDMin = np.zeros(shape=maxsamples, dtype=np.int16)

# Setting the data buffer location for data collection from channel A
status["SetDataBuffers"] = ps.ps3000aSetDataBuffers(chandle, chA_channel_No, bufferAMax.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), bufferAMin.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), maxsamples, 0, 0)
status["SetDataBuffers"] = ps.ps3000aSetDataBuffers(chandle, chB_channel_No, bufferBMax.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), bufferBMin.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), maxsamples, 0, 0)
status["SetDataBuffers"] = ps.ps3000aSetDataBuffers(chandle, chC_channel_No, bufferCMax.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), bufferCMin.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), maxsamples, 0, 0)
status["SetDataBuffers"] = ps.ps3000aSetDataBuffers(chandle, chD_channel_No, bufferDMax.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), bufferDMin.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), maxsamples, 0, 0)
assert_pico_ok(status["SetDataBuffers"])

myROOT = picoDAQAssistant.RootManager(filename="test.root", runN=1, chunk_size=2000, sample_num=maxsamples)
myROOT.start_thread()


# Creates a overlow location for data
overflow = (ctypes.c_int16 * 10)()
# Creates converted types maxsamples
cmaxSamples = ctypes.c_int32(maxsamples)

# Creates the time data
t = np.linspace(0, (cmaxSamples.value - 1) * timeIntervalns.value, cmaxSamples.value)

for _ in range(100):
    # Starts the block capture
    status["runblock"] = ps.ps3000aRunBlock(chandle, preTriggerSamples, postTriggerSamples, timebase, 1, None, 0, None, None)
    assert_pico_ok(status["runblock"])


    # Checks data collection to finish the capture
    ready = ctypes.c_int16(0)
    check = ctypes.c_int16(0)
    while ready.value == check.value:
        status["isReady"] = ps.ps3000aIsReady(chandle, ctypes.byref(ready))

    status["GetValues"] = ps.ps3000aGetValues(chandle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, ctypes.byref(overflow))
    assert_pico_ok(status["GetValues"])

    # Converts ADC from channel A to mV
    adc2mVChAMax =  picoDAQAssistant.fastAdc2mV(bufferAMax, chA_range, maxADC)
    adc2mVChBMax =  picoDAQAssistant.fastAdc2mV(bufferBMax, chB_range, maxADC)
    adc2mVChCMax =  picoDAQAssistant.fastAdc2mV(bufferCMax, chC_range, maxADC)
    adc2mVChDMax =  picoDAQAssistant.fastAdc2mV(bufferDMax, chD_range, maxADC)

    myROOT.fill(Time=t, ChA=adc2mVChAMax, ChB=adc2mVChBMax, ChC=adc2mVChCMax, ChD=adc2mVChDMax)

myROOT.close()

# Stops the scope
# Handle = chandle
status["stop"] = ps.ps3000aStop(chandle)
assert_pico_ok(status["stop"])

# Closes the unit
# Handle = chandle
status["close"] = ps.ps3000aCloseUnit(chandle)
assert_pico_ok(status["close"])

# Displays the staus returns
print(status)
