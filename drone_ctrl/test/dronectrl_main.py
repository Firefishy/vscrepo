#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
This program is ...
main control program for delivery drone.
Title: Drone(Coptor) control program using dronekit python
Company: Systena Corporation Inc
Autor: y.saito
Date: 10th Oct, 2021
"""
import os
import sys
import time
import threading
import ardctrl_cls as accls
import dlogger as dlog

import tkinter as tk
from tkinter import ttk
import tkinter

import asyncio
import functools
import requests

# The tkinter root object
global root

# var
NED_VELOCITY = 11
YAW_CW = 1
YAW_CCW = -1
GROUND_SPEED = 5

# read path
base_path = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.normpath(os.path.join(base_path, '../json/setting.json'))
SETTING_JSON = json_path


###
### Main function
###
if __name__ == '__main__':

    ARM_HEIGHT = 3.0

    # Get instance of DroneController(by Dronekit)
    arduCtrlClass = accls.ArdCtrl.get_instance()
    print("instance1", arduCtrlClass)
    print("input json file is : {0}".format(arduCtrlClass.input))

    # Log: CRITICAL, ERROR < WARNING < INFO < DEBUG 
    #dlog = dlog.Dlog() 

    arduCtrlClass.connect_vehicle(SETTING_JSON)
    time.sleep(5)

    # try:
        # # Drone init, arm and takeoff
        # arduCtrlClass.pub_state("Vehicle初期化完了")
        # dlog.LOG("INFO", "Vehicle初期化完了")

        # # Get attributes
        # arduCtrlClass.dsp_attributes()

        # # Vehicle mode check
        # mode = arduCtrlClass.vehicle.mode
        # print("vehicle mode is : ", mode)
        
        # # if vehicle mode isn't GUIDED, set mode to GUIDED
        # if mode != "GUIDED":
        #     print("Vehicle mode set to GUIDED")
        #     arduCtrlClass.set_vehicle_mode("GUIDED")
        #     arduCtrlClass.pub_state("GUIDEDモードに設定")
        #     dlog.LOG("DEBUG", "GUIDEDモードに設定")
        # else:
        #     print("Vehicle mode is already GUIDED")
        #     arduCtrlClass.pub_state("すでにGUIDEDモードです")
        #     dlog.LOG("DEBUG", "すでにGUIDEDモードです")
        
        # # -- ARM and Take off -------------------------------------------------
        # # Drone arming
        # if arduCtrlClass.vehicle.armed == False:
        #    arduCtrlClass.arm_and_takeoff(ARM_HEIGHT)
        #    arduCtrlClass.pub_state("ARMと離陸開始:" + str(ARM_HEIGHT) + 'm')
        #    dlog.LOG("DEBUG", "ARMと離陸開始:" + str(ARM_HEIGHT) + 'm')
        # # Check drone is already arming or not
        # while arduCtrlClass.vehicle.armed == False:
        #     arduCtrlClass.pub_state("ARMと離陸をしています")
        #     dlog.LOG("DEBUG", "ARMしています...")
        #     time.sleep(1)
        # arduCtrlClass.pub_state("ARMと離陸完了")
        # dlog.LOG("INFO", "ARMと離陸完了:" + str(ARM_HEIGHT) + 'm')
        # # ----------------------------------------------------------------------

        # while True:
        #     time.sleep(0.1)


    # except KeyboardInterrupt:
    #     # Catch Ctrl-C
    #     msg = "キーボード例外処理発生"
    #     dlog.LOG("CRITICAL", msg)



