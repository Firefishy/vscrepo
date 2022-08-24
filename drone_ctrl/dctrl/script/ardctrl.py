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
import sys
import time
import threading
import json
import signal
import dlogger as dlog
import drnctrl_cls as drnCtrl
from pymavlink import mavutil

import tloganalysis as tloga

VERSION = "0.5_220823"

# 接続設定をJSONファイルから取得する
base_path = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.normpath(os.path.join(base_path, '../json/setting.json'))
SETTING_JSON = json_path

CW = 1
CCW = -1

### =================================================================================== 
### ドローンの情報をMQTTでクライアントにパブリッシュ
### =================================================================================== 
def pub_drone_info():
    while True:
        drnc.set_vehicle_info()
        # 辞書型をJSON型に変換
        json_message = json.dumps( drnc.drone_info )
        # print(drnc.drone_info["position"]["altitude"])
        drnc.client.publish(drnc.topic_drone_info, json_message )
        time.sleep(0.1)

### =================================================================================== 
### ウェイポイントアクション
### ===================================================================================
# マニュアル操作
def waypoint_action_manu(operation):
    # 回転：GUIDEDモード時のみ有効
    if operation == "ROTATE":
        rot = float(drnc.drone_command["d_alt"])
        if rot < 0:
            # CCW rotation
            dir = CCW
        else:
            # CW rotation
            dir = CW
        # Relative rotation
        drnc.condition_yaw_vehicle(abs(rot), dir, relative=True)
        drnc.drone_command["operation"] = ""

    # 特定の位置へ移動
    elif operation == "MOVE":
        dlog.LOG("DEBUG", "Goto specific xy point")
        gspx = float(drnc.drone_command["d_lat"])
        gspy = float(drnc.drone_command["d_lon"])
        gsps = float(drnc.drone_command["d_spd"])
        drnc.goto_specific_pnt(gspx, gspy, 0, gsps)
        drnc.drone_command["operation"] = ""

    # 高度変更
    elif operation == "ALT":
        dlog.LOG("DEBUG", "Goto specific z point")
        gspz = float(drnc.drone_command["d_alt"])
        gsps = float(drnc.drone_command["d_spd"])
        drnc.goto_specific_pnt(0, 0, gspz, gsps)  
        drnc.drone_command["operation"] = ""

# オート操作
def waypoint_action_auto(ope,val):
    dlog.LOG("DEBUG","START")
    if ope == "hovering":
        value = int(val)
        dlog.LOG("DEBUG", "Hover time: " + str(value))
        for i in range(value):
            time.sleep(1)
            if drnc.flg_wayPointActionPause:
                break

    elif ope == "rotate":
        angle = float(val)
        dlog.LOG("DEBUG", "RotAngle: " + str(angle))
        if angle < 0:
            # CCW rotation
            dir = CCW
        else:
            # CW rotation
            dir = CW
        # Relative rotation
        drnc.condition_yaw_vehicle(abs(angle), dir, relative=True)
    dlog.LOG("DEBUG","END")

### =================================================================================== 
### Main
### =================================================================================== 
def main():

    ARM_HEIGHT = 3.0
    mav_cmd = ""
    
    drnc.connect_vehicle(SETTING_JSON)
    time.sleep(3)

    # 機体の情報を配信するスレッド
    thread_pub_info = threading.Thread(target=pub_drone_info, daemon=True)

    # ------------------------------------------------
    # MAVLINK MESSAGE取得
    # ------------------------------------------------

    # GPS情報を取得するデコレータ
    @drnc.vehicle.on_message('GPS_RAW_INT')
    def listner( self, name, message ):
        # GPS FIX type
        drnc.gps_fix = message.fix_type
        drnc.drone_info['gps']['fixtype'] = message.fix_type
        # Visibled GPS数
        drnc.drone_info['gps']['count'] = message.satellites_visible
        #msg = "GPS_RAW_INT : " + str(message)
        #dlog.LOG("DEBUG", msg)

    # @drnc.vehicle.on_message('RAW_IMU')
    # def listner( self, name, message ):
    #     msg = "RAW_IMU: " + str(message)
    #     dlog.LOG("DEBUG", msg)

    @drnc.vehicle.on_message('ATTITUDE')
    def listner( self, name, message ):
        drnc.drone_info['attitude']['roll'] = message.roll
        drnc.drone_info['attitude']['pitch'] = message.pitch
        drnc.drone_info['attitude']['yaw'] = message.yaw
        #msg = "ATTITUDE: " + str(message)
        #dlog.LOG("DEBUG", msg)

    # グローバルポジション情報
    #@drnc.vehicle.on_message('GLOBAL_POSITION_INT')
    # def listner( self, name, message ):
    #     msg = "GLOBAL_POSITION_INT : " + str(message)
    #     dlog.LOG("DEBUG", msg)

    # サーボ出力
    @drnc.vehicle.on_message('SERVO_OUTPUT_RAW')
    def listner( self, name, message ):
        drnc.drone_info['servo']['1'] = message.servo1_raw
        drnc.drone_info['servo']['2'] = message.servo2_raw
        drnc.drone_info['servo']['3'] = message.servo3_raw
        drnc.drone_info['servo']['4'] = message.servo4_raw
        #msg = "SERVO_OUTPUT_RAW: " + str(message)
        #dlog.LOG("DEBUG", msg)

    #127 ... not published yet
    @drnc.vehicle.on_message('GPS_RTK')
    def listner( self, name, message ):
        msg = "GPS_RTK: " + str(message)
        dlog.LOG("DEBUG", msg)

    #128 ... not published yet
    @drnc.vehicle.on_message('GPS2_RTK')
    def listner( self, name, message ):
        msg = "GPS_RTK2: " + str(message)
        dlog.LOG("DEBUG", msg)

    # #141
    # @drnc.vehicle.on_message('BATTERY_STATUS')
    # def listner( self, name, message ):
    #     # Battery voltage
    #     dvolt = 0
    #     for i in range(10):
    #         dvolt += message.voltages[i] if message.voltages[i] != 65535 else 0
    #     drnc.drone_info["battery"]["voltage"] = dvolt          
    #     # Battery current
    #     drnc.drone_info["battery"]["current"] = message.current_battery            
    #     #msg = "BATTERY_STATUS: " + str(message)
    #     #dlog.LOG("DEBUG", msg)

    # #77 コマンドACK: コマンド受信に対するACK
    # コマンドが正しく送信されたかどうかのチェックに使用可能
    # 現状は特にチェックしていない
    @drnc.vehicle.on_message('COMMAND_ACK')
    def listner( self, name, message ):
        msg = "COMMAND_ACK: " + str(message)
        #dlog.LOG("DEBUG", msg)
        msg = "MAV:COMMAND_ACK: " + str(message.command) + ( (" is Accepted") if message.result==0 else " Error" )
        drnc.set_vehicle_cmsg(msg)

    # ---- for test -----------------------------------------
    @drnc.vehicle.on_message('PARAM_SET')
    def listner( self, name, message ):
        msg = "PARAM_SET: " + str(message)
        dlog.LOG("DEBUG", msg)
    # ---- for test -----------------------------------------

    # #45 ミションクリア時に取得するデコレータ
    @drnc.vehicle.on_message('MISSION_CLEAR_ALL')
    def listner( self, name, message ):
        msg = "MISSION_CLEAR_ALL受信: " + str(message)
        dlog.LOG("DEBUG", msg)

    # # システムステータスを取得するデコレータ
    # @drnc.vehicle.on_message('SYS_STATUS')
    # def listner( self, name, message ):
    #     print(message)
    # # IMU情報を取得するデコレータ
    # @drnc.vehicle.on_message('RAW_IMU')
    # def listner( self, name, message ):
    #     print(message)

    # #47 ミッションACKデコレータ
    @drnc.vehicle.on_message('MISSION_ACK')
    def listner( self, name, message ):
        # message.type : ミッションの結果
        # message.mission_type: 
        drnc.set_vehicle_cmsg("MISSION_ACK")
        msg = "MAV:MISSION_ACK: " + str(message)
        dlog.LOG("DEBUG", msg)

    # ミッション位置到着デコレータ
    # ウェイポイントに到着した場合にメッセージを受信
    @drnc.vehicle.on_message('MISSION_ITEM_REACHED')
    def listner( self, name, message ):
        drnc.set_vehicle_cmsg("MISSION_ITEM_REACHED")
        msg = "MAV:MISSION_ITEM_REACHED: " + str(message)
        dlog.LOG("DEBUG", msg)

        if drnc.vehicle.commands.next >= 1:
            # ウェイポイント到着したらGUIDEDモードに設定
            drnc.set_vehicle_mode("GUIDED")
            # ウェイポイントアクションを実行
            drnc.flg_wayPointReached = True
            drnc.wp_action_no = drnc.wp_action_no + 1
        drnc.mission_wp_count = drnc.mission_wp_count - 1

    try:
        dlog.LOG("INFO", "Vehicle初期化完了")

        # ドローン情報送信スレッドを開始
        thread_pub_info.start()

        # Get attributes
        drnc.dsp_attributes()

        drnc.set_vehicle_csts("Vehicle connected!")

        # tlog解析テスト用 T.B.D.
        # tloga.position_messages_from_tlog("mav.tlog")

        # ----------------------------------------------------------------
        # Main Loop
        # ----------------------------------------------------------------
        while True:

            if drnc.gps_fix > 1:

                drnc.wp_action_no = 0
                # ----------------------------------------------------------------
                # MISSION START
                # ----------------------------------------------------------------
                # マニュアル操作（GUIDEDモード時のみ有効）
                waypoint_action_manu(drnc.drone_command["operation"])

                if drnc.drone_command["operation"] == "MISSION_UPLOAD":
                    msg = "MISSIONをUPLOADしました WP数: " + str(drnc.mission_wp_count)
                    dlog.LOG("DEBUG", msg)
                    drnc.set_vehicle_csts(msg)
                    drnc.flg_wayPointReached = False
                
                elif drnc.drone_command["operation"] == "MISSION_START":
                    # MISSIONファイルがアップロードされている場合にMISSIONを実行
                    if drnc.flg_MissionUploaded:
                        drnc.flg_MissionDoing = True
                        dlog.LOG("DEBUG", "MISSION START")
                        # Set GUIDED mode
                        drnc.set_vehicle_mode("GUIDED")
                        
                        # アームしていない場合ARMする
                        if not drnc.vehicle.armed:
                            drnc.arm_and_takeoff(ARM_HEIGHT)
                            msg = "ARMと離陸開始:" + str(ARM_HEIGHT) + 'm'
                            dlog.LOG("DEBUG", msg)
                            drnc.set_vehicle_csts(msg)
                        # Checking arm status
                        while not drnc.vehicle.armed:
                            msg = "ARMと離陸をしています..."
                            dlog.LOG("DEBUG", msg)
                            drnc.set_vehicle_csts(msg)
                            time.sleep(1)

                        msg = "ARMと離陸完了:" + str(ARM_HEIGHT) + 'm'
                        dlog.LOG("INFO", msg)
                        drnc.set_vehicle_csts(msg)

                        # Reset mission set to first (0) waypoint
                        drnc.vehicle.commands.next=0                

                        # ミッションを実行するため、モードをAUTOにする
                        drnc.set_vehicle_mode("AUTO")

                        while True:

                            nextwaypoint = drnc.vehicle.commands.next
                            # init to MAV_CMD_NAV_WAYPOINT(16): Navigate to waypoint 
                            mav_cmd = mavutil.mavlink.MAV_CMD_NAV_WAYPOINT

                            # dlog.LOG("DEBUG", "["+str(drnc.wp_action_no)+"]です")
                            # -----------------------------------------------------------
                            # ウェイポイントアクション
                            # -----------------------------------------------------------
                            if drnc.flg_wayPointReached:
                                dlog.LOG("DEBUG", "Waypoit "+str(drnc.wp_action_no)+":"+str(drnc.wp_action[drnc.wp_action_no-1])+" action , Remain WP: " + str(drnc.mission_wp_count))
                                
                                wplen = int(len(drnc.wp_action[drnc.wp_action_no-1])/2)
                                for i in range(wplen):
                                    msg = "WPアクション" + str(i) + "開始(" + drnc.wp_action[drnc.wp_action_no-1][i*2] + "," + str(drnc.wp_action[drnc.wp_action_no-1][i*2+1]) + ")"
                                    dlog.LOG("DEBUG", msg)
                                    drnc.set_vehicle_csts(msg)
                                    waypoint_action_auto(
                                        drnc.wp_action[drnc.wp_action_no-1][i*2],
                                        drnc.wp_action[drnc.wp_action_no-1][i*2+1]
                                    )

                                    # WPアクション一時停止
                                    while drnc.flg_wayPointActionPause:
                                        drnc.set_vehicle_csts("MISSION一時停止")
                                        # WPアクション再開 or ミッション中止
                                        if drnc.flg_wayPointActionResume:
                                            drnc.set_vehicle_csts("MISSION再開")
                                            break
                                        if drnc.flg_abortMission:
                                            break
                                        time.sleep(1)
                                    drnc.flg_wayPointActionPause = False
                                    drnc.flg_wayPointActionResume = False
                                    if drnc.flg_abortMission:
                                        drnc.set_vehicle_csts("MISSION終了")
                                        break
                                    # アクションとアクションの間のインターバル（暫定）
                                    time.sleep(1)
                                
                                drnc.flg_wayPointReached = False                            
                                
                                msg = "WP(" + str(drnc.wp_action_no) + ")"
                                drnc.set_vehicle_csts(msg) 
                                if drnc.mission_wp_count == 0:
                                    drnc.flg_MissionDoing = False
                                    # 最後のWPの後にRTLが設定されていない場合ここで抜ける
                                    break
                                else:
                                    if not drnc.flg_abortMission:
                                        # 次のWPへ移動するためにAUTOモードにする
                                        drnc.set_vehicle_mode("AUTO")

                            else:

                                if nextwaypoint == 0:
                                    dlog.LOG("DEBUG", "ウェイポイント未設定")
                                    drnc.flg_MissionUploaded = False
                                else:
                                    missionitem = drnc.vehicle.commands[nextwaypoint-1] 
                                    mav_cmd = missionitem.command
                                    # WP移動速度設定
                                    drnc.vehicle.groundspeed = float(missionitem.param2)
                                    msg = "Vehicle Spped: " + str(float(missionitem.param2))
                                    dlog.LOG("DEBUG", msg)

                                msg = 'Goto WP(%s) Remain [%s(m)]' % (nextwaypoint, drnc.distance_to_current_waypoint())
                                dlog.LOG("DEBUG", msg)
                                drnc.set_vehicle_csts(msg)

                                if drnc.vehicle.commands.count == 0:
                                    dlog.LOG("DEBUG", "Count=0のためMISSION実行できません")
                                    break
                                
                                elif drnc.flg_abortMission:
                                    msg = "ミッション中断コマンドで終了"
                                    dlog.LOG("DEBUG", msg)
                                    drnc.set_vehicle_csts(msg)
                                    # 中断時はミッションをWPにする
                                    mav_cmd = mavutil.mavlink.MAV_CMD_NAV_WAYPOINT
                                    drnc.flg_wayPointReached = False
                                    break

                                # MAV_CMD_NAV_RETURN_TO_LAUNCH(20): Return to launch location
                                elif mav_cmd == mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH:
                                    msg = "ミッションを終了して離陸地点へ戻る"
                                    dlog.LOG("DEBUG", msg)
                                    drnc.set_vehicle_csts(msg)
                                    # ミッションをクリア
                                    drnc.set_vehicle_mode("RTL")
                                    break
                                
                                # MAV_CMD_NAV_LAND(21): Land at location.
                                elif mav_cmd == mavutil.mavlink.MAV_CMD_NAV_LAND:
                                    msg = "ミッションを終了して現在位置へLANDする"
                                    dlog.LOG("DEBUG", msg)
                                    drnc.set_vehicle_csts(msg)
                                    # ミッションをクリア
                                    drnc.set_vehicle_mode("LAND")
                                    break

                                elif drnc.mission_wp_count <= 0:
                                    msg = "ミッション完了で終了"
                                    dlog.LOG("DEBUG", msg)
                                    drnc.set_vehicle_csts(msg)
                                    break
                        
                            time.sleep(0.5)
                        
                        dlog.LOG("DEBUG", "ミッション動作を終了")
                        drnc.wp_action_no = 0
                        drnc.flg_MissionDoing = False
                        drnc.set_vehicle_csts("MISSION END")
                        # ミッションをクリア
                        drnc.clear_mission_all()
                        drnc.mission_wp_count = 0
                        drnc.flg_MissionUploaded = False
                        drnc.flg_abortMission = False

                    else:
                        msg = "Mission is not uploaded"
                        drnc.set_vehicle_csts(msg)
                        dlog.LOG("DEBUG", msg)
                
            else:
                dlog.LOG("DEBUG", "GPS NO FIX ... ")

            time.sleep(1)

    # キーボード割り込みで終了
    except KeyboardInterrupt:
        # Catch Ctrl-C
        dlog.LOG("CRITICAL","KeyBoard Exception")
        msg = "キーボード例外処理発生"
        # スクリプトを終了する前に機体オブジェクトを閉じる
        dlog.LOG("INFO", "Close vehicle object")
        drnc.vehicle.close() 
        dlog.LOG("INFO", "プログラム終了")
        dlog.LOG("CRITICAL", msg)

if __name__ == '__main__':
  
    args = sys.argv
    if len(args) == 1:
        # Drone Control class instance
        drnc = drnCtrl.DrnCtrl()
        main()
    elif args[1] == '-v':
        print("---------------------------------------")
        print("Drone control program ver." + VERSION)
        print("---------------------------------------")
    else:
        print("Invalid argument")