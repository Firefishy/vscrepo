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
Date: Aug, 2022

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
import math
import time
import json
from dronekit import connect, VehicleMode, LocationGlobal, LocationGlobalRelative, Command
from pymavlink import mavutil
import dlogger as dlog

##################################################################
### Ardupilot drone control base class
##################################################################
class ArdCtrlCls():
    
    vehicle = ""
    dinfo = ""

    ### =================================================================================== 
    ### MQTTで送信するドローンの情報:クライアントへ送信
    ###     ドローンのステータス及び現在位置情報
    ### =================================================================================== 
    drone_info = {  
        "status":{  
            "isArmable":"false",
            "Arm":"false",
            "FlightMode":"false",
            "dinfo":""
        },
        "battery":{
            "voltage":"0.0",
            "current":"0.0"
        },
        "gps":{
            "count":"0"
        },
        "position":{ 
            "latitude":"35.0000", 
            "longitude":"135.0000",
            "altitude":"20",
            "heading":"0",
            "speed":"0"
        }
    } 
    
    def __init__(self):
        dlog.LOG("INFO", "ard_control_class init")

    ### =================================================================================== 
    ### Connec to vehicle
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
    ### Vehicle close
    ### =================================================================================== 
    def close_vehicle(self):
        dlog.LOG("DEBUG", "START")      
        self.vehicle.close()
        dlog.LOG("DEBUG", "END")

    ### =================================================================================== 
    ### Add observer for the custom attribute
    ### =================================================================================== 
    def raw_msg_callback(self, attr_name, value):
        # attr_name == 'raw_imu'
        # value == vehicle.raw_imu
        print(value)
        dlog.LOG("INFO", value)
    def get_custom_message(self, message):
        self.vehicle.add_attribute_listener(message, self.raw_msg_callback)

    ### =================================================================================== 
    ### Set drone information (use for transfar to server by MQTT)
    ### =================================================================================== 
    def set_vehicle_info(self):
        # Is Armable ？
        self.drone_info["status"]["isArmable"] = str(self.vehicle.is_armable)           
        # ARMING status
        self.drone_info["status"]["Arm"] = str(self.vehicle.armed)                 
        # Flight mode
        self.drone_info["status"]["FlightMode"] = str(self.vehicle.mode.name)                 
        # Battery voltage
        self.drone_info["battery"]["voltage"] = str(self.vehicle.battery.voltage)             
        # Battery current
        self.drone_info["battery"]["voltage"] = str(self.vehicle.battery.current)             
        # latitude
        self.drone_info["position"]["latitude"] = str(self.vehicle.location.global_frame.lat) 
        # longitude
        self.drone_info["position"]["longitude"] = str(self.vehicle.location.global_frame.lon)
        # altitude
        self.drone_info["position"]["altitude"] = str(self.vehicle.location.global_relative_frame.alt) 
        # Drone heading
        self.drone_info["position"]["heading"] = str(self.vehicle.heading) 
        # Drone Speed
        self.drone_info["position"]["speed"] = str(self.vehicle.groundspeed) 
        # GPS count
        #self.drone_info["gps"]["count"] = str(self.vehicle.gps_0.num_sat)

        self.drone_info["status"]["info"] = self.dinfo 
    
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

    ### =============================================================================================
    ### End of file
    ### =============================================================================================