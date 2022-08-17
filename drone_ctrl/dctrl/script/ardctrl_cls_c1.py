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
import ardctrl_cls as ardctrl

##################################################################
### Ardupilot drone control command class
##################################################################
class ArdCtrlClsC1(ardctrl.ArdCtrlCls):

    def __init__(self):
        dlog.LOG("INFO", "ard_control_class(1) init")
        self.vehicle = ardctrl.ArdCtrlCls.vehicle

    ### =================================================================================== 
    ### Mode set
    ### =================================================================================== 
    def set_vehicle_mode(self, mode):
        dlog.LOG("DEBUG","SET MODE: " + mode)
        self.set_vehicle_csts("SET MODE: " + mode)
        self.vehicle.mode = VehicleMode(mode)

    ### =================================================================================== 
    ### Arming
    ### =================================================================================== 
    def vehicle_arming(self):
        dlog.LOG("DEBUG","ARMING:")
        if self.vehicle.is_armable:
            if self.vehicle.armed:
                dlog.LOG("DEBUG","すでにARMしています")
                self.set_vehicle_csts("Already Armed")
            else:
                self.vehicle.armed = True
                self.set_vehicle_csts("Arming")
        else:
            dlog.LOG("DEBUG","ARMできません。")

    ### =================================================================================== 
    ### Disarm
    ### =================================================================================== 
    def vehicle_disarming(self):
        dlog.LOG("DEBUG","DISARMING:")
        self.set_vehicle_csts("Disarming")
        if not self.vehicle.armed:
            dlog.LOG("DEBUG","すでにDISARM状態です")
        else:
            self.vehicle.armed = False

    ### =================================================================================== 
    ### Take off
    ### =================================================================================== 
    def vehicle_takeoff(self, alt):
        if self.vehicle.is_armable:
            dlog.LOG("DEBUG","TAKEOFF")
            self.set_vehicle_csts("Take off: " + str(alt) + "m")
            # Take off to target altitude
            self.vehicle.simple_takeoff(alt)  
            self.dinfo = "Take off done"
        else:
            dlog.LOG("DEBUG","ARMしていないためTAKEOFFできません")

    ### =================================================================================== 
    ### Auto takeoff
    ### =================================================================================== 
    def arm_and_takeoff(self, aTargetAltitude):
        dlog.LOG("DEBUG", "START")
        count = 0   
        msgstr = ""
        # Don't let the user try to arm until autopilot is ready
        while not self.vehicle.is_armable:
            msgstr = "Vehicle準備中 しばらくお待ちください(30秒程度かかる場合があります): " + str(count) + " 秒経過"
            dlog.LOG("DEBUG", msgstr)
            self.set_vehicle_csts(msgstr)
            time.sleep(1)
            count += 1
        msgstr = "Vehicle Arm開始しています"
        dlog.LOG("DEBUG",msgstr)
        self.set_vehicle_csts("Arming")

        # Copter should arm in GUIDED mode
        self.vehicle.mode = VehicleMode("GUIDED")
        self.vehicle.armed = True

        while not self.vehicle.armed:      
            msgstr = "Vehicle Armしています"
            dlog.LOG("INFO", msgstr)
            time.sleep(1)

        msgstr = "Vehicle 離陸しています"
        dlog.LOG("INFO", msgstr) 
        self.set_vehicle_csts("Take off")
        self.vehicle.simple_takeoff(aTargetAltitude) # Take off to target altitude

        # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command 
        #  after Vehicle.simple_takeoff will execute immediately).
        while True:
            msgstr = "Vehicle現在高度: " + str(self.vehicle.location.global_relative_frame.alt)
            dlog.LOG("INFO", msgstr)
            self.set_vehicle_csts("Alt: " + str(self.vehicle.location.global_relative_frame.alt) + "m")
            #self.pub_state(msgstr)
            if self.vehicle.location.global_relative_frame.alt>=aTargetAltitude*0.95: #Trigger just below target alt.
                msgstr = "設定高度に到達しました"      
                dlog.LOG("DEBUG", msgstr) 
                #self.pub_state(msgstr)
                break
            time.sleep(1)
        dlog.LOG("DEBUG", "END") 

    ### =============================================================================================
    ### Send Command by MAVLINK
    ### =============================================================================================
    def snd_cmd_mav(self,
        tsys,   # target system
        tcmp,   # target component
        cmd,
        para1, para2, para3, para4, para5, para6, para7
    ):
        dlog.LOG("DEBUG","START")
        mavmsg = self.vehicle.message_factory.command_long_encode(
            tsys, tcmp, # target system, target component
            cmd,    # command
            0,      # confirmation
            para1,  # parameter1
            para2,  # parameter2
            para3,  # parameter3
            para4,  # parameter4
            para5,  # parameter5
            para6,  # parameter6
            para7)  # parameter7
        # send command to vehicle
        self.vehicle.send_mavlink(mavmsg)

    ### =================================================================================== 
    ### Pause
    ### =================================================================================== 
    def pause_vehicle(self):
        dlog.LOG("DEBUG", "START")
        mavmsg = self.vehicle.message_factory.command_long_encode(
            0, 0,    # target system, target component
            mavutil.mavlink.MAV_CMD_DO_PAUSE_CONTINUE,  # command
            0,    # confirmation
            0,    # 0:Pause current mission
            0,    # Reserved
            0,    # Reserved
            0,    # Reserved
            0, 0, 0)    # param 5 ~ 7 not used
        # send command to vehicle
        self.vehicle.send_mavlink(mavmsg)
        self.set_vehicle_csts("Flt Pause")

    ### =================================================================================== 
    ### Resume
    ### =================================================================================== 
    def resume_vehicle(self):
        dlog.LOG("DEBUG", "START")
        mavmsg = self.vehicle.message_factory.command_long_encode(
            0, 0,    # target system, target component
            mavutil.mavlink.MAV_CMD_DO_PAUSE_CONTINUE,  # command
            0,    # confirmation
            1,    # 1:Continue mission
            0,    # Reserved
            0,    # Reserved
            0,    # Reserved
            0, 0, 0)    # param 5 ~ 7 not used
        # send command to vehicle
        self.vehicle.send_mavlink(mavmsg)
        self.set_vehicle_csts("Flt Resume")

    ### =================================================================================== 
    ### Brake
    ### =================================================================================== 
    def brake_vehicle(self):
        dlog.LOG("DEBUG", "RAUSE")
        mavmsg = self.vehicle.message_factory.set_position_target_local_ned_encode(
            0,       # time_boot_ms (not used)
            0, 0,    # target system, target component
            mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
            0b0000111111000111, # type_mask (only speeds enabled)
            0, 0, 0, # x, y, z positions (not used)
            0, 0, 0, # x, y, z velocity in m/s
            0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
            0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink) 
        self.vehicle.send_mavlink(mavmsg)
        self.set_vehicle_csts("Flt Brake!")
        dlog.LOG("DEBUG", "END")

    ### =================================================================================== 
    ### Yaw rotation 【ヘッディングが固定される】
    ### 機能：MAV_CMD_CONDITION_YAWメッセージを送信して、車両を指定された方位（度単位）に向けます。
    ### relative = False : 絶対角度
    ### relative = True  : 現在位置からの相対角度
    ### =================================================================================== 
    def condition_yaw_vehicle(self, heading, direction, relative=False):
        dlog.LOG("DEBUG", "START")      
        """
        デフォルトでは、車両のヨーは進行方向に従います。この機能を使用して設定した場合、デフォルトのヨー「フォロー方向」
        に戻る方法はありません。（https://github.com/diydrones/ardupilot/issues/2427）
        """
        if relative:
            # yaw relative to direction of travel
            is_relative = 1
        else:
            # yaw is an absolute angle
            is_relative = 0
        # create the CONDITION_YAW command using command_long_encode()
        mavmsg = self.vehicle.message_factory.command_long_encode(
            0, 0,           # target system, target component
            mavutil.mavlink.MAV_CMD_CONDITION_YAW, #command
            0,              # confirmation
            heading,        # param 1, yaw in degrees
            0,              # param 2, yaw speed deg/s
            direction,      # param 3, direction -1 ccw, 1 cw
            is_relative,    # param 4, relative offset 1, absolute angle 0
            0, 0, 0)        # param 5 ~ 7 not used
        # send command to vehicle
        self.vehicle.send_mavlink(mavmsg)
        dlog.LOG("DEBUG", "END")

    ### =============================================================================================
    ### End of file
    ### =============================================================================================
