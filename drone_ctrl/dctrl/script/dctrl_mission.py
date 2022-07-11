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

###
### Main function
###
if __name__ == '__main__':

    ARM_HEIGHT = 3.0

    # Get instance of DroneController(by Dronekit)
    dCtrlClass = dccls.DrnCtrl.get_instance()
    mqttClass = mqttcls.MqttCtrl.get_instance()
    print("instance1", dCtrlClass)

    dCtrlClass.connect_vehicle(SETTING_JSON)
    time.sleep(5)

    try:
        dlog.LOG("INFO", "START MQTT")
        # 接続時のコールバック関数を登録
        mqttClass.client.on_connect = mqttClass.on_connect              
        # 切断時のコールバックを登録
        mqttClass.client.on_disconnect = mqttClass.on_disconnect        
        # メッセージ送信時のコールバック
        mqttClass.client.on_publish = mqttClass.on_publish              
        # 接続先は自分自身
        mqttClass.client.connect(mqttClass.host, mqttClass.port, 60)     
        # メッセージ到着時のコールバック        
        mqttClass.client.on_message = mqttClass.on_message              

        # 通信処理スタート

        # subはloop_forever()だが，pubはloop_start()で起動だけさせる
        mqttClass.client.loop_start()                                   
        # 永久ループして待ち続ける
        #mqttClass.client.loop_forever()                                 

        # Drone init, arm and takeoff
        # Log: CRITICAL, ERROR < WARNING < INFO < DEBUG 
        dlog.LOG("INFO", "Vehicle初期化完了")

        # Get attributes
        dCtrlClass.dsp_attributes()

        # dlog.LOG("DEBUG", "新規ミッションの作成（現在地用）")
        # dCtrlClass.adds_square_mission(dCtrlClass.vehicle.location.global_frame,50)        

        # Vehicleの現在モードを取得
        mode = dCtrlClass.vehicle.mode
        
        # ガイドモードにセット
        if mode != "GUIDED":
            dCtrlClass.set_vehicle_mode("GUIDED")
            dlog.LOG("DEBUG", "GUIDEDモードに設定")
        else:
            dlog.LOG("DEBUG", "すでにGUIDEDモードです")
        
        # アーム
        if dCtrlClass.vehicle.armed == False:
            dCtrlClass.arm_and_takeoff(ARM_HEIGHT)
            dlog.LOG("DEBUG", "ARMと離陸開始:" + str(ARM_HEIGHT) + 'm')
        # アーム状態をチェック
        while dCtrlClass.vehicle.armed == False:
            dlog.LOG("DEBUG", "ARMと離陸をしています...")
            time.sleep(1)
        dlog.LOG("INFO", "ARMと離陸完了:" + str(ARM_HEIGHT) + 'm')

        # print("Starting mission")
        # # 最初の（0）ウェイポイントに設定されたミッションをリセット
        # dCtrlClass.vehicle.commands.next = 0

        import_mission_filename = 'mpmission.txt'
        export_mission_filename = 'exportedmission.txt' 

        #Upload mission from file
        dCtrlClass.upload_mission(import_mission_filename)

        # モードをAUTOに設定して、ミッションを開始する
        dCtrlClass.set_vehicle_mode("AUTO")

        count = 0
        while True:

            send_message = "Hello, Drone!" + str(count)
            count = count + 1
            dlog.LOG("DEBUG", send_message)
            mqttClass.client.publish(mqttClass.topic, send_message)    # トピック名とメッセージを決めて送信

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
            msg = "現在のウェイポイントは["+str(dCtrlClass.vehicle.commands.next)+"]です。"
            dlog.LOG("DEBUG", msg)
            time.sleep(1)

        dCtrlClass.set_vehicle_mode("RTL") 

        # スクリプトを終了する前に車両オブジェクトを閉じる
        dlog.LOG("INFO", "Close vehicle object")
        dCtrlClass.vehicle.close() 

        dlog.LOG("INFO", "プログラム終了")

    except KeyboardInterrupt:
        print("Exception")
        # Catch Ctrl-C
        msg = "キーボード例外処理発生"
        dlog.LOG("CRITICAL", msg)



