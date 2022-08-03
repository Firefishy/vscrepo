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

##################################################################
### Ardupilot drone control base class
##################################################################
class ArdCtrl():
    
    vehicle = ""

    ### =================================================================================== 
    ### MQTTで送信するドローンの情報:クライアントへ送信
    ###     ドローンのステータス及び現在位置情報
    ### =================================================================================== 
    drone_info = {  
        "status":{  
            "isArmable":"false",
            "Arm":"false",
            "FlightMode":"false"
        },
        "position":{ 
            "latitude":"35.0000", 
            "longitude":"135.0000",
            "altitude":"20",
            "heading":"0"
        }
    } 
    
    def __init__(self):
        #print("init")
        dlog.LOG("INFO", "Ardctrl_class init")

    ### =================================================================================== 
    ### Vehicleに接続
    ### =================================================================================== 
    def connect_vehicle(self, json_file):
        dlog.LOG("DEBUG", "START")
        msgstr = "Connect to vehicle object:" + json_file
        dlog.LOG("DEBUG", msgstr)
        json_open = open(json_file, 'r')
        json_load = json.load(json_open)
        connection_string = (json_load['connection']['sim'])
        dlog.LOG("DEBUG", json_file)
        
        # Store connrction information
        self.SETTING_JSON = json_file

        dlog.LOG("DEBUG", "SETTING_JSON: " + self.SETTING_JSON)
        dlog.LOG("DEBUG", "connection_string: " + connection_string)

        # Connect to Vehicle
        dlog.LOG("DEBUG", "Connecting to vehicle on: " + str(connection_string))
        self.vehicle = connect(connection_string, wait_ready=True)
        self.vehicle.wait_ready('autopilot_version')

        dlog.LOG("DEBUG", "END")

    ### =================================================================================== 
    ### Vehicleクローズ
    ### =================================================================================== 
    def close_vehicle(self):
        dlog.LOG("DEBUG", "START")      
        self.vehicle.close()
        dlog.LOG("DEBUG", "END")

    ### =================================================================================== 
    ### ドローンの情報をセット
    ### =================================================================================== 
    def set_vehicle_info(self):
        self.drone_info["status"]["isArmable"] = str(self.vehicle.is_armable)                 # ARM可能か？
        self.drone_info["status"]["Arm"] = str(self.vehicle.armed)                            # ARM状態
        self.drone_info["status"]["FlightMode"] = str(self.vehicle.mode.name)                 # フライトモード
        self.drone_info["position"]["latitude"] = str(self.vehicle.location.global_frame.lat) # 緯度
        self.drone_info["position"]["longitude"] = str(self.vehicle.location.global_frame.lon)# 経度
        self.drone_info["position"]["altitude"] = str(self.vehicle.location.global_relative_frame.alt) # 高度
        self.drone_info["position"]["heading"] = str(self.vehicle.heading) 
    
    ### =============================================================================================
    ### ドローンの属性を取得しコンソールに表示する（のみ）
    ### =============================================================================================
    def dsp_attributes(self):
        dlog.LOG("DEBUG", "START")
        # Get all vehicle attributes (state)
        dlog.LOG("INFO","\n---- Vehicle attributes ----------------------------------------")
        dlog.LOG("INFO","Ardupilot Firmware version: " + str(self.vehicle.version))
        # dlog.LOG("INFO","  Major version number: " + str(self.vehicle.version.major))
        # dlog.LOG("INFO","  Minor version number: " + str(self.vehicle.version.minor))
        # dlog.LOG("INFO","  Patch version number: " + str(self.vehicle.version.patch))
        # dlog.LOG("INFO","  Release type: " + self.vehicle.version.release_type())
        # dlog.LOG("INFO","  Release version: " + str(self.vehicle.version.release_version()))
        # dlog.LOG("INFO","  Stable release?: " + str(self.vehicle.version.is_stable()))
        # dlog.LOG("INFO","Autopilot capabilities")
        # dlog.LOG("INFO","  Supports MISSION_FLOAT message type: " + str(self.vehicle.capabilities.mission_float))
        # dlog.LOG("INFO","  Supports PARAM_FLOAT message type: " + str(self.vehicle.capabilities.param_float))
        # dlog.LOG("INFO","  Supports MISSION_INT message type: " + str(self.vehicle.capabilities.mission_int))
        # dlog.LOG("INFO","  Supports COMMAND_INT message type: " + str(self.vehicle.capabilities.command_int))
        # dlog.LOG("INFO","  Supports PARAM_UNION message type: " + str(self.vehicle.capabilities.param_union))
        # dlog.LOG("INFO","  Supports ftp for file transfers: " + str(self.vehicle.capabilities.ftp))
        # dlog.LOG("INFO","  Supports commanding attitude offboard: " + str(self.vehicle.capabilities.set_attitude_target))
        # dlog.LOG("INFO","  Supports commanding position and velocity targets in local NED frame: " + str(self.vehicle.capabilities.set_attitude_target_local_ned))
        # dlog.LOG("INFO","  Supports set position + velocity targets in global scaled integers: " + str(self.vehicle.capabilities.set_altitude_target_global_int))
        # dlog.LOG("INFO","  Supports terrain protocol / data handling: " + str(self.vehicle.capabilities.terrain))
        # dlog.LOG("INFO","  Supports direct actuator control: " + str(self.vehicle.capabilities.set_actuator_target))
        # dlog.LOG("INFO","  Supports the flight termination command: " + str(self.vehicle.capabilities.flight_termination))
        # dlog.LOG("INFO","  Supports mission_float message type: " + str(self.vehicle.capabilities.mission_float))
        # dlog.LOG("INFO","  Supports onboard compass calibration: " + str(self.vehicle.capabilities.compass_calibration))
        dlog.LOG("INFO","Global Location: " + str(self.vehicle.location.global_frame))
        dlog.LOG("INFO","Global Location (relative altitude): " + str(self.vehicle.location.global_relative_frame))
        dlog.LOG("INFO","Local Location: " + str(self.vehicle.location.local_frame))
        dlog.LOG("INFO","Attitude: " + str(self.vehicle.attitude))
        dlog.LOG("INFO","Velocity: " + str(self.vehicle.velocity))
        dlog.LOG("INFO","GPS: " + str(self.vehicle.gps_0))
        dlog.LOG("INFO","Gimbal status: " + str(self.vehicle.gimbal))
        dlog.LOG("INFO","Battery: " + str(self.vehicle.battery))
        dlog.LOG("INFO","EKF OK?: " + str(self.vehicle.ekf_ok))
        dlog.LOG("INFO","Last Heartbeat: " + str(self.vehicle.last_heartbeat))
        # dlog.LOG("INFO","Rangefinder: " + str(self.vehicle.rangefinder))
        # dlog.LOG("INFO","Rangefinder distance: " + str(self.vehicle.rangefinder.distance))
        # dlog.LOG("INFO","Rangefinder voltage: " + str(self.vehicle.rangefinder.voltage))
        dlog.LOG("INFO","Heading: " + str(self.vehicle.heading))
        dlog.LOG("INFO","Is Armable?: " + str(self.vehicle.is_armable))
        dlog.LOG("INFO","System status: " + str(self.vehicle.system_status.state))
        dlog.LOG("INFO","Groundspeed: " + str(self.vehicle.groundspeed))    # settable
        dlog.LOG("INFO","Airspeed: " + str(self.vehicle.airspeed))    # settable
        dlog.LOG("INFO","Mode: " + str(self.vehicle.mode.name))    # settable
        dlog.LOG("INFO","Armed: " + str(self.vehicle.armed))    # settable
        dlog.LOG("INFO","----------------------------------------------------------------\n")
        dlog.LOG("DEBUG", "END")

##################################################################
### Ardupilot drone control command class
##################################################################
class ArdCtrlCmd(ArdCtrl):

    def __init__(self):
        self.vehicle = ArdCtrl.vehicle
        #print("init")
        dlog.LOG("INFO", "dctrl_command_classinit")

    ### =================================================================================== 
    ### Vehicleのモードを設定
    ### =================================================================================== 
    def set_vehicle_mode(self, mode):
        dlog.LOG("DEBUG","SET MODE: " + mode)
        self.vehicle.mode = VehicleMode(mode)

    ### =================================================================================== 
    ### Arming
    ### =================================================================================== 
    def vehicle_arming(self):
        dlog.LOG("DEBUG","ARMING:")
        if self.vehicle.is_armable == True:
            if self.vehicle.armed:
                dlog.LOG("DEBUG","すでにARMしています。")
            else:
                self.vehicle.armed = True
        else:
            dlog.LOG("DEBUG","ARMできません。")

    ### =================================================================================== 
    ### Disarm
    ### =================================================================================== 
    def vehicle_disarming(self):
        dlog.LOG("DEBUG","ARMING:")
        if not self.vehicle.armed:
            dlog.LOG("DEBUG","すでにDISARM状態です。")
        else:
            self.vehicle.armed = False

    ### =================================================================================== 
    ### Take off
    ### =================================================================================== 
    def vehicle_takeoff(self, alt):
        dlog.LOG("DEBUG","TAKEOFF")
        self.vehicle.simple_takeoff(alt)  # Take off to target altitude

    ### =================================================================================== 
    ### Automatic arming and takeoff to set altitide
    ### =================================================================================== 
    def arm_and_takeoff(self, aTargetAltitude):
        dlog.LOG("DEBUG", "START")
        count = 0   
        msgstr = ""
        # Don't let the user try to arm until autopilot is ready
        while not self.vehicle.is_armable:
            msgstr = "Vehicle準備中 しばらくお待ちください(30秒程度かかる場合があります): " + str(count) + " 秒経過"
            dlog.LOG("DEBUG", msgstr)
            #self.pub_state(msgstr)
            time.sleep(1)
            count += 1
        msgstr = "Vehicle Arm開始しています"
        dlog.LOG("DEBUG",msgstr)
        #self.pub_state(msgstr)

        # Arming check: 0 is disable
        # ArdCtrl.vehicle.parameters['ARMING_CHECK'] = 0

        # Copter should arm in GUIDED mode
        self.vehicle.mode = VehicleMode("GUIDED")
        self.vehicle.armed = True

        while not self.vehicle.armed:      
            msgstr = "Vehicle Armしています"
            dlog.LOG("INFO", msgstr)
            #self.pub_state(msgstr)
            time.sleep(1)

        msgstr = "Vehicle 離陸しています"
        dlog.LOG("INFO", msgstr) 
        ArdCtrl.self.simple_takeoff(aTargetAltitude) # Take off to target altitude

        # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command 
        #  after Vehicle.simple_takeoff will execute immediately).
        while True:
            msgstr = "Vehicle現在高度: " + str(self.vehicle.location.global_relative_frame.alt)
            dlog.LOG("INFO", msgstr) 
            #self.pub_state(msgstr)
            if self.vehicle.location.global_relative_frame.alt>=aTargetAltitude*0.95: #Trigger just below target alt.
                msgstr = "設定高度に到達しました"      
                dlog.LOG("DEBUG", msgstr) 
                #self.pub_state(msgstr)
                break
            time.sleep(1)
        dlog.LOG("DEBUG", "END") 


##################################################################
### Ardupilot drone mission control command class
##################################################################
# class ArdCtrlMission(ArdCtrl):

#     def __init__(self):
#         #print("init")
#         dlog.LOG("INFO", "dctrl_mission_class init")

#     ### =================================================================================== 
#     ### SimpleGoto
#     ### =================================================================================== 
#     def vehicle_goto(self, cmd):            
#         dlog.LOG("DEBUG","Sinple GOTO")
#         point = LocationGlobalRelative(
#             float(cmd["d_lat"]), 
#             float(cmd["d_lon"]), 
#             float(cmd["d_alt"]) 
#         )
#         # point = LocationGlobalRelative(
#         #     cmd["d_lat"], 
#         #     cmd["d_lon"], 
#         #     cmd["d_alt"] 
#         # )
#         ArdCtrl.vehicle.simple_goto(point, groundspeed=5)





# ardcls = ArdCtrl.DrnCtrl.get_instance()

# ardcls.set_vehicle_mode('GUIDED')



