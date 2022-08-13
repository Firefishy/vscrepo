#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
This program is ...
main control program for delivery drone.
Title: Drone(Coptor) control program using dronekit python
Company: Systena Corporation Inc
Autor: y.saito
Date: Aug, 2022
"""
import os
import time
import json
import dlogger as dlog
import drnctrl_cls as drnCtrl
from pymavlink import mavutil

# 接続設定をJSONファイルから取得する
base_path = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.normpath(os.path.join(base_path, '../json/setting.json'))
SETTING_JSON = json_path

### =================================================================================== 
### Main
### =================================================================================== 
if __name__ == '__main__':

    ARM_HEIGHT = 3.0
    mcmd = ""

    # Drone Control class instance
    drnc = drnCtrl.DrnCtrl()
    drnc.connect_vehicle(SETTING_JSON)
    time.sleep(3)

    try:

        # ミションクリア時に取得するデコレータ
        # @drnc.vehicle.on_message('MISSION_CLEAR_ALL')
        # def listner( self, name, message ):
        #     print(message)

        # # システムステータスを取得するデコレータ
        # @drnc.vehicle.on_message('SYS_STATUS')
        # def listner( self, name, message ):
        #     print(message)
        # # IMU情報を取得するデコレータ
        # @drnc.vehicle.on_message('RAW_IMU')
        # def listner( self, name, message ):
        #     print(message)

        # ミッション実行中デコレータ
        @drnc.vehicle.on_message('MISSION_ACK')
        def listner( self, name, message ):
            msg = "ミッション実行中:" + str(message)
            dlog.LOG("DEBUG", msg)
            print(message)

        # ミッション位置到着デコレータ
        # ウェイポイントに到着した場合にメッセージを受信
        @drnc.vehicle.on_message('MISSION_ITEM_REACHED')
        def listner( self, name, message ):
            msg = "ウェイポイントに到着:" + str(message)
            dlog.LOG("DEBUG", msg)

            # ------------------------------------------------------
            # ウェイポイント到着したらGUIDEDモードに設定
            # ------------------------------------------------------
            drnc.set_vehicle_mode("GUIDED")
            # ------------------------------------------------------
            # ウェイポイントアクションを実行
            # ------------------------------------------------------
            drnc.flg_wayPoint = True

        dlog.LOG("INFO", "Vehicle初期化完了")

        # Get attributes
        drnc.dsp_attributes()

        drnc.drone_info["status"]["dinfo"] = "Vehicle connected!"

        # dlog.LOG("DEBUG", "新規ミッションの作成（現在地用）")
        # dCtrlClass.adds_square_mission(dCtrlClass.vehicle.location.global_frame,50) 

        # Vehicleの現在モードを取得
        mode = drnc.vehicle.mode
        drnc.pub_drone_info("Vehicle connected")

        while True:
            
            # ----------------------------------------------------------------
            # MISSION START
            # ----------------------------------------------------------------
            if drnc.drone_command["operation"] == "MISSION_START":
                drnc.pub_drone_info("MISSION: Start")
                # MISSIONファイルがアップロードされている場合にMISSIONを実行
                drnc.flg_MissionUploaded = True
                dlog.LOG("DEBUG", "MISSION START")
                # Set GUIDED mode
                drnc.set_vehicle_mode("GUIDED")
                
                # アームしていない場合ARMする
                if drnc.vehicle.armed == False:
                    drnc.pub_drone_info("MISSION: Arming")
                    drnc.arm_and_takeoff(ARM_HEIGHT)
                    dlog.LOG("DEBUG", "ARMと離陸開始:" + str(ARM_HEIGHT) + 'm')
                # Checking arm status
                while drnc.vehicle.armed == False:
                    drnc.pub_drone_info("MISSION: Arm and take off")
                    dlog.LOG("DEBUG", "ARMと離陸をしています...")
                    time.sleep(1)
                dlog.LOG("INFO", "ARMと離陸完了:" + str(ARM_HEIGHT) + 'm')                

                # ミッションを実行するため、モードをAUTOにする
                drnc.set_vehicle_mode("AUTO")
                # ドローン情報をMQTTでパブリッシュ
                drnc.pub_drone_info("MISSION: AUTO mode set")

                while True:

                    nextwaypoint = drnc.vehicle.commands.next
                    #commands are zero indexed
                    if nextwaypoint>0:
                        missionitem = drnc.vehicle.commands[nextwaypoint-1] 
                        mcmd = missionitem.command

                    ###############################################
                    drnc.vehicle.groundspeed = 10 # Ground Speed is Fix (T.B.D.)
                    ###############################################

                    msg = "現在のウェイポイント: " + str(drnc.vehicle.commands.next-1) + "]です"
                    dlog.LOG("DEBUG", msg)
                    msg = '次のウェイポイント(%s)まで[ %s ]' % (nextwaypoint, drnc.distance_to_current_waypoint())
                    dlog.LOG("DEBUG", msg)
                    msg = "MISSION FLT: [ CntWP: " + str(drnc.vehicle.commands.next-1) + " --> NxtWP: " + str(nextwaypoint) + " (Dist: " + str(drnc.distance_to_current_waypoint()) + "m)]"
                    drnc.pub_drone_info(msg)

                    if mcmd==mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH or mcmd==mavutil.mavlink.MAV_CMD_NAV_LAND:
                        msg = "ミッションを終了して離陸地点へ戻る"
                        dlog.LOG("DEBUG", msg)
                        break

                    # -----------------------------------------------------------
                    # ウェイポイント到着時の処理
                    # -----------------------------------------------------------
                    if drnc.flg_wayPoint == True:
                        drnc.pub_drone_info("MISSION: WP Action")
                        dlog.LOG("DEBUG", "ウェイポイントアクションを実行")
                        drnc.condition_yaw_vehicle(30, 1, True)
                        time.sleep(1)

                    time.sleep(1)

                # ミッション終了後、離陸地点へ戻る
                drnc.pub_drone_info("MISSION: Return To Home")
                drnc.set_vehicle_mode("RTL") 
                drnc.flg_MissionUploaded = False
            time.sleep(1)

    # キーボード割り込みで終了
    except KeyboardInterrupt:
        dlog.LOG("CRITICAL","KeyBoard Exception")
        # Catch Ctrl-C
        msg = "キーボード例外処理発生"
        # スクリプトを終了する前に車両オブジェクトを閉じる
        dlog.LOG("INFO", "Close vehicle object")
        drnc.vehicle.close() 
        dlog.LOG("INFO", "プログラム終了")
        dlog.LOG("CRITICAL", msg)