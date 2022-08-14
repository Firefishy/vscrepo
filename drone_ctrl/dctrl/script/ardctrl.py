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
import threading
import json
import signal
import dlogger as dlog
import drnctrl_cls as drnCtrl
from pymavlink import mavutil

# 接続設定をJSONファイルから取得する
base_path = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.normpath(os.path.join(base_path, '../json/setting.json'))
SETTING_JSON = json_path

### =================================================================================== 
### ドローンの情報をMQTTでクライアントにパブリッシュ
### =================================================================================== 
def pub_drone_info():
    while True:
        drnc.set_vehicle_info()
        # 辞書型をJSON型に変換
        json_message = json.dumps( drnc.drone_info )
        drnc.client.publish(drnc.topic_drone_info, json_message )
        time.sleep(1)

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

    thread_pub_info = threading.Thread(target=pub_drone_info, daemon=True)

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
            drnc.mission_wp_count = drnc.mission_wp_count - 1

        dlog.LOG("INFO", "Vehicle初期化完了")

        # ドローン情報送信スレッドを開始
        thread_pub_info.start()

        # Get attributes
        drnc.dsp_attributes()

        drnc.set_vehicle_csts("Vehicle connected!")

        while True:

            
            
            # ----------------------------------------------------------------
            # MISSION START
            # ----------------------------------------------------------------
            if drnc.drone_command["operation"] == "MISSION_UPLOAD":
                dlog.LOG("DEBUG", "Got WP count = " + str(drnc.mission_wp_count))
            elif drnc.drone_command["operation"] == "MISSION_START":
                # MISSIONファイルがアップロードされている場合にMISSIONを実行
                drnc.flg_MissionUploaded = True
                dlog.LOG("DEBUG", "MISSION START")
                # Set GUIDED mode
                drnc.set_vehicle_mode("GUIDED")
                
                # アームしていない場合ARMする
                if drnc.vehicle.armed == False:
                    drnc.arm_and_takeoff(ARM_HEIGHT)
                    dlog.LOG("DEBUG", "ARMと離陸開始:" + str(ARM_HEIGHT) + 'm')
                # Checking arm status
                while drnc.vehicle.armed == False:
                    dlog.LOG("DEBUG", "ARMと離陸をしています...")
                    time.sleep(1)
                dlog.LOG("INFO", "ARMと離陸完了:" + str(ARM_HEIGHT) + 'm')                

                # ミッションを実行するため、モードをAUTOにする
                drnc.set_vehicle_mode("AUTO")
                # ドローン情報をMQTTでパブリッシュ

                while True:

                    nextwaypoint = drnc.vehicle.commands.next
                    #print("nextwaypoint="+str(nextwaypoint))
                    #print(str(drnc.mission_wp_count))
                    #commands are zero indexed
                    if nextwaypoint>0:
                        missionitem = drnc.vehicle.commands[nextwaypoint-1] 
                        mcmd = missionitem.command

                    ###############################################
                    drnc.vehicle.groundspeed = 10 # Ground Speed is Fix (T.B.D.)
                    ###############################################

                    msg = 'Next WP(%s) --> [ %s m]' % (nextwaypoint, drnc.distance_to_current_waypoint())
                    dlog.LOG("DEBUG", msg)
                    drnc.set_vehicle_csts(msg)
                    if mcmd == mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH:
                        msg = "ミッションを終了して離陸地点へ戻る"
                        dlog.LOG("DEBUG", msg)
                        # ミッションをクリア
                        drnc.clear_mission_all()
                        drnc.set_vehicle_mode("RTL")
                        break
                    elif mcmd == mavutil.mavlink.MAV_CMD_NAV_LAND:
                        msg = "ミッションを終了して現在位置へLANDする"
                        dlog.LOG("DEBUG", msg)
                        # ミッションをクリア
                        drnc.clear_mission_all()
                        drnc.set_vehicle_mode("LAND")
                        break

                    if drnc.mission_wp_count <= 0:
                        drnc.clear_mission_all()
                        break
                    # -----------------------------------------------------------
                    # ウェイポイント到着時の処理
                    # -----------------------------------------------------------
                    if drnc.flg_wayPoint == True:
                        dlog.LOG("DEBUG", "ウェイポイントアクションを実行")
                        drnc.set_vehicle_csts("WP Action")
                        drnc.condition_yaw_vehicle(30, 1, True)
                        time.sleep(1)
                    
                    #print( "WP count = " + str(drnc.mission_wp_count))
                    time.sleep(1)
                
                dlog.LOG("DEBUG", "ミッションを終了しました")
                drnc.set_vehicle_csts("MISSION END")
                # ミッションをクリア
                drnc.clear_mission_all()
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