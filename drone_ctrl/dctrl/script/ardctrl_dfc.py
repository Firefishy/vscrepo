#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
^----^
 *  * 
This program is ...
Drone control program for specific drone.
Title: The part of drone(Coptor) control program using dronekit python
Company: Systena Corporation Inc
Autor: y.s
Date: June, 2022

This program is based on following ... Ardupilot
------------------------------------------------------------------------------------------
© Copyright 2015-2016, 3D Robotics.
guided_set_speed_yaw.py: (Copter Only)
This example shows how to move/direct Copter and send commands 
in GUIDED mode using DroneKit Python.
Example documentation: http://python.dronekit.io/examples/guided-set-speed-yaw-demo.html
------------------------------------------------------------------------------------------
"""
from __future__ import print_function

#import sys
import math
#import numpy as np
#from numpy.core.numeric import True_
import time
#import datetime
#from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
#from threading import current_thread
import json
#import traceback
#import os

#from configparser import ConfigParser
#from std_msgs.msg import Float64, Float32, String, Int32

from dronekit import connect, VehicleMode, LocationGlobal, LocationGlobalRelative, Command
from pymavlink import mavutil
#from multiprocessing import Value, Process
#from geometry_msgs.msg import PoseStamped

import dlogger as dlog
import ardctrl

##################################################################
### Ardupilot drone mission control command class
##################################################################
class ArdCtrlFlt(ardctrl.ArdCtrlCmd):

    def __init__(self):
        #print("init")
        self.vehicle = ardctrl.ArdCtrlCmd.vehicle
        dlog.LOG("INFO", "dctrl_mission_class init")

    ### =================================================================================== 
    ### SimpleGoto
    ### =================================================================================== 
    def vehicle_goto(self, cmd):            
        dlog.LOG("DEBUG","Start Simple-GOTO")
        point = LocationGlobalRelative(
            float(cmd["d_lat"]), 
            float(cmd["d_lon"]), 
            float(cmd["d_alt"]) 
        )
        # point = LocationGlobalRelative(
        #     cmd["d_lat"], 
        #     cmd["d_lon"], 
        #     cmd["d_alt"] 
        # )
        self.vehicle.simple_goto(point, groundspeed=5)