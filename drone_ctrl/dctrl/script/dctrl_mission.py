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
    dlog.LOG("DEBUG", json_message)
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
    print("instance1", dCtrlClass)

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
               
            # Drone mode 
            if mqttClass.drone_command["command"] == "GUIDED":
                dlog.LOG("DEBUG", "Set mode to GUIDED")
                dCtrlClass.set_vehicle_mode("GUIDED")
                mqttClass.drone_command["command"] = "NONE"
            elif mqttClass.drone_command["command"] == "AUTO":
                dlog.LOG("DEBUG", "Set mode to AUTO")
                dCtrlClass.set_vehicle_mode("AUTO")
                mqttClass.drone_command["command"] = "NONE"
            elif mqttClass.drone_command["command"] == "RTL":
                dlog.LOG("DEBUG", "Set mode to AUTO")
                dCtrlClass.set_vehicle_mode("RTL")
                mqttClass.drone_command["command"] = "NONE"
            
            # Arm
            elif mqttClass.drone_command["command"] == "ARM":
                dlog.LOG("DEBUG", "Arming moter")
                dCtrlClass.vehicle_arming()
                mqttClass.drone_command["command"] = "NONE"
            # DisArm
            elif mqttClass.drone_command["command"] == "DISARM":
                dlog.LOG("DEBUG", "DIsarming moter")
                dCtrlClass.vehicle_disarming()
                mqttClass.drone_command["command"] = "NONE"

            # Take off
            elif mqttClass.drone_command["command"] == "TAKEOFF":
                dlog.LOG("DEBUG", "Take off")
                dCtrlClass.vehicle_takeoff(20.0)
                mqttClass.drone_command["command"] = "NONE"

            # Land
            elif mqttClass.drone_command["command"] == "LAND":
                dlog.LOG("DEBUG", "Landing")
                dCtrlClass.set_vehicle_mode("LAND")
                mqttClass.drone_command["command"] = "NONE"

            # Simple GOTO
            elif mqttClass.drone_command["command"] == "GOTO":
                dlog.LOG("DEBUG", "Simple GOTO")
                dCtrlClass.vehicle_goto(mqttClass.drone_command)
                mqttClass.drone_command["command"] = "NONE"

            # Mission
            elif mqttClass.drone_command["command"] == "MISSION":
                dlog.LOG("DEBUG", "MISSION")
                mqttClass.drone_command["command"] = "NONE"

                # print("Starting mission")
                # # 最初の（0）ウェイポイントに設定されたミッションをリセット
                # dCtrlClass.vehicle.commands.next = 0

                import_mission_filename = '../mission/mpmission.txt'
                export_mission_filename = '../mission/exportedmission.txt' 

                #Upload mission from file
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

                # AUTOモードに設定して、ミッションを開始する
                dCtrlClass.set_vehicle_mode("AUTO")
                pub_drone_info()

                count = 0
                while True:
                    pub_drone_info()
                    nextwaypoint=dCtrlClass.vehicle.commands.next
                    msg = 'Distance to waypoint (%s): %s' % (nextwaypoint, dCtrlClass.distance_to_current_waypoint())
                    dlog.LOG("DEBUG", msg)
                
                    if nextwaypoint == 3: # 次のウェイポイントへスキップ
                        msg = 'ウェイポイント3に到達したらウェイポイント5へスキップする'
                        dlog.LOG("DEBUG", msg)
                        #dCtrlClass.vehicle.commands.next = 5
                    if nextwaypoint == 5: # ダミーウェイポイント - ウェイポイント4に到達するとすぐにこれが真となり、終了します。
                        msg = "最終目的地に向かう際、「標準」ミッションを終了する (5)"
                        dlog.LOG("DEBUG", msg)
                        break;
                    msg = "現在のウェイポイントは["+str(dCtrlClass.vehicle.commands.next)+"]です。[Head:" + str(dCtrlClass.vehicle.heading) + "]"
                    dlog.LOG("DEBUG", msg)
                    time.sleep(1)

                dCtrlClass.set_vehicle_mode("RTL") 
            pub_drone_info()
            time.sleep(1)
        
        # スクリプトを終了する前に車両オブジェクトを閉じる
        dlog.LOG("INFO", "Close vehicle object")

        dCtrlClass.vehicle.close() 

        dlog.LOG("INFO", "プログラム終了")

    except KeyboardInterrupt:
        print("Exception")
        # Catch Ctrl-C
        msg = "キーボード例外処理発生"
        dlog.LOG("CRITICAL", msg)



