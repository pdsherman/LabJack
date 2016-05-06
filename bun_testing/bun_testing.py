"""
File:   bun_testing.py 
Author: pdsherman
Date:   23 Feb. 2016

Description: Plan is to use the LabJack U6 data to collect
analog values from the laser distance sensor used for the bun
subsystem. The data is planned to be used to help design,
test and analyze the control for the bun dispense.

Note: Libraries and examples from LabJack.com were
used heavily during the creation of this script
"""
from __future__ import print_function
from datetime import datetime
import sys
import time
import u6
import numpy
import matplotlib.pyplot as plt

#--- variables used in script ---#
start_time = 0
stop_time = 0

#--- U6 device ---#
d = u6.U6()

#--- Set calibration data for U6 device ---#
d.getCalibrationData()

#--- Stream configuration ---#
#Note: not all arguments are listed (using defaults)
#see source file for u6 module for details
numChannels = 1 #number of channels
ri = 1 # resolution index
spp = 25 #samples per packet
sf = 0   #settling factor
cNums = [0] #channel numbers
cOpt = [0] #channel options
si = 60000 #scan interval

d.streamConfig(NumChannels = numChannels, ResolutionIndex = ri,
        SamplesPerPacket = spp,  SettlingFactor = sf,
        ChannelNumbers = cNums, ChannelOptions = cOpt, 
        ScanInterval = si)

#--- Define start and stop conditions ---#
#set up IO for digital input to use as a start/stop trigger
d.getFeedback( u6.PortDirWrite([0, 0, 0]) )

def start_check():
    io = d.getFeedback(u6.PortStateRead())
    bit = u6.getBit(io[0]['FIO'], 0)
    return bool(bit)

def stop_check():
    return not start_check()

#--- Stream data and collect ---#
try:
    while(True):
        results = list([])
        start_time = time.time()

        #Wait for start condition to start streaming data
        print("Waiting for start trigger.")
        while not start_check(): pass

        print("Starting stream...")
        d.streamStart() 
        start_time = time.time()

        missed = 0

        for r in d.streamData():
            if r is not None:
                #Check if errors occurred 
                if r['errors'] != 0:
                    print("Error: {} : {}".format(r['errors'], datetime.now()))

                #Check number of packets
                if r['numPackets'] != d.packetsPerRequest:
                    print("UNDERFLOW: {} : {}".format(r['numPackets'], datetime.now()))

                #Any missed samples
                if r['missed'] != 0:
                    missed += r['missed']
                    print("MISSED SAMPLES: {}".format(r['missed']))

                #Get results
                results += r['AIN0']

                #Stop condition
                if stop_check():
                    stop_time = time.time()
                    d.streamStop()
                    print("Stop triggered.")
                    break
            else:
                #Got no data back.
                #Stream isn't faster than USB read timeout, ~1 sec
                print("No data")

        num_samples = len(results)
        print("Length of sampling time: " + str(stop_time-start_time) + " seconds.")
        print("Number of samples: " + str(num_samples) )

        #--- convert results (Volts to Inches) ---#
        v_to_in = 38.08
        v_at_zero = 0.123
        dist = [(x - v_at_zero)*v_to_in for x in results]

        sample_rate = 0.015
        time_vec = [x*sample_rate for x in range(num_samples)]

        #--- save data to cvs file ---#
        #Get filename
        #filename = raw_input("Filename: ")
        filename = "test"

        #open file and write all data to new file
        with open(filename, 'w') as f:
            col_titles = "time (sec),distance (in)\n"
            f.write(col_titles)
            for (t, x) in zip(time_vec, dist):
                line = str(t) + ',' + str(x) + '\n'
                f.write(line)

        #--- Plot Results ---#
        plt.plot(time_vec, dist)
        plt.title("Bun Hopper Distance Testing")
        plt.xlabel("Time (sec)")
        plt.ylabel("Distance (in)")
        plt.show()
except:
    print("Exiting program.")
    d.hardReset()
    d.close()
    sys.exit()

