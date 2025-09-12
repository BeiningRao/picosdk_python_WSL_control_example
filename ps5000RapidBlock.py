# This example is created from picosdk.ipynb (rapid block sampling mode), with picoDAQAssystant.py lib to save data in ROOT form
# Created by Meng Lyu on 2025.09.12

import ctypes
import time
import numpy as np
from picosdk.ps5000a import ps5000a, Ps5000alib
import os
import datetime
base_date = datetime.datetime.now().strftime("%Y%m%d")
from ctypes import c_int16, c_int32, c_uint32,c_uint16, c_int64, c_char_p, c_void_p, POINTER, create_string_buffer
from picosdk.ps5000a import ps5000a as ps
from picosdk.constants import PICO_STATUS, PICO_INFO
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc
import matplotlib.pyplot as plt
import sys, select

import picoDAQAssistant as pda

## Setting file path and checking PS module ##

TARGET_EVENTS = 10000   # Target waveform number saved for each block
PRE_TRIGGER_SAMPLE = 25 # Sample number to be saved before trigger 
POST_TRIGGER_SAMPLE = 225 # Sample number to be saved after trigger
NUM_SAMPLES = PRE_TRIGGER_SAMPLE+POST_TRIGGER_SAMPLE       # Total sample number per waveform 
Nout = 2000             # Output sample number after interpolation

# Open the ROOT file
myROOT = pda.RootManager(filename="/home/sasuke/opstime-normal-5mv/test00.root",    # Output file
                         runN=1,                                                    # Run number 
                         chunk_size=TARGET_EVENTS,                                  # If you're using rapid block, set this value larger than waveform number of a block
                         sample_num=Nout)                                    # The sample number to be recorded in each waveform
myROOT.start_thread()   # Start background loop to receive data

## Checking the picoscope status ##
chandle = ctypes.c_int16()
status = {}

resolution =ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_8BIT"]
# Returns handle to chandle for use in future API functions
status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(chandle), None, resolution)

try:
    assert_pico_ok(status["openunit"])
except: # PicoNotOkError:

    powerStatus = status["openunit"]

    if powerStatus == 286:
        status["changePowerSource"] = ps.ps5000aChangePowerSource(chandle, powerStatus)
    elif powerStatus == 282:
        status["changePowerSource"] = ps.ps5000aChangePowerSource(chandle, powerStatus)
    else:
        raise

    assert_pico_ok(status["changePowerSource"])

## Setting trigger threshold
maxADC = ctypes.c_int16()
status["maximumValue"] = ps.ps5000aMaximumValue(chandle, ctypes.byref(maxADC))
assert_pico_ok(status["maximumValue"])

NUM_SAMPLES   = 250

THR_COUNTS_CD = mV2adc(-10,ps.PS5000A_RANGE["PS5000A_500MV"],maxADC) 

max_counts = (1 << (8 - 1)) - 1 
# vRange = 500.0  
threshold_mv = 160.0 
THR_COUNTS_A = mV2adc(160,ps.PS5000A_RANGE["PS5000A_1V"], maxADC)
THR_COUNTS_B = mV2adc(160,ps.PS5000A_RANGE["PS5000A_1V"], maxADC)

## Checking current pico resolution ##
current_res = ctypes.c_int32()
status = ps.ps5000aGetDeviceResolution(
    chandle,
    ctypes.byref(current_res)
)
print("pico current resolution：", current_res.value) 
print("PS500A_RESOLUTION",ps.PS5000A_DEVICE_RESOLUTION)

status = ps.ps5000aSetAutoTriggerMicroSeconds(chandle, ctypes.c_uint64(0))
print("status=",status)

## Four channel basic properties ##

CHANNEL_A = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
CHANNEL_B = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
CHANNEL_C = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_C"]
CHANNEL_D = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_D"]

for ch in (CHANNEL_A, CHANNEL_B):
    status = ps.ps5000aSetChannel(
        chandle,
        ch,
        ctypes.c_int16(1),                    # enabled = 1
        ps.PS5000A_COUPLING['PS5000A_DC'],    
        ps.PS5000A_RANGE['PS5000A_1V'],    # ±500 mV
        ctypes.c_float(0.0)                # analogOffset = 0.300 V 
    )
    if status != PICO_STATUS['PICO_OK']:
        raise RuntimeError(f"ps5000aSetChannel CH{ch} (A/B) not set,status = {status}")

for ch in (CHANNEL_C, CHANNEL_D):
    status = ps.ps5000aSetChannel(
        chandle,
        ch,
        ctypes.c_int16(1),                    # enabled = 1
        ps.PS5000A_COUPLING['PS5000A_DC'],    
        ps.PS5000A_RANGE['PS5000A_500MV'],    # ±500 mV
        ctypes.c_float(0.3)                   # analogOffset = 0.0 V
    )
    if status != PICO_STATUS['PICO_OK']:
        raise RuntimeError(f"ps5000aSetChannel CH{ch} (C/D) not set,status = {status}")

class PS5000A_TRIGGER_CHANNEL_PROPERTIES_V2(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("thresholdUpper", ctypes.c_int16),
        ("thresholdUpperHysteresis", ctypes.c_uint16),
        ("thresholdLower", ctypes.c_int16),
        ("thresholdLowerHysteresis", ctypes.c_uint16),
        ("channel", ctypes.c_int32),
    ]

hysteresis_counts_A = 10
hysteresis_counts_B = 10

trig_a = PS5000A_TRIGGER_CHANNEL_PROPERTIES_V2(
                            
    ctypes.c_int16(THR_COUNTS_A),
    ctypes.c_uint16(hysteresis_counts_A),   
    0,
    0,         
    CHANNEL_A                     
)

trig_b = PS5000A_TRIGGER_CHANNEL_PROPERTIES_V2(

    ctypes.c_int16(THR_COUNTS_B),
    ctypes.c_uint16(hysteresis_counts_B),
    0,
    0,
    CHANNEL_B
)

arr_props = (PS5000A_TRIGGER_CHANNEL_PROPERTIES_V2 * 2)(trig_a, trig_b)
status = ps.ps5000aSetTriggerChannelPropertiesV2(
    chandle,
    ctypes.cast(arr_props, ctypes.c_void_p),
    ctypes.c_int16(2),   
    ctypes.c_int16(0)    # auxOutputEnable = 0
)
if status != PICO_STATUS['PICO_OK']:
    raise RuntimeError(f"ps5000aSetTriggerChannelPropertiesV2 notset,status= {status}")


## Trigger logic (This example shows  A and B "AND" logic)
# Notes that If you want AND, you should put two channel in one arr_dirs, otherwise you should add two dirs to get "OR" logic
dir_a = ps.PS5000A_DIRECTION(
    ps.PS5000A_CHANNEL['PS5000A_CHANNEL_A'],
    ps.PS5000A_THRESHOLD_DIRECTION['PS5000A_RISING'],
    ps.PS5000A_THRESHOLD_MODE['PS5000A_LEVEL']
)

dir_b = ps.PS5000A_DIRECTION(
    ps.PS5000A_CHANNEL['PS5000A_CHANNEL_B'],
    ps.PS5000A_THRESHOLD_DIRECTION['PS5000A_RISING'],
    ps.PS5000A_THRESHOLD_MODE['PS5000A_LEVEL'] 
)


arr_dirs = (ps.PS5000A_DIRECTION * 2)(dir_a, dir_b)


status = ps.ps5000aSetTriggerChannelDirectionsV2(
    chandle,
    ctypes.cast(arr_dirs, ctypes.c_void_p),
    ctypes.c_uint16(2)  
)

if status != PICO_STATUS['PICO_OK']:
    raise RuntimeError(f"ps5000aSetTriggerChannelDirectionsV2 notset status = {status}")

class PS5000A_TRIGGER_CHANNEL_CONDITIONS(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("source", ctypes.c_int32),
        ("condition", ctypes.c_int32),
    ]

cond_a = PS5000A_TRIGGER_CHANNEL_CONDITIONS(
    CHANNEL_A,
    ps.PS5000A_TRIGGER_STATE['PS5000A_CONDITION_TRUE']
)
cond_b = PS5000A_TRIGGER_CHANNEL_CONDITIONS(
    CHANNEL_B,
    ps.PS5000A_TRIGGER_STATE['PS5000A_CONDITION_TRUE']
)
arr_conds = (PS5000A_TRIGGER_CHANNEL_CONDITIONS * 2)(cond_a, cond_b)
INFO_CLEAR = ps.PS5000AConditionsInfo["PS5000A_ADD"]

status = ps.ps5000aSetTriggerChannelConditionsV2(
    chandle,
    ctypes.cast(arr_conds, ctypes.c_void_p),
    ctypes.c_int16(2),
    INFO_CLEAR
)
if status != PICO_STATUS['PICO_OK']:
    raise RuntimeError(f"ps5000aSetTriggerChannelConditionsV2 failed,status = {status}")

## Setting segments fragmentation ##
max_segments = c_uint32(0)
status = ps.ps5000aGetMaxSegments(chandle, ctypes.byref(max_segments))
if status != PICO_STATUS['PICO_OK']:
    raise RuntimeError(f"ps5000aGetMaxSegments failed: {status}")

n_segments = int(TARGET_EVENTS)

max_samples_per_segment = ctypes.c_uint32()
status = ps.ps5000aMemorySegments(
    chandle,
    ctypes.c_uint32(n_segments),
    ctypes.byref(max_samples_per_segment)
)
if status != PICO_STATUS['PICO_OK']:
    raise RuntimeError(f"ps5000aMemorySegments failed: {status}")

## Setting rapid capture ##
status = ps.ps5000aSetNoOfCaptures(chandle, ctypes.c_uint32(n_segments))
if status != PICO_STATUS['PICO_OK']:
    raise RuntimeError(f"ps5000aSetNoOfCaptures failed: {status}")
print(f"✅set capture amount {n_segments}")

def status_to_msg(status):
    """Convert the status code to a message string."""
    for k, v in PICO_STATUS.items():
        if v == status:
            return k
    return f"Unknown status code {status}"

def sincx_interp(x,xp,yp):
    X=x[:,None]-xp[None,:]
    S=np.sinc(X/(xp[1]-xp[0]))
    return S.dot(yp)/S.sum(axis=1)

## Four-channel data buffer register ##
A_buf = np.zeros(shape=NUM_SAMPLES, dtype=np.int16)
B_buf = np.zeros(shape=NUM_SAMPLES, dtype=np.int16)
C_buf = np.zeros(shape=NUM_SAMPLES, dtype=np.int16)
D_buf = np.zeros(shape=NUM_SAMPLES, dtype=np.int16)

status  = ps.ps5000aSetDataBuffer(
    chandle,
    CHANNEL_A,
    A_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
    ctypes.c_int32(NUM_SAMPLES),
    ctypes.c_uint32(0),               # segmentIndex
    ps.PICO_RATIO_MODE[""]
)
status |= ps.ps5000aSetDataBuffer(chandle, CHANNEL_B, B_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                                  ctypes.c_int32(NUM_SAMPLES),
                                  ctypes.c_uint32(0),
                                  ps.PICO_RATIO_MODE[""])
status |= ps.ps5000aSetDataBuffer(chandle, CHANNEL_C, C_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                                  ctypes.c_int32(NUM_SAMPLES),
                                  ctypes.c_uint32(0),
                                  ps.PICO_RATIO_MODE[""])
status |= ps.ps5000aSetDataBuffer(chandle, CHANNEL_D, D_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                                  ctypes.c_int32(NUM_SAMPLES),
                                  ctypes.c_uint32(0),
                                  ps.PICO_RATIO_MODE[""])

if status != PICO_STATUS["PICO_OK"]:
    raise RuntimeError(f"SetDataBuffer register failed, status={status}")

print("✅ The A/B/C/D four-channel data buffer has been correctly registered.")

## Running and Saving ##
base_date = datetime.datetime.now().strftime("%Y%m%d")
batch_index = 1
status = ps.ps5000aSetAutoTriggerMicroSeconds(
    chandle,
    ctypes.c_uint64(0)  
)
print("status=",status)

# The DAQ loop cannot be always True because ROOT file needs to be closed after the loop
print("DAQ starts. Press Enter to stop...")
while True:
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        _ = sys.stdin.readline()  # read and ignore input
        print("Enter pressed, exiting DAQ")
        break

    event_count = 0
    batch_number=0

    A_buf = np.zeros(shape=(n_segments, NUM_SAMPLES), dtype=np.int16)
    B_buf = np.zeros(shape=(n_segments, NUM_SAMPLES), dtype=np.int16)
    C_buf = np.zeros(shape=(n_segments, NUM_SAMPLES), dtype=np.int16)
    D_buf = np.zeros(shape=(n_segments, NUM_SAMPLES), dtype=np.int16)

    while event_count <TARGET_EVENTS :
        batch_number += 1

        ps.ps5000aStop(chandle)
        time.sleep(1e-5)
        status = ps.ps5000aSetNoOfCaptures(chandle, ctypes.c_uint32(n_segments))
        if status != PICO_STATUS['PICO_OK']:
            raise RuntimeError(f"ps5000aSetNoOfCaptures fail: {status}")
        print(f"✅ segments number{n_segments}")
        for seg in range(n_segments):
            for ch, buf_array in [
                (CHANNEL_A, A_buf),
                (CHANNEL_B, B_buf),
                (CHANNEL_C, C_buf),
                (CHANNEL_D, D_buf)
            ]:
                status = ps.ps5000aSetDataBuffer(
                    chandle,
                    ch,
                    buf_array[seg].ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                    ctypes.c_int32(NUM_SAMPLES),
                    ctypes.c_uint32(seg),
                    ps.PICO_RATIO_MODE[""]
                )
                if status != PICO_STATUS['PICO_OK']:
                    raise RuntimeError(f"ps5000aSetDataBuffer CH{ch} {seg} not set,status = {status}")



        # ———————————— 4.2.1 RunBlock ————————————
        status = ps.ps5000aRunBlock(
            chandle,
            ctypes.c_int32(PRE_TRIGGER_SAMPLE),
            ctypes.c_int32(POST_TRIGGER_SAMPLE),
            ctypes.c_uint32(2),
            None,
            ctypes.c_uint32(0),
            None,
            None
        )
        if status != PICO_STATUS['PICO_OK']:
            raise RuntimeError(f"ps5000aRunBlock fail, status= {status}")

        ready = c_int16(0)
        timeout_ms = 1000
        start_time = time.time()
        while ready.value == 0:
            status = ps.ps5000aIsReady(chandle, ctypes.byref(ready))
            if status != PICO_STATUS['PICO_OK']:
                print(f"IsReady error: {status}")
                break
            if (time.time() - start_time) * 10 > timeout_ms:
                print("Waiting for trigger timeout")
                break
            time.sleep(0.001)
        
        captures_completed = c_uint32(0)
        status = ps.ps5000aGetNoOfCaptures(chandle, ctypes.byref(captures_completed))
        if status != PICO_STATUS['PICO_OK']:
            print(f"fail get the capture number: {status} - {status_to_msg(status)}")
        
        print(f"✓ complete {captures_completed.value}/{n_segments} capture")

        if captures_completed.value == 0:
            print("fail to get any events")
            continue
    # ———————————— 4.2.3 GetValues ————————————
        num_samples = c_uint32(NUM_SAMPLES)
        overflow = (c_uint16 * n_segments)()


        num_samples = c_uint32(NUM_SAMPLES)
        overflow = (c_uint16 * n_segments)()
        status = ps.ps5000aGetValuesBulk(
            chandle,
            ctypes.byref(num_samples),
            c_uint32(0),
            c_uint32(captures_completed.value - 1),
            c_uint32(1),
            ps.PICO_RATIO_MODE[""],
            ctypes.cast(overflow, ctypes.POINTER(c_uint16))
        )

        if status != PICO_STATUS['PICO_OK']:
            print(f"fail to get events f: {status}")
            continue
        actual_count = num_samples.value
        time_interval_s = 4 * 1e-9
        for seg in range(captures_completed.value):
            
            A_counts = A_buf[seg][:actual_count]
            B_counts = B_buf[seg][:actual_count]
            C_counts = C_buf[seg][:actual_count]
            D_counts = D_buf[seg][:actual_count]


            C8 = C_counts
            D8 = D_counts
            
            baseline_C = np.mean(C8[:20])
            baseline_D = np.mean(D8[:20])
            
     
            check_length = min(actual_count, int(1e-6 / time_interval_s))
            
 
            minC = np.min(C8[25:check_length])
            minD = np.min(D8[25:check_length])
            
            deltaC = minC - baseline_C  
            deltaD = minD - baseline_D
            
 
            if not (deltaC < THR_COUNTS_CD or deltaD < THR_COUNTS_CD):
                continue
            
     
            C_voltage = pda.fastAdc2mV(C8, ps.PS5000A_RANGE["PS5000A_500MV"], maxADC)
            D_voltage = pda.fastAdc2mV(D8, ps.PS5000A_RANGE["PS5000A_500MV"], maxADC)

           
            A8 = A_counts
            B8 = B_counts
            
            A_voltage = pda.fastAdc2mV(A8, ps.PS5000A_RANGE["PS5000A_1V"], maxADC)
            B_voltage = pda.fastAdc2mV(B8, ps.PS5000A_RANGE["PS5000A_1V"], maxADC)
            A_min_value = np.min(A_voltage)
            A_max_index = np.argmax(A_voltage)
            A_max_value = np.max(A_voltage)

            B_min_value = np.min(B_voltage)
            B_max_index = np.argmax(B_voltage)
            B_max_value = np.max(B_voltage)

            # print(f"A channel - max: {A_max_value} at index {A_max_index}")
            # print(f"B channel - max: {B_max_value} at index {B_max_index}")


            t0 = -PRE_TRIGGER_SAMPLE * time_interval_s
            t1 = (actual_count - PRE_TRIGGER_SAMPLE - 1) * time_interval_s
            time_s = np.arange(actual_count) * time_interval_s - PRE_TRIGGER_SAMPLE * time_interval_s
            
            time_s_new = np.linspace(t0, t1, Nout)
            

            A_voltage_new = sincx_interp(time_s_new, time_s, A_voltage)
            B_voltage_new = sincx_interp(time_s_new, time_s, B_voltage)
            C_voltage_new = sincx_interp(time_s_new, time_s, C_voltage)
            D_voltage_new = sincx_interp(time_s_new, time_s, D_voltage)
            

            myROOT.fill(Time=time_s_new, ChA=A_voltage_new, ChB=B_voltage_new, ChC=C_voltage_new, ChD=D_voltage_new)
            event_count += 1
            
            if event_count % 1000 == 0:
                print(f"✅ save events {event_count}/{TARGET_EVENTS} ")
            

            if event_count >= TARGET_EVENTS:
                break
        

        if event_count >= TARGET_EVENTS:
            break
    
    print(f"\n=== complete {batch_index} round, save {event_count} events to  {myROOT.filename} ===")
    batch_index += 1

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