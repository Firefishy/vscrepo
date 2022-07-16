#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
//////////////////////////////////////////////////////////////////////////////////////////
 ^----^
  *  * 
   ~
//////////////////////////////////////////////////////////////////////////////////////////
"""

from http import client
import paho.mqtt.client as mqtt     # MQTTのライブラリをインポート
from time import sleep              # 3秒間のウェイトのために使う
import dlogger as dlog
import json

##################################################################
### Class as singleton
##################################################################
class Mqtt_Singleton(object):
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
class MqttCtrl(Mqtt_Singleton):

    host = "localhost"
    port = 1883
    # Publisher 座標等のドローン情報
    topic_dinfo = "drone/dinfo"
    # Subscriber コマンド、ミッションデータ
    topic_dctrl = "drone/dctrl"
    client = ""
    msg = ""

    #== MQTTで受信するコマンドのベースになる辞書 ================
    drone_command = {
        "IsChanged":"false",
        "command":"None",
        "d_lat":"0",
        "d_lon":"0",
        "d_alt":"0"
    }    

    ### =================================================================================== 
    ### コンストラクタ
    ### =================================================================================== 
    def __init__(self):
        dlog.LOG("INFO", "START")
        # クラスのインスタンス(実体)の作成
        self.client = mqtt.Client() 
        # 接続時のコールバック関数を登録
        self.client.on_connect = self.on_connect              
        # 切断時のコールバックを登録
        self.client.on_disconnect = self.on_disconnect        
        # メッセージ送信時のコールバック
        self.client.on_publish = self.on_publish              
        # 接続先は自分自身
        self.client.connect(self.host, self.port, 60)     
        # メッセージ到着時のコールバック        
        self.client.on_message = self.on_message
        # subはloop_forever()だが，pubはloop_start()で起動だけさせる
        self.client.loop_start()                                   
        # 永久ループして待ち続ける
        #mqttClass.client.loop_forever()

    ### =================================================================================== 
    ### ブローカーに接続できたときの処理：コールバック
    ### =================================================================================== 
    def on_connect(self, client, userdata, flag, rc):
        print("Connected with result code " + str(rc))  # 接続できた旨表示
        client.subscribe(self.topic_dctrl)  # subするトピックを設定 

    ### =================================================================================== 
    ### ブローカーから切断されたときの処理：コールバック
    ### =================================================================================== 
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print("Unexpected disconnection.")

    ### =================================================================================== 
    ### publishが完了したときの処理：コールバック
    ### =================================================================================== 
    def on_publish(self, client, userdata, mid):
        print("publish: {0}".format(mid))

    ### =================================================================================== 
    ### メッセージが届いたときの処理：コールバック
    ### =================================================================================== 
    def on_message(self, client, userdata, msg):
        # msg.topicにトピック名が，msg.payloadに届いたデータ本体が入っている
        recv_command = json.loads(msg.payload)

        # 受信メッセージをコマンド辞書にコピー、その際に変更フラグを付加
        # 届いた際にtrueにし，コマンドを処理したらfalseにする
        self.drone_command["IsChanged"] = "true"     
        self.drone_command["command"] = recv_command["command"]

        if self.drone_command["command"] == "GOTO":
            self.drone_command["d_lat"] = recv_command["d_lat"]
            self.drone_command["d_lon"] = recv_command["d_lon"]
            self.drone_command["d_alt"] = recv_command["d_alt"]

        print("Received message '" 
            + self.drone_command["command"] + "/"
            + str(self.drone_command["d_lat"]) + "/"
            + str(self.drone_command["d_lon"]) + "/"
            + str(self.drone_command["d_alt"]) 
        )
        
    ### =================================================================================== 
    ### topicをpublish
    ### =================================================================================== 
    def publish_topic(self, topic):
        self.client.publish(topic)

