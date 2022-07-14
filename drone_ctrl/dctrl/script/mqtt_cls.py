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
    # Published topic
    topic_dstate = "drone/frame"
    # Subscribed topic
    topic_dinfo = "drone/dinfo"
    client = ""
    msg = ""

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
        client.subscribe(self.topic_dinfo)  # subするトピックを設定 

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
        print("Received message '" 
            + str(msg.payload) 
            + "' on topic '" 
            + msg.topic 
            + "' with QoS " 
            + str(msg.qos)
        )
        
    ### =================================================================================== 
    ### topicをpublish
    ### =================================================================================== 
    def publish_topic(self, topic):
        self.client.publish(topic)

