#!usr/bin/env python
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
import time
import json                         # json.dumps関数を使いたいのでインポート

import dctrl_cls as dccls
import mqtt_cls as mqttcls
import dlogger as dlog

from pymavlink import mavutil

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

### =================================================================================== 
### ドローンの情報をクライアントにパブリッシュ
### =================================================================================== 
def pub_drone_info():
    dCtrlClass.set_vehicle_info()
    #--- MQTTの送信 ---
    # 辞書型をJSON型に変換
    json_message = json.dumps( dCtrlClass.drone_info )     
    #dlog.LOG("DEBUG", json_message)
    # トピック名は以前と同じ"drone/001"
    mqttClass.client.publish(mqttClass.topic_dinfo, json_message )

### =================================================================================== 
### Main function
### =================================================================================== 
if __name__ == '__main__':

    ARM_HEIGHT = 3.0

    # Get instance of DroneController(by Dronekit)
    dCtrlClass = dccls.DrnCtrl.get_instance()
    # MQTT通信処理スタート
    mqttClass = mqttcls.MqttCtrl.get_instance()
    #print("instance1", dCtrlClass)

    dCtrlClass.connect_vehicle(SETTING_JSON)
    time.sleep(5)

    try:

        # Drone init, arm and takeoff
        # Log: CRITICAL, ERROR < WARNING < INFO < DEBUG 
        dlog.LOG("INFO", "Vehicle初期化完了")

        # Get attributes
        dCtrlClass.dsp_attributes()

        # dlog.LOG("DEBUG", "新規ミッションの作成（現在地用）")
        # dCtrlClass.adds_square_mission(dCtrlClass.vehicle.location.global_frame,50)        

        # Vehicleの現在モードを取得
        mode = dCtrlClass.vehicle.mode
        pub_drone_info()

        while True:
            # ---------------------------
            # Drone command   
            # ---------------------------
            # Drone mode 
            if mqttClass.drone_command["operation"] == "GUIDED":
                dlog.LOG("DEBUG", "Set mode to GUIDED")
                dCtrlClass.set_vehicle_mode("GUIDED")
                mqttClass.drone_command["operation"] = "NONE"
            elif mqttClass.drone_command["operation"] == "AUTO":
                dlog.LOG("DEBUG", "Set mode to AUTO")
                dCtrlClass.set_vehicle_mode("AUTO")
                mqttClass.drone_command["operation"] = "NONE"
            elif mqttClass.drone_command["operation"] == "RTL":
                dlog.LOG("DEBUG", "Set mode to AUTO")
                dCtrlClass.set_vehicle_mode("RTL")
                mqttClass.drone_command["operation"] = "NONE"
            
            # Arm
            elif mqttClass.drone_command["operation"] == "ARM":
                dlog.LOG("DEBUG", "Arming moter")
                dCtrlClass.vehicle_arming()
                mqttClass.drone_command["operation"] = "NONE"
            # DisArm
            elif mqttClass.drone_command["operation"] == "DISARM":
                dlog.LOG("DEBUG", "DIsarming moter")
                dCtrlClass.vehicle_disarming()
                mqttClass.drone_command["operation"] = "NONE"

            # Take off
            elif mqttClass.drone_command["operation"] == "TAKEOFF":
                dlog.LOG("DEBUG", "Take off")
                dCtrlClass.vehicle_takeoff(20.0)
                mqttClass.drone_command["operation"] = "NONE"

            # Land
            elif mqttClass.drone_command["operation"] == "LAND":
                dlog.LOG("DEBUG", "Landing")
                dCtrlClass.set_vehicle_mode("LAND")
                mqttClass.drone_command["operation"] = "NONE"

            # Simple GOTO
            elif mqttClass.drone_command["operation"] == "GOTO":
                dlog.LOG("DEBUG", "Simple GOTO")

                # ガイドモードにセット
                dCtrlClass.set_vehicle_mode("GUIDED")
                pub_drone_info()

                # アームしていない場合ARMする
                if dCtrlClass.vehicle.armed == False:
                    pub_drone_info()
                    dCtrlClass.arm_and_takeoff(ARM_HEIGHT)
                    dlog.LOG("DEBUG", "ARMと離陸開始:" + str(ARM_HEIGHT) + 'm')
                # アーム状態をチェック
                while dCtrlClass.vehicle.armed == False:
                    pub_drone_info()
                    dlog.LOG("DEBUG", "ARMと離陸をしています...")
                    time.sleep(1)
                dlog.LOG("INFO", "ARMと離陸完了:" + str(ARM_HEIGHT) + 'm')    

                dCtrlClass.vehicle_goto(mqttClass.drone_command)
                mqttClass.drone_command["operation"] = "NONE"

            # ---------------------------
            # Drone mission   
            # ---------------------------
            # Mission
            if mqttClass.drone_mission["operation"] == "MISSION":
                dlog.LOG("DEBUG", "MISSION")
                mqttClass.drone_mission["operation"] = "NONE"

                # print("Starting mission")
                # # 最初の（0）ウェイポイントに設定されたミッションをリセット
                dCtrlClass.vehicle.commands.next = 0

                # # ジオフェンスファイル名
                import_fence_filename = '../mission/polygon_fence.txt'

                # # ジオフェンスデータをファイルからドローンへアップロード
                #dCtrlClass.upload_fence(import_fence_filename) 
                
                # ミッションファイル名
                import_mission_filename = '../mission/mpmission.txt'
                # エクスポートファイル名
                export_mission_filename = '../mission/exportedmission.txt'

                # ミッションデータをファイルからドローンへアップロード
                dCtrlClass.upload_mission(import_mission_filename)

                # ガイドモードにセット
                dCtrlClass.set_vehicle_mode("GUIDED")
                pub_drone_info()
                
                # アームしていない場合ARMする
                if dCtrlClass.vehicle.armed == False:
                    pub_drone_info()
                    dCtrlClass.arm_and_takeoff(ARM_HEIGHT)
                    dlog.LOG("DEBUG", "ARMと離陸開始:" + str(ARM_HEIGHT) + 'm')
                # アーム状態をチェック
                while dCtrlClass.vehicle.armed == False:
                    pub_drone_info()
                    dlog.LOG("DEBUG", "ARMと離陸をしています...")
                    time.sleep(1)
                dlog.LOG("INFO", "ARMと離陸完了:" + str(ARM_HEIGHT) + 'm')                

                # ミッションを実行するため、モードをAUTOにする
                dCtrlClass.set_vehicle_mode("AUTO")
                pub_drone_info()

                # ミッションを実行
                while True:
                    pub_drone_info()
                    nextwaypoint=dCtrlClass.vehicle.commands.next
                    missionitem=dCtrlClass.vehicle.commands[nextwaypoint-1] #commands are zero indexed
                    mcmd = missionitem.command

                    msg = 'ウェイポイントまでの距離 (%s): %s' % (nextwaypoint, dCtrlClass.distance_to_current_waypoint())
                    dlog.LOG("DEBUG", msg)

                    if mcmd==mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH or mcmd==mavutil.mavlink.MAV_CMD_NAV_LAND:
                        msg = "ミッションを終了して離陸地点へ戻る"
                        dlog.LOG("DEBUG", msg)
                        break;
                
                    # if nextwaypoint == 3: # 次のウェイポイントへスキップ
                    #     msg = 'ウェイポイント3に到達したらウェイポイント5へスキップする'
                    #     dlog.LOG("DEBUG", msg)
                    #     #dCtrlClass.vehicle.commands.next = 5
                    # if nextwaypoint == 5: # ダミーウェイポイント - ウェイポイント4に到達するとすぐにこれが真となり、終了します。
                    #     msg = "最終目的地に向かう際、「標準」ミッションを終了する (5)"
                    #     dlog.LOG("DEBUG", msg)
                    #     break;
                    msg = "現在のウェイポイントは["+str(dCtrlClass.vehicle.commands.next)+"]です。[Head:" + str(dCtrlClass.vehicle.heading) + "]"
                    dlog.LOG("DEBUG", msg)
                    time.sleep(1)

                # ミッション終了後、離陸地点へ戻る
                dCtrlClass.set_vehicle_mode("RTL") 
            pub_drone_info()
            time.sleep(1)

    # キーボード割り込みで終了
    except KeyboardInterrupt:
        dlog.LOG("CRITICAL","KeyBoard Exception")
        # Catch Ctrl-C
        msg = "キーボード例外処理発生"
        # スクリプトを終了する前に車両オブジェクトを閉じる
        dlog.LOG("INFO", "Close vehicle object")
        dCtrlClass.vehicle.close() 
        dlog.LOG("INFO", "プログラム終了")
        dlog.LOG("CRITICAL", msg)