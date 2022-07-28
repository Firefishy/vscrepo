#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
//////////////////////////////////////////////////////////////////////////////////////////
 ^----^
  *  * 
   ~
This program is control program for Drone 
based on following ... Ardupilot
------------------------------------------------------------------------------------------
© Copyright 2015-2016, 3D Robotics.
guided_set_speed_yaw.py: (Copter Only)
This example shows how to move/direct Copter and send commands 
in GUIDED mode using DroneKit Python.
Example documentation: http://python.dronekit.io/examples/guided-set-speed-yaw-demo.html
------------------------------------------------------------------------------------------
and modification and added methods for delivery drone project by ....
Title: Drone(Coptor) control program based on dronekit python
Company: Systena Corporation Inc
Autor: y.saito
Date: 2nd Dec, 2021
//////////////////////////////////////////////////////////////////////////////////////////
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

# from enum import IntEnum, auto

# class cmdFrom(IntEnum):
#     MapMoveSimple = auto()
#     MapMoveVelocity = auto()
#     SlideMoveSimple = auto()
#     SlideMoveVelocity = auto()

##################################################################
### Class as singleton
##################################################################
class Dctr_Singleton(object):
    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        #    cls._instance = cls(input)
        # else:
        #     cls._instance.input = input
        return cls._instance

##################################################################
### Drone control class
##################################################################
class DrnCtrl(Dctr_Singleton):

    vehicle = ""
    compass_data = 0.0
    droneCntAlt = 0.0

    moveMode = 0
    MOVE_MODE_NONE  = 0
    MOVE_MODE_S1  = 1001
    MOVE_MODE_S2  = 2001
    MOVE_MODE_S3  = 3001
    MOVE_MODE_LAND = 4001
    MOVE_MODE_ALL = 7001

    gspeed = 0.7

    # Step1移動量を算出するためのパラメータ
    ASP_RATIO_H = 1440/640  # ratio
    ASP_RATIO_V = 1080/480  # ratio
    PIXEL_PITCH = 0.0000014 # unit = m
    FOCAL_LENGTH = 0.00188  # unit = m
    DRONE_HEIGHT = 30       # unit = m
    ADJ_FACTOR = 0.93       # adjustment factor
    
    dist2object = 3
    flgGotMoveCmd = 0
    YAW_CW = 1
    YAW_CCW = -1

    # 制御用サブコマンド
    SMODE0 = 0
    SMODE1 = 1
    SMODE2 = 2
    SMODE3 = 3
    SMODE4 = 4
    SMODE5 = 5

    SMODE_SIMPLE_MAP = 1001
    SMODE_VELOCITY_MAP = 1002
    SMODE_SIMPLE_SLD = 2001
    SMODE_VELOCITY_SLD = 2002

    NED_SIMPLE_STP1 = 1000      # Simple goto by map clicked
    NED_SIMPLE_STP2 = 2000      # Simple goto by slider input
    NED_SIMPLE_STP3 = 3000      # 
    NED_VELOCITY_STP1 = 1001    # Velocity control by map clicked
    NED_VELOCITY_STP2 = 2001    # Velocity control by slider input
    NED_VELOCITY_STP3 = 3001    #

    SETTING_JSON = ""
    CURRENT_ALT = 0.0
    DIST_FORWARD = 0.0
    DIST_DOWN = 0.0
    
    # Step1msg
    STEP1_COMP = ""

    # Step2msg
    DOOR_RESULT_MSG = ""
    DOOR_SCORE = 0.0
    DOOR_DIST = 0.0
    DOORCCX = 0
    DOORCCY = 0
    STEP2_COMP = ""
    STEP3_SCORE = 0.0

    # Step3msg
    GROUND_RESULT_MSG = ""
    GROUND_SCORE = 0.0
    STEP3_COMP = ""

    #droneInfoMsg = DroneInfo()

    ### =================================================================================== 
    ### MQTTで受信するドローンの情報:クライアントから受信
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

    ### =================================================================================== 
    ### コンストラクタ
    ### =================================================================================== 
    def __init__(self):
        #print("init")
        dlog.LOG("INFO", "dctrl_cls init")

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
        self.drone_info["position"]["heading"] = str(self.vehicle.heading)                    # 方位
    
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
    ### Goto
    ### =================================================================================== 
    def vehicle_goto(self, cmd):            
        dlog.LOG("DEBUG","Sinple GOTO")
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

    ### =================================================================================== 
    ### 自動 ARMと離陸
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
        # self.vehicle.parameters['ARMING_CHECK'] = 0

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
        self.vehicle.simple_takeoff(aTargetAltitude) # Take off to target altitude

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

    ### =================================================================================== 
    ### Vehicleクローズ
    ### =================================================================================== 
    def close_vehicle(self):
        dlog.LOG("DEBUG", "START")      
        self.vehicle.close()
        dlog.LOG("DEBUG", "END")      

    ### =============================================================================================
    ### ドローンの属性を取得しコンソールに表示する（のみ）
    ### =============================================================================================
    def dsp_attributes(self):
        dlog.LOG("DEBUG", "START")
        # Get all vehicle attributes (state)
        dlog.LOG("INFO","\n---- Vehicle attributes ----------------------------------------")
        dlog.LOG("INFO","Ardupilot Firmware version: " + str(self.vehicle.version))
        dlog.LOG("INFO","  Major version number: " + str(self.vehicle.version.major))
        dlog.LOG("INFO","  Minor version number: " + str(self.vehicle.version.minor))
        dlog.LOG("INFO","  Patch version number: " + str(self.vehicle.version.patch))
        dlog.LOG("INFO","  Release type: " + self.vehicle.version.release_type())
        dlog.LOG("INFO","  Release version: " + str(self.vehicle.version.release_version()))
        dlog.LOG("INFO","  Stable release?: " + str(self.vehicle.version.is_stable()))
        dlog.LOG("INFO","Autopilot capabilities")
        dlog.LOG("INFO","  Supports MISSION_FLOAT message type: " + str(self.vehicle.capabilities.mission_float))
        dlog.LOG("INFO","  Supports PARAM_FLOAT message type: " + str(self.vehicle.capabilities.param_float))
        dlog.LOG("INFO","  Supports MISSION_INT message type: " + str(self.vehicle.capabilities.mission_int))
        dlog.LOG("INFO","  Supports COMMAND_INT message type: " + str(self.vehicle.capabilities.command_int))
        dlog.LOG("INFO","  Supports PARAM_UNION message type: " + str(self.vehicle.capabilities.param_union))
        dlog.LOG("INFO","  Supports ftp for file transfers: " + str(self.vehicle.capabilities.ftp))
        dlog.LOG("INFO","  Supports commanding attitude offboard: " + str(self.vehicle.capabilities.set_attitude_target))
        dlog.LOG("INFO","  Supports commanding position and velocity targets in local NED frame: " + str(self.vehicle.capabilities.set_attitude_target_local_ned))
        dlog.LOG("INFO","  Supports set position + velocity targets in global scaled integers: " + str(self.vehicle.capabilities.set_altitude_target_global_int))
        dlog.LOG("INFO","  Supports terrain protocol / data handling: " + str(self.vehicle.capabilities.terrain))
        dlog.LOG("INFO","  Supports direct actuator control: " + str(self.vehicle.capabilities.set_actuator_target))
        dlog.LOG("INFO","  Supports the flight termination command: " + str(self.vehicle.capabilities.flight_termination))
        dlog.LOG("INFO","  Supports mission_float message type: " + str(self.vehicle.capabilities.mission_float))
        dlog.LOG("INFO","  Supports onboard compass calibration: " + str(self.vehicle.capabilities.compass_calibration))
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
        dlog.LOG("INFO","Rangefinder: " + str(self.vehicle.rangefinder))
        dlog.LOG("INFO","Rangefinder distance: " + str(self.vehicle.rangefinder.distance))
        dlog.LOG("INFO","Rangefinder voltage: " + str(self.vehicle.rangefinder.voltage))
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
    ###
    ### =============================================================================================
    def get_location_metres(self,original_location, dNorth, dEast):
        """
        Returns a LocationGlobal object containing the latitude/longitude `dNorth` and `dEast` metres from the 
        specified `original_location`. The returned Location has the same `alt` value
        as `original_location`.

        The function is useful when you want to move the vehicle around specifying locations relative to 
        the current vehicle position.
        The algorithm is relatively accurate over small distances (10m within 1km) except close to the poles.
        For more information see:
        http://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
        """
        earth_radius=6378137.0 #Radius of "spherical" earth
        #Coordinate offsets in radians
        dLat = dNorth/earth_radius
        dLon = dEast/(earth_radius*math.cos(math.pi*original_location.lat/180))

        #New position in decimal degrees
        newlat = original_location.lat + (dLat * 180/math.pi)
        newlon = original_location.lon + (dLon * 180/math.pi)
        return LocationGlobal(newlat, newlon,original_location.alt)

    ### =============================================================================================
    ### 2 つの LocationGlobal オブジェクト間の地上距離をメートル単位で返します。
    ###    このメソッドは近似値であり、長距離や地球の極の近くでは正確ではありません。
    ###    これはArduPilotのテストコードに由来しています。
    ###    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    ### =============================================================================================
    def get_distance_metres(self, aLocation1, aLocation2):
        dlat = aLocation2.lat - aLocation1.lat
        dlong = aLocation2.lon - aLocation1.lon
        return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5

    ### =============================================================================================
    ### 現在のウェイポイントまでの距離をメートル単位で取得します。 
    ### 最初のウェイポイント（原点）に対しては、Noneを返します。
    ### =============================================================================================
    def distance_to_current_waypoint(self):
        nextwaypoint = self.vehicle.commands.next
        if nextwaypoint==0:
            return None
        missionitem=self.vehicle.commands[nextwaypoint-1] #commands are zero indexed
        lat = missionitem.x
        lon = missionitem.y
        alt = missionitem.z
        targetWaypointLocation = LocationGlobalRelative(lat,lon,alt)
        distancetopoint = self.get_distance_metres(self.vehicle.location.global_frame, targetWaypointLocation)
        return distancetopoint

    ### =============================================================================================
    ### 車両から現在のミッションをダウンロードする。
    ### =============================================================================================
    def download_mission(self):
        cmds = self.vehicle.commands
        cmds.download()
        cmds.wait_ready() # wait until download is complete.

    
    def adds_square_fence(self, aLocation, aSize):
        cmds = self.vehicle.commands
        print(" Clear any existing commands")
        cmds.clear() 
        print(" Define/add new commands.")
        # 新しいコマンドを追加します。パラメータの意味/順序はCommandクラスに記載されています。
        # MAV_CMD_NAV_TAKEOFF コマンドを追加しました。すでに空中にいる場合は無視されます。
        cmds.add(
            Command
            ( 
                4, 
                0, 
                0, 
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # グローバル（WGS84）座標フレーム+ホームポジションを基準とした高度。最初の値/x：緯度、2番目の値/ y：経度、3番目の値/ z：正の高度。0はホームポジションの高度です。
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,            # 地面/手からの離陸
                0, 
                0, 
                0, 
                0, 
                0, 
                0, 
                0, 
                0, 
                10
            )
        )

        # MAV_CMD_NAV_WAYPOINT を4 箇所定義し、コマンドを追加します。
        point1 = self.get_location_metres(aLocation, aSize, -aSize)
        point2 = self.get_location_metres(aLocation, aSize, aSize)
        point3 = self.get_location_metres(aLocation, -aSize, aSize)
        point4 = self.get_location_metres(aLocation, -aSize, -aSize)

        """
        https://mavlink.io/en/messages/common.html#enums
        ミッションメッセージ

        """

        cmds.add(
            Command( 
                0,                                              # Target System ID
                0,                                              # Target Component ID
                0,                                              # Waypoint ID
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # frame: グローバル（WGS84）座標フレーム+ホームポジションを基準とした高度。最初の値/x：緯度、2番目の値/ y：経度、3番目の値/ z：正の高度。0はホームポジションの高度です。
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,           # command: ウェイポイントへの移動 
                0,                                              # current: false=0, true=1
                0,                                              # autocontinue to next waypoint 
                0,                                              # param1:
                0,                                              # param2:
                0,                                              # param3:
                0,                                              # param4:
                point1.lat,                                     # 緯度(ローカル:x(m)x10^4, グローバル:緯度x10^7)
                point1.lon,                                     # 経度(ローカル:y(m)x10^4, グローバル:経度x10^7)
                11                                              # 高度(m) 相対、絶対
            )
        )
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point2.lat, point2.lon, 12))
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point3.lat, point3.lon, 13))
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point4.lat, point4.lon, 14))
        
        # 4地点にダミーのウェイポイント "5 "を追加（目的地に到着したことを知ることができる）
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point4.lat, point4.lon, 14))    

        msg = " Upload new commands to vehicle"
        dlog.LOG("DEBUG", msg)
        cmds.upload()


    ### =============================================================================================
    ### 現在のミッションに離陸コマンドと4つのウェイポイントコマンドを追加する。
    ###        ウェイポイントは、指定されたLocationGlobal (aLocation)を中心に、辺の長さ2*aSizeの正方形を
    ###    形成するように配置される。
    ###    この関数は、vehicle.commandsが車両のミッションの状態と一致すると仮定しています。
    ###    (セッション中、ミッションをクリアした後に少なくとも一度はdownloadを呼び出す必要があります)    
    ### =============================================================================================
    def adds_square_mission(self, aLocation, aSize):
        cmds = self.vehicle.commands
        dlog.LOG("DEBUG"," Clear any existing commands")
        cmds.clear() 
        dlog.LOG("DEBUG"," Define/add new commands.")
        # 新しいコマンドを追加します。パラメータの意味/順序はCommandクラスに記載されています。
        # MAV_CMD_NAV_TAKEOFF コマンドを追加しました。すでに空中にいる場合は無視されます。
        cmds.add(
            Command
            ( 
                0, 
                0, 
                0, 
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # グローバル（WGS84）座標フレーム+ホームポジションを基準とした高度。最初の値/x：緯度、2番目の値/ y：経度、3番目の値/ z：正の高度。0はホームポジションの高度です。
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,            # 地面/手からの離陸
                0, 
                0, 
                0, 
                0, 
                0, 
                0, 
                0, 
                0, 
                10
            )
        )

        # MAV_CMD_NAV_WAYPOINT を4 箇所定義し、コマンドを追加します。
        point1 = self.get_location_metres(aLocation, aSize, -aSize)
        point2 = self.get_location_metres(aLocation, aSize, aSize)
        point3 = self.get_location_metres(aLocation, -aSize, aSize)
        point4 = self.get_location_metres(aLocation, -aSize, -aSize)

        """
        https://mavlink.io/en/messages/common.html#enums
        ミッションメッセージ

        """

        cmds.add(
            Command( 
                0,                                              # Target System ID
                0,                                              # Target Component ID
                0,                                              # Waypoint ID
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # frame: グローバル（WGS84）座標フレーム+ホームポジションを基準とした高度。最初の値/x：緯度、2番目の値/ y：経度、3番目の値/ z：正の高度。0はホームポジションの高度です。
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,           # command: ウェイポイントへの移動 
                0,                                              # current: false=0, true=1
                0,                                              # autocontinue to next waypoint 
                0,                                              # param1:
                0,                                              # param2:
                0,                                              # param3:
                0,                                              # param4:
                point1.lat,                                     # 緯度(ローカル:x(m)x10^4, グローバル:緯度x10^7)
                point1.lon,                                     # 経度(ローカル:y(m)x10^4, グローバル:経度x10^7)
                11                                              # 高度(m) 相対、絶対
            )
        )
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point2.lat, point2.lon, 12))
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point3.lat, point3.lon, 13))
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point4.lat, point4.lon, 14))
        
        # 4地点にダミーのウェイポイント "5 "を追加（目的地に到着したことを知ることができる）
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point4.lat, point4.lon, 14))    

        msg = " Upload new commands to vehicle"
        dlog.LOG("DEBUG", msg)
        cmds.upload()

    ### =============================================================================================
    ### ファイルからリストにミッションを読み込む。
    ###    ミッションの定義は、Waypointファイル
    ###    形式(http://qgroundcontrol.org/mavlink/waypoint_protocol#waypoint_file_format)です。
    ###    この関数は、upload_mission()で使用される。    
    ### =============================================================================================
    def readmission(self, aFileName):
        msgstr = "Reading mission from file: %s" % aFileName
        dlog.LOG("DEBUG", msgstr)
        missionlist=[]
        with open(aFileName) as f:
            for i, line in enumerate(f):
                if i==0:
                    if not line.startswith('QGC WPL 110'):
                        raise Exception('File is not supported WP version')
                else:
                    linearray=line.split('\t')
                    #ln_index=int(linearray[0])                  # INDEX: 0,1,2..　--> Don't use
                    ln_currentwp=int(linearray[1])              # CURRENT WP　--> Don't use
                    ln_frame=int(linearray[2])                  # COORD FRAME　--> [5]
                    ln_command=int(linearray[3])                # COMMAND --> [4]
                    ln_param1=float(linearray[4])               # PARAM1 --> [7]
                    ln_param2=float(linearray[5])               # PARAM2 --> [8]
                    ln_param3=float(linearray[6])               # PARAM3 --> [9]
                    ln_param4=float(linearray[7])               # PARAM4 --> [10]
                    ln_param5=float(linearray[8])               # PARAM5/LATITUDE --> [11]
                    ln_param6=float(linearray[9])               # PARAM6/LONGITUDE --> [12]
                    ln_param7=float(linearray[10])              # PARAM7/ALTITUDE --> [13]
                    ln_autocontinue=int(linearray[11].strip())  # AUTOCONTINUE --> [6]
                    mission_cmd = Command(
                        0,
                        0,
                        0,
                        ln_frame,
                        ln_command,
                        ln_currentwp,
                        ln_autocontinue,
                        ln_param1,
                        ln_param2,
                        ln_param3, 
                        ln_param4, 
                        ln_param5,
                        ln_param6,
                        ln_param7
                    )
                    missionlist.append(mission_cmd)
        f.close()
        return missionlist

    ### =============================================================================================
    ### ファイルからミッションデータをアップロードする。
    ### =============================================================================================
    def upload_mission(self, aFileName):
        #Read mission from file
        missionlist = self.readmission(aFileName)
        
        #print("\nUpload mission from a file: %s" % aFileName)
        #Clear existing mission from vehicle
        #print(' Clear mission')
        cmds = self.vehicle.commands
        cmds.clear()
        #Add new mission to vehicle
        for command in missionlist:
            cmds.add(command)
        print('Mission upload start')
        cmds.upload()
        print('Mission uploaded')

    ### =============================================================================================
    ### ファイルからジオフェンスデータをアップロードする。
    ### Refer: https://github.com/dronekit/dronekit-python/issues/1092
    ### =============================================================================================
    def upload_fence(self, aFileName):
        #Read mission from file
        missionlist = self.readmission(aFileName)
        
        #print("\nUpload fence from a file: %s" % aFileName)
        # Clear existing mission from vehicle
        # print(' Clear mission')
        cmds = self.vehicle.commands
        #cmds.clear()
        #Add new mission to vehicle
        for command in missionlist:
            # Missionの場合0のため、1に書き換える必要がある。
            command.mission_type = 1
            cmds.add(command)
        print('Upload fence start...')
        #self.vehicle.commands.upload()
        cmds.upload_fence()
        print('Upload fence end...')

    ### =============================================================================================
    ### 現在のミッションをダウンロードし、リストで返します。
    ### =============================================================================================
    def download_mission(self, ):
        """        
        save_mission() で、保存するファイル情報を取得するために使用される。
        """
        #print(" Download mission from vehicle")
        missionlist=[]
        cmds = self.vehicle.commands
        cmds.download()
        cmds.wait_ready()
        for cmd in cmds:
            missionlist.append(cmd)
        return missionlist

    ### =============================================================================================
    ### Save a mission in the Waypoint file format 
    ###    (http://qgroundcontrol.org/mavlink/waypoint_protocol#waypoint_file_format).
    ### =============================================================================================
    def save_mission(self, aFileName):
        #print("\nSave mission from Vehicle to file: %s" % aFileName)    
        #Download mission from vehicle
        missionlist = self.download_mission()
        #Add file-format information
        output='QGC WPL 110\n'
        #Add home location as 0th waypoint
        home = self.vehicle.home_location
        output+="%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (0,1,0,16,0,0,0,0,home.lat,home.lon,home.alt,1)
        #Add commands
        for cmd in missionlist:
            commandline="%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (cmd.seq,cmd.current,cmd.frame,cmd.command,cmd.param1,cmd.param2,cmd.param3,cmd.param4,cmd.x,cmd.y,cmd.z,cmd.autocontinue)
            output+=commandline
        with open(aFileName, 'w') as file_:
            #print(" Write mission to file")
            file_.write(output)
            
            
    ### =============================================================================================
    ### Print a mission file to demonstrate "round trip"
    ### =============================================================================================
    def printfile(self, aFileName):
        #print("\nMission file: %s" % aFileName)
        with open(aFileName) as f:
            for line in f:
                print(' %s' % line.strip())     

    ### =============================================================================================
    ### End of file
    ### =============================================================================================