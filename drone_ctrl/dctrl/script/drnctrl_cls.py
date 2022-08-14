#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
^----^
 *  * 
This program is ...
Drone control program for specific drone.
Title: The part of MQTT data transfer and drone control program on dronekit python
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

#from http import client
import time
import paho.mqtt.client as mqtt     # MQTTのライブラリをインポート
#from time import sleep              # 3秒間のウェイトのために使う
import dlogger as dlog
import json
#from dronekit import Command
import os
import ardctrl_cls_c2 as ardctrl

ARM_HEIGHT = 3.0

##################################################################
### Class as singleton
##################################################################
# class Dctrl_Singleton(object):
#     @classmethod
#     def get_instance(cls):
#         if not hasattr(cls, "_instance"):
#             cls._instance = cls()
#         #    cls._instance = cls(input)
#         # else:
#         #     cls._instance.input = input
#         return cls._instance

##################################################################
### Drone control class
##################################################################
#class MqttCtrl(Mqtt_Singleton):
class DrnCtrl(ardctrl.ArdCtrlClsC2):

    host = "localhost"
    port = 1883
    # Publisher 座標等のドローン情報
    topic_drone_info = "drone/dinfo"
    # Subscriber コマンド、Simple Goto
    topic_drone_command = "drone/dctrl"
    # Subscriber ミッション
    topic_drone_mission_test = "drone/mission"
    # Subscriber ミッション: マップ制御画面対応用
    topic_drone_mission = "ctrl/001"

    # ミッションファイルをアップロードした場合にTrue、ミッション実行後False
    flg_MissionUploaded = False
    # ミッションでWayPointに到着した場合にTrue
    flg_wayPoint = False

    # info pub / command sub
    client = ""
    # mission sub
    client_mission_test = ""
    # mission sub
    client_mission = ""
    #msg = ""

    mission_wp_count = 0

    ### =================================================================================== 
    ### MQTTで受信するドローン操作コマンド:クライアントから受信
    ###     コマンドおよび移動先の「緯度、経度、高度」情報
    ### =================================================================================== 
    drone_command = {
        "operation":"None",
        "subcode":"None",
        "d_lat":"0",
        "d_lon":"0",
        "d_alt":"0",
        "d_spd":"5"
    }

    drone_mission_command = {
        "IsChanged": "false",
        "command": "None",
        "d_lat": "0",
        "d_lon": "0",
        "d_alt": "0",
        "d_spd": "0"
    }

    drone_mission = {
        "operation":"None",
        "index":"0",
        "cntwp":"0",
        "frame":"0",
        "command":"0",
        "para1":"0",
        "para2":"0",
        "para3":"0",
        "para4":"0",
        "d_lat":"0",
        "d_lon":"0",
        "d_alt":"0",
        "acnt":"0"
    }   

    ### =================================================================================== 
    ### コンストラクタ
    ### =================================================================================== 
    def __init__(self):
        dlog.LOG("INFO", "START")
        self.vehicle = ardctrl.ArdCtrlClsC2.vehicle

        # クラスのインスタンス(実体)の作成
        self.client = mqtt.Client() 
        self.client_mission_test = mqtt.Client() 
        self.client_mission = mqtt.Client()

        # 接続時のコールバック関数を登録
        self.client.on_connect = self.on_connect              
        self.client_mission_test.on_connect = self.on_connect_mission_test           
        self.client_mission.on_connect = self.on_connect_mission

        # 切断時のコールバックを登録
        self.client.on_disconnect = self.on_disconnect        
        self.client_mission_test.on_disconnect = self.on_disconnect_mission_test       
        self.client_mission.on_disconnect = self.on_disconnect_mission

        #self.client.on_publish = self.on_publish              
        #self.client_mission_test.on_publish = self.on_publish_m              
        #self.client_mission.on_publish = self.on_publish_m
        #           
        # 接続先は自分自身
        self.client.connect(self.host, self.port, 60)     
        self.client_mission_test.connect(self.host, self.port, 60)     
        self.client_mission.connect(self.host, self.port, 60)

        # メッセージ到着時のコールバック        
        self.client.on_message = self.on_message
        self.client_mission_test.on_message = self.on_message_mission_test
        self.client_mission.on_message = self.on_message_mission

        # subはloop_forever()だが，pubはloop_start()で起動だけさせる
        self.client.loop_start()                                   
        self.client_mission_test.loop_start()                                   
        self.client_mission.loop_start()

        # 永久ループして待ち続ける
        #mqttClass.client.loop_forever()
        #mqttClass.client_mission_test.loop_forever()
        #mqttClass.client_mission.loop_forever()

    ### =================================================================================== 
    ### ブローカーに接続できたときの処理：コールバック
    ### =================================================================================== 
    def on_connect(self, client, userdata, flag, rc):
        dlog.LOG("DEBUG", "Connected with result code " + str(rc))  
        # subscribeトピックを設定
        client.subscribe(self.topic_drone_command)  

    def on_connect_mission_test(self, client_mission_test, userdata, flag, rc):
        dlog.LOG("DEBUG", "Connected with result code " + str(rc))  
        # subscribeトピックを設定
        client_mission_test.subscribe(self.topic_drone_mission_test)  

    def on_connect_mission(self, client_mission, userdata, flag, rc):
        dlog.LOG("DEBUG", "Connected with result code " + str(rc))  
        # subscribeトピックを設定
        client_mission.subscribe(self.topic_drone_mission)  

    ### =================================================================================== 
    ### ブローカーから切断されたときの処理：コールバック
    ### =================================================================================== 
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            dlog.LOG("DEBUG", "Unexpected disconnection.")

    def on_disconnect_mission_test(self, client_mission_test, userdata, rc):
        if rc != 0:
            dlog.LOG("DEBUG", "Unexpected disconnection.")

    def on_disconnect_mission(self, client_mission, userdata, rc):
        if rc != 0:
            dlog.LOG("DEBUG", "Unexpected disconnection.")

    ### =================================================================================== 
    ### publishが完了したときの処理：コールバック
    ### =================================================================================== 
    # def on_publish(self, client, userdata, mid):
    #     dlog.LOG("DEBUG", "publish: {0}".format(mid))

    # def on_publish_m(self, client, userdata, mid):
    #     dlog.LOG("DEBUG", "publish: {0}".format(mid))
        
    ### =================================================================================== 
    ### ドローン動作コマンドサブスクライバコールバック
    ### =================================================================================== 
    def on_message(self, client, userdata, msg):
        dlog.LOG("DEBUG","START")
        # msg.topicにトピック名が，msg.payloadに届いたデータ本体が入っている
        recvData = json.loads(msg.payload)
        
        if msg.topic==self.topic_drone_command:

            # 受信メッセージをコマンド辞書にコピー、その際に変更フラグを付加
            # 届いた際にtrueにし，コマンドを処理したらfalseにする
            self.drone_command["operation"] = recvData["operation"]

            if self.drone_command["operation"] == "MISSION_UPLOAD":
                self.drone_info["status"]["dinfo"] = self.drone_command["operation"]
                # MISSION実行中のミッションファイルのアップロードは禁止
                if self.flg_MissionUploaded == False:
                # MISSIONのUPLOAD
                    if self.flg_MissionUploaded == False:
                        # 最初の（0）ウェイポイントに設定されたミッションをリセット

                        self.vehicle.commands.next = 0

                        # ジオフェンスファイル名
                        # import_fence_filename = '../mission/polygon_fence.txt'

                        # ジオフェンスデータをファイルからドローンへアップロード : T.B.D.
                        # self.upload_fence(import_fence_filename) 
                        
                        # ミッションファイル名
                        import_mission_filename = '../mission/mpmission.txt'
                        # エクスポートファイル名
                        # export_mission_filename = '../mission/exportedmission.txt'

                        # ミッションデータをファイルからドローンへアップロード
                        self.upload_mission(import_mission_filename)
                        #self.flg_MissionUploaded = True
                    #self.drone_command["operation"] = "NONE"

            elif self.drone_command["operation"] == "ARM":
                self.drone_info["status"]["dinfo"] = self.drone_command["operation"]
                # ARMしていない場合
                if self.vehicle.armed == False:
                    # ARMの場合GUIDEDにしてARMする
                    dlog.LOG("DEBUG", "GUided and Arm the drone")
                    self.set_vehicle_mode("GUIDED")
                    self.vehicle_arming()
                    self.drone_command["operation"] = "NONE"

            else:
                # ARMしている場合
                if self.vehicle.armed == True:

                    dlog.LOG("DEBUG", self.drone_command["operation"])
                    if self.drone_command["operation"] == "MAV_MESSAGE":
                        self.drone_info["status"]["dinfo"] = self.drone_command["operation"]
                        self.get_custom_message(self.drone_command["subcode"])

                    # DISARM
                    elif self.drone_command["operation"] == "DISARM":
                        self.vehicle_disarming()
                    # TAKE OFF
                    elif self.drone_command["operation"] == "TAKEOFF":
                        self.vehicle_takeoff(20.0)

                    # PAUSE
                    elif self.drone_command["operation"] == "MISSION_PAUSE":
                        self.pause_vehicle()
                    # RESUME
                    elif self.drone_command["operation"] == "MISSION_RESUME":
                        self.resume_vehicle()

                    # ROTATION
                    elif self.drone_command["operation"] == "ROTATION":
                        self.condition_yaw_vehicle(45, 1, True)

                    # ---- Simple GOTO ----
                    elif self.drone_command["operation"] == "GOTO":
                        self.drone_info["status"]["dinfo"] = self.drone_command["operation"]
                        self.drone_command["d_lat"] = recvData["d_lat"]
                        self.drone_command["d_lon"] = recvData["d_lon"]
                        self.drone_command["d_alt"] = recvData["d_alt"]
                        self.drone_command["d_spd"] = recvData["d_spd"]

                        # ガイドモードにセット
                        self.set_vehicle_mode("GUIDED")

                        # アームしていない場合ARMする
                        if self.vehicle.armed == False:
                            self.arm_and_takeoff(ARM_HEIGHT)
                            dlog.LOG("DEBUG", "ARMと離陸開始:" + str(ARM_HEIGHT) + 'm')
                        # アーム状態をチェック
                        while self.vehicle.armed == False:
                            dlog.LOG("DEBUG", "ARMと離陸をしています...")
                            time.sleep(1)
                        dlog.LOG("INFO", "GOTO: ARMと離陸完了:" + str(ARM_HEIGHT) + 'm')
                        self.vehicle_goto(self.drone_command)
                    
                    elif self.drone_command["operation"] == "MISSION_CLEAR":
                        self.drone_info["status"]["dinfo"] = "MISSION CLEAR ALL"
                        self.clear_mission_all()

                    # Drone mode set / MISSION start
                    else:
                        # AUTOモードに設定した場合はウェイポイントフラグをクリアする
                        if self.drone_command["operation"] == "AUTO":
                            self.flg_wayPoint = False

                        # Deone mode set: MISSION_STARTはモードでは無いため除外する
                        if self.drone_command["operation"] != "MISSION_START":
                            self.set_vehicle_mode(self.drone_command["operation"])                

    ### =================================================================================== 
    ### Missionコマンドサブスクライバコールバック
    ### =================================================================================== 
    def on_message_mission_test(self, client, userdata, msg):
        dlog.LOG("DEBUG","START")

        path = '../mission/mpmission.txt'
        f = open(path, 'w')
        #f.write(self.drone_mission2["sfx"]) # これは送られていない、要チェック！
        f.write('QGC WPL 110'+'\r\n')

        # msg.topicにトピック名が，msg.payloadに届いたデータ本体が入っている
        recvData = json.loads(msg.payload)
        dlog.LOG("DEBUG", "Mission data size: " + str(len(recvData)))
        
        # ミッションデータをファイルに保存
        if msg.topic==self.topic_drone_mission_test:
          for num in range(len(recvData)):
            print(str(recvData[num]))
            #dlog.LOG("DEBUG", "MissionData: " + str(recvData[num]))
            f.write(recvData[num])
        # MISSIONのWP数を保存（WP0はカウントしない）    
        self.mission_wp_count = len(recvData) - 1
        f.close()        
        self.drone_mission["operation"] = "MISSION_UPLOAD"
        dlog.LOG("DEBUG","END")

    ### =================================================================================== 
    ### 本番マップ用Missionコマンドサブスクライバコールバック
    ### =================================================================================== 
    def on_message_mission(self, client, userdata, msg):
        dlog.LOG("DEBUG","START")

        path = '../mission/mpmission_new.txt'
        f = open(path, 'w')
        #f.write(self.drone_mission2["sfx"]) # これは送られていない、要チェック！
        f.write('QGC WPL 110'+'\r\n')

        # msg.topicにトピック名が，msg.payloadに届いたデータ本体が入っている
        recvData = json.loads(msg.payload)

        # 受信メッセージをコマンド辞書にコピー、その際に変更フラグを付加
        # 届いた際にtrueにし，コマンドを処理したらfalseにする
        self.drone_mission_command["IsChanged"] = "true"
        self.drone_mission_command["IsChanged"] = "true"
        self.drone_mission_command["command"] = recvData["command"]

        if self.drone_mission_command["command"] == "MISSION_UPLOAD":
            wp_num = int(recvData["WP_num"])
            print(wp_num)
            for i in range(wp_num):
                tmp_wp = "WP_data" + str(i)
                missionData = str(i) + '\t' \
                            + '0' + '\t' + '3' + '\t' + '16' + '\t' \
                            + '0' + '\t' + '0' + '\t' + '0' + '\t' + '0' + '\t' \
                            + recvData[tmp_wp]["lat"] + '\t' \
                            + recvData[tmp_wp]["lon"] + '\t' \
                            + recvData[tmp_wp]["alt"]+ '\t' \
                            + '1' + '\r\n';                
                # ミッションデータをファイルに保存
                f.write(missionData)
            self.drone_mission["operation"] = "MISSION_START"
        f.close()        
        dlog.LOG("DEBUG","END")

