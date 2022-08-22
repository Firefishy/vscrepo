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

from decimal import Decimal, ROUND_HALF_UP
import numpy as np

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
    ### Yaw rotation
    ### 機能：MAV_CMD_CONDITION_YAWメッセージを送信して、車両を指定された方位（度単位）に向けます。
    ### relative = False : 絶対角度
    ### relative = True  : 現在位置からの相対角度
    ### =================================================================================== 
    def condition_yaw_vehicle(self, heading, direction, relative=False):
        dlog.LOG("DEBUG", "START")
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

    ### =================================================================================== 
    ### Fly to specific position by using local_ned coordination
    ### 機能：SET_POSITION_TARGET_LOCAL_NED コマンドを送信し、北・東・下フレームの
    ### 指定位置に飛行する
    ### =================================================================================== 
    def goto_position_target_local_ned(self, north, east, down):
        dlog.LOG("DEBUG", "START")
        msg = self.vehicle.message_factory.set_position_target_local_ned_encode(
            0,       # time_boot_ms (not used)
            0, 0,    # target system, target component
            mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
            0b0000111111111000, # type_mask (only positions enabled)
            north, east, down, # x, y, z positions (or North, East, Down in the MAV_FRAME_BODY_NED frame
            0, 0, 0, # x, y, z velocity in m/s  (not used)
            0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
            0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink) 
        # send command to vehicle
        self.vehicle.send_mavlink(msg)
        dlog.LOG("DEBUG", "END")

    ### =============================================================================================
    ### 座標変換
    ### =============================================================================================
    def coord_trans(self, ori_x, ori_y, deg):
        dlog.LOG("DEBUG", "START")
        rot_x = (ori_x * np.cos(np.deg2rad(deg))) - (ori_y * np.sin(np.deg2rad(deg)))
        rot_y = (ori_x * np.sin(np.deg2rad(deg))) + (ori_y * np.cos(np.deg2rad(deg)))
        msgstr = "Deg=" + str(deg) + ',from x=' + str(ori_x) + ",y=" + str(ori_y) + ",to x=" + str(rot_x) + ",y=" + str(rot_y)
        dlog.LOG("DEBUG", msgstr)
        dlog.LOG("DEBUG", "END")      
        return rot_x, rot_y

    ### =================================================================================== 
    ### 【Heading】Vehicle移動メソッド 前後左右上下方向へ移動
    ### 進行方向にHeadingして飛行します。
    ### 機能：速度ベクトルと実行回数（期間）によって車両を方向に移動します。
    ### =================================================================================== 
    def send_ned_velocity_heading(self, 
        vx, # X方向速度 
        vy, # Y方向速度
        vz, # Z方向速度
        duration    # 実行回数（期間）
    ):
        dlog.LOG("INFO", "START")
        msgstr = ""
        try:
            """
            AC3.3以降、メッセージは1秒ごとに再送信される必要があることに注意してください（約3秒後）
            メッセージがない場合、速度はゼロに戻ります）。 AC3.2.1以前では、指定された
            速度はキャンセルされるまで持続します。以下のコードはどちらのバージョンでも機能するはずです
            （メッセージを複数回送信しても問題は発生しません）。
        
            type_mask（0 =有効、1 =無視）については、上記のリンクを参照してください。
            執筆時点では、加速ビットとヨービットは無視されます。
            """
            mavmsg = self.vehicle.message_factory.set_position_target_local_ned_encode(
                0,       # time_boot_ms (not used)
                0, 0,    # target system, target component
                mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
                # bit 1024 is heading enable bit, 0 is disable
                0b0000111111000111, # type_mask (only speeds enabled)
                0, 0, 0, # x, y, z positions (not used)
                vx, vy, vz, # x, y, z velocity in m/s
                0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
                90, 10)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink) 

            # send command to vehicle on 1 Hz cycle
            for i in range(0,duration):
                # 目標物までの実距離を取得
                msgstr = "move velocity (m/s)["+"{:.3f}".format(vx) + "/{:.3f}".format(vy) + "/{:.3f}".format(vz)+"]で移動中 <" + str(i) + "/" + str(duration) + " 回目>"
                dlog.LOG("INFO", msgstr)
                self.vehicle.send_mavlink(mavmsg)
                self.set_vehicle_csts(msgstr)
                self.set_vehicle_info()
                time.sleep(1)

            dlog.LOG("INFO", "移動終了")
            dlog.LOG("DEBUG", "MOVE END")
        except:
            #ex = traceback.format_exc()
            #msgstr = "Exception: " + ex
            dlog.LOG("WARNING", msgstr)            
        dlog.LOG("INFO", "END")

    ### =================================================================================== 
    ### Vehicle移動メソッド
    ### 機能：Vehicleを特定のポイントへ移動させる
    ### 説明：各ステップのラッパーメソッドから呼ばれる
    ### =================================================================================== 
    def goto_specific_pnt(self, move_x, move_y, move_z, gspeed):
        dlog.LOG("INFO", "START")
        rot_x, rot_y = self.coord_trans(move_x, move_y, self.vehicle.heading)
        msgstr = "-------------------------" \
                + "\r\n        x:" + str(rot_x) \
                + "\r\n        y:" + str(rot_y) \
                + "\r\n        z:" + str(move_z) \
                + "\r\n   gspeed:" + str(gspeed) \
                + "\r\n-------------------------"
        dlog.LOG("INFO", msgstr)

        # ---------------------------------------------------
        # HEADING
        # ---------------------------------------------------
        dlog.LOG("INFO", "MOVE Heading Start")
        if gspeed == 0:
            dur_rnd = 0
            vx = 0
            vy = 0
            vz = 0
        else:
            if move_z == 0:
                dur = math.sqrt( rot_x**2 + rot_y**2 )/gspeed
                dur_rnd = int(Decimal(str(dur)).quantize(Decimal('0'), rounding=ROUND_HALF_UP))
                if dur_rnd == 0:
                    vx = 0
                    vy = 0
                    vz = 0
                else:
                    vx = rot_x / dur_rnd
                    vy = rot_y / dur_rnd
                    vz = 0

            else:
                move_z = move_z * (1/gspeed)
                dur_rnd = int(Decimal(str(abs(move_z))).quantize(Decimal('0'), rounding=ROUND_HALF_UP))
                vx = 0
                vy = 0
                if dur_rnd == 0:
                    vz = 0
                else:
                    vz = ( gspeed * move_z / dur_rnd ) * -1

        heading = round(np.rad2deg(math.atan(rot_y/rot_x)),3) if rot_x != 0 else 0.0
        if (rot_x < 0) and (rot_y > 0):
            heading += 180
        elif (rot_x > 0) and (rot_y < 0):
            heading += 360
        elif (rot_x < 0) and (rot_y < 0):
            heading += 180

        msgstr = "-------------------------" \
                + "\r\n        vx:" + str(vx) \
                + "\r\n        vy:" + str(vy) \
                + "\r\n        vz:" + str(vz) \
                + "\r\n  duration:" + str(dur_rnd) \
                + "\r\n   heading:" + str(heading) \
                + "\r\n    gspeed:" + str(gspeed) \
                + "\r\n-------------------------"
        dlog.LOG("INFO", msgstr)
        # Heading for moving direction
        self.send_ned_velocity_heading(vx, vy, vz, dur_rnd)
        self.send_ned_velocity_heading(0, 0, 0, 1)
        dlog.LOG("INFO", "END")

    ### =============================================================================================
    ### End of file
    ### =============================================================================================
