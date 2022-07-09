#!usr/bin/env python
# -*- coding: utf-8 -*-
print( "dronekitスタート" )    # 開始メッセージ

# 必要なライブラリをインポート
from kbhit import *                 # kbhitを使うために必要(同じフォルダにkbhit.pyを置くこと)
from subprocess import Popen        # subprocessの中から、Popenをインポート
from signal import signal, SIGINT   # Ctrl+C(SIGINT)の送出のために必要 
from dronekit import connect        # connectを使いたいのでインポート
from dronekit import VehicleMode    # VehicleModeも使いたいのでインポート
import time                         # ウェイト関数time.sleepを使うために必要

# kbhit()を使うための「おまじない」を最初に２つ書く
atexit.register(set_normal_term)
set_curses_term()

# dronekit SITL の起動情報
# example: 'dronekit-sitl copter --home=35.079624,136.905453,50.0,3.0 --instance 0'
sitl_frame          = 'copter'          # rover, plane, copterなどのビークルタイプ
sitl_home_latitude  = '35.894087'       # 緯度(度)  柏の葉キャンパス駅前ロータリー
sitl_home_longitude = '139.952447'      # 経度(度)
sitl_home_altitude  = '17.0'            # 高度(m)
sitl_home_direction = '0.0'             # 機首方位(度)
sitl_instance_num   = 0                 # 0〜

# コマンドライン入力したい文字列をリスト形式で作成
sitl_boot_list = ['dronekit-sitl',sitl_frame,
                  '--home=%s,%s,%s,%s' % (sitl_home_latitude,sitl_home_longitude,sitl_home_altitude,sitl_home_direction),
                  '--instance=%s'%(sitl_instance_num)]

print '# sitl command: ', sitl_boot_list        # 文字列を表示
p = Popen(sitl_boot_list)   # サブプロセスの起動
time.sleep(1)   # 起動完了のために1秒待つ

#connection_stringの生成
connection_string = 'tcp:localhost:' + str(5760 + int(sitl_instance_num) * 10 ) # インスタンスが増えるとポート番号が10増える

# フライトコントローラ(FC)へ接続
print( "FCへ接続: %s" % (connection_string) )    # 接続設定文字列を表示
vehicle = connect(connection_string, wait_ready=True)    # 接続

#Ctrl+cが押されるまでループ
try:
    while True:
        if kbhit():     # 何かキーが押されるのを待つ
            key = getch()   # 1文字取得

            # keyの中身に応じて分岐
            if key=='g':                # guided
                vehicle.mode = VehicleMode( 'GUIDED' )
            elif key=='l':              # land
                vehicle.mode = VehicleMode( 'LAND' )


        # ここはif文と同じインデントなので，キーに関係なく1秒に1回実行される
        # 現在の状態を表示
        print("--------------------------" )
        print(" System status: %s" % vehicle.system_status.state)
        print(" Is Armable?: %s" % vehicle.is_armable)
        print(" Armed: %s" % vehicle.armed) 
        print(" Mode: %s" % vehicle.mode.name )
        print(" Global Location: %s" % vehicle.location.global_frame)
        time.sleep(1)

except( KeyboardInterrupt, SystemExit):    # Ctrl+cが押されたら離脱
    print( "SIGINTを検知" )

# フライトコントローラとの接続を閉じる
vehicle.close()

 # サブプロセスにもSIGINT送信
p.send_signal(SIGINT)
p.communicate()
time.sleep(1)   # 終了完了のために1秒待つ

print("終了．")    # 終了メッセージ