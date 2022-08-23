#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
^----^
 *  * 
This program is ...
Drone control program for specific drone.
Title: The part of drone(Coptor) control program using dronekit python
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
from __future__ import print_function
import math
import time
import json
from dronekit import connect, VehicleMode, LocationGlobal, LocationGlobalRelative, Command
from pymavlink import mavutil
import dlogger as dlog
import ardctrl_cls_c1 as ardctrl

##################################################################
### Ardupilot drone flight control command class
##################################################################
class ArdCtrlClsC2(ardctrl.ArdCtrlClsC1):

    def __init__(self):
        dlog.LOG("INFO", "ard_control_class(2) init")
        self.vehicle = ardctrl.ArdCtrlClsC1.vehicle

    ### =================================================================================== 
    ### SimpleGoto
    ### =================================================================================== 
    def vehicle_goto(self, cmd):            
        dlog.LOG("DEBUG","START")
        point = LocationGlobalRelative(
            float(cmd["d_lat"]), 
            float(cmd["d_lon"]), 
            float(cmd["d_alt"]) 
        )
        dlog.LOG("DEBUG", cmd["d_spd"])
        self.set_vehicle_csts("Simple Goto")
        self.vehicle.simple_goto(point, groundspeed=float(cmd["d_spd"]))

    ### =============================================================================================
    ### 指定した「original_location」からの 「LocationGlobal」を応答する。
    ### (高度はoriginal_locationと同じ)
    ### ---------------------------------------------------------------------------------------------
    ### この関数は、現在の機体位置から相対的な位置を指定して機体を移動させたい場合に便利です。
    ### このアルゴリズムは、電柱の近くを除けば、小さな距離 (1km 以内なら 10m) で比較的正確です。
    ### 詳細は以下を参照。
    ### http://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
    ### =============================================================================================
    def get_location_metres(self,original_location, dNorth, dEast):
        dlog.LOG("DEBUG","START")
        #Radius of "spherical" earth
        earth_radius=6378137.0 
        #Coordinate offsets in radians
        dLat = dNorth/earth_radius
        dLon = dEast/(earth_radius*math.cos(math.pi*original_location.lat/180))

        #New position in decimal degrees
        newlat = original_location.lat + (dLat * 180/math.pi)
        newlon = original_location.lon + (dLon * 180/math.pi)
        dlog.LOG("DEBUG","END")
        return LocationGlobal(newlat, newlon,original_location.alt)

    ### =============================================================================================
    ### 2 つの LocationGlobal オブジェクト間の地上距離をメートル単位で返します。
    ###    このメソッドは近似値であり、長距離や地球の極の近くでは正確ではありません。
    ###    これはArduPilotのテストコードに由来しています。
    ###    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    ### =============================================================================================
    def get_distance_metres(self, aLocation1, aLocation2):
        dlog.LOG("DEBUG","START")
        dlat = aLocation2.lat - aLocation1.lat
        dlong = aLocation2.lon - aLocation1.lon
        dlog.LOG("DEBUG","END")
        return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5

    ### =============================================================================================
    ### 現在のウェイポイントまでの距離をメートル単位で取得します。 
    ### 最初のウェイポイント（原点）に対しては、Noneを返します。
    ### =============================================================================================
    def distance_to_current_waypoint(self):
        dlog.LOG("DEBUG","START")
        nextwaypoint = self.vehicle.commands.next
        if nextwaypoint == 0:
            return None
        missionitem=self.vehicle.commands[nextwaypoint-1] #commands are zero indexed
        lat = missionitem.x
        lon = missionitem.y
        alt = missionitem.z
        targetWaypointLocation = LocationGlobalRelative(lat,lon,alt)
        distancetopoint = self.get_distance_metres(self.vehicle.location.global_frame, targetWaypointLocation)
        distancetopoint = round(distancetopoint,2)
        dlog.LOG("DEBUG","END")
        return distancetopoint

    ### =============================================================================================
    ### Download mission data from vehicle
    ### =============================================================================================
    def download_mission(self):
        dlog.LOG("DEBUG","START")
        cmds = self.vehicle.commands
        cmds.download()
        cmds.wait_ready() # wait until download is complete.
        dlog.LOG("DEBUG","END")
    
    ### =============================================================================================
    ### 現在のミッションに離陸コマンドと4つのウェイポイントコマンドを追加する。
    ###        ウェイポイントは、指定されたLocationGlobal (aLocation)を中心に、辺の長さ2*aSizeの正方形を
    ###    形成するように配置される。
    ###    この関数は、vehicle.commandsが機体のミッションの状態と一致すると仮定しています。
    ###    (セッション中、ミッションをクリアした後に少なくとも一度はdownloadを呼び出す必要があります)    
    ### =============================================================================================
    def adds_square_mission(self, aLocation, aSize):
        dlog.LOG("DEBUG","START")
        cmds = self.vehicle.commands
        dlog.LOG("DEBUG"," Clear any existing commands")
        cmds.clear() 
        dlog.LOG("DEBUG"," Define/add new commands.")
        # 新しいコマンドを追加します。パラメータの意味/順序はCommandクラスに記載されています。
        # MAV_CMD_NAV_TAKEOFF コマンドを追加しました。すでに空中にいる場合は無視されます。
        cmds.add(
            Command
            ( 
                0, 
                0, 
                0, 
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # グローバル（WGS84）座標フレーム+ホームポジションを基準とした高度。最初の値/x：緯度、2番目の値/ y：経度、3番目の値/ z：正の高度。0はホームポジションの高度です。
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,            # 地面/手からの離陸
                0, 0, 0, 0, 0, 0, 0, 0, 
                10
            )
        )

        # MAV_CMD_NAV_WAYPOINT を4 箇所定義し、コマンドを追加します。
        point1 = self.get_location_metres(aLocation, aSize, -aSize)
        point2 = self.get_location_metres(aLocation, aSize, aSize)
        point3 = self.get_location_metres(aLocation, -aSize, aSize)
        point4 = self.get_location_metres(aLocation, -aSize, -aSize)

        """
        https://mavlink.io/en/messages/common.html#enums
        ミッションメッセージ

        """

        cmds.add(
            Command( 
                0,                                              # Target System ID
                0,                                              # Target Component ID
                0,                                              # Waypoint ID
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # frame: グローバル（WGS84）座標フレーム+ホームポジションを基準とした高度。最初の値/x：緯度、2番目の値/ y：経度、3番目の値/ z：正の高度。0はホームポジションの高度です。
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,           # command: ウェイポイントへの移動 
                0,                                              # current: false=0, true=1
                0,                                              # autocontinue to next waypoint 
                0,                                              # param1:
                0,                                              # param2:
                0,                                              # param3:
                0,                                              # param4:
                point1.lat,                                     # 緯度(ローカル:x(m)x10^4, グローバル:緯度x10^7)
                point1.lon,                                     # 経度(ローカル:y(m)x10^4, グローバル:経度x10^7)
                11                                              # 高度(m) 相対、絶対
            )
        )
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point2.lat, point2.lon, 12))
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point3.lat, point3.lon, 13))
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point4.lat, point4.lon, 14))
        
        # 4地点にダミーのウェイポイント "5 "を追加（目的地に到着したことを知ることができる）
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point4.lat, point4.lon, 14))    

        msg = " Upload new commands to vehicle"
        dlog.LOG("DEBUG", msg)
        cmds.upload()
        dlog.LOG("DEBUG","END")

    ### =============================================================================================
    ### ファイルからリストにミッションを読み込む。
    ### ミッションの定義は、Waypointファイル
    ### 形式(http://qgroundcontrol.org/mavlink/waypoint_protocol#waypoint_file_format)です。
    ### この関数は、upload_mission()で使用される。    
    ### =============================================================================================
    def readmission(self, aFileName):
        dlog.LOG("DEBUG","START")
        msgstr = "Reading mission from file: %s" % aFileName
        dlog.LOG("DEBUG", msgstr)
        missionlist=[]
        with open(aFileName) as f:
            for i, line in enumerate(f):
                if i==0:
                    if not line.startswith('QGC WPL 110'):
                        raise Exception('File is not supported WP version')
                else:
                    linearray=line.split('\t')
                    #ln_index=int(linearray[0])                  # INDEX: 0,1,2..　--> Don't use
                    ln_currentwp=int(linearray[1])              # CURRENT WP　--> Don't use
                    ln_frame=int(linearray[2])                  # COORD FRAME　--> [5]
                    ln_command=int(linearray[3])                # COMMAND --> [4]
                    ln_param1=float(linearray[4])               # PARAM1 --> [7]
                    ln_param2=float(linearray[5])               # PARAM2 --> [8]
                    ln_param3=float(linearray[6])               # PARAM3 --> [9]
                    ln_param4=float(linearray[7])               # PARAM4 --> [10]
                    ln_param5=float(linearray[8])               # PARAM5/LATITUDE --> [11]
                    ln_param6=float(linearray[9])               # PARAM6/LONGITUDE --> [12]
                    ln_param7=float(linearray[10])              # PARAM7/ALTITUDE --> [13]
                    ln_autocontinue=int(linearray[11].strip())  # AUTOCONTINUE --> [6]
                    mission_cmd = Command(
                        0,
                        0,
                        0,
                        ln_frame,
                        ln_command,
                        ln_currentwp,
                        ln_autocontinue,
                        ln_param1,
                        ln_param2,
                        ln_param3, 
                        ln_param4, 
                        ln_param5,
                        ln_param6,
                        ln_param7
                    )
                    missionlist.append(mission_cmd)
        f.close()
        dlog.LOG("DEBUG","END")
        return missionlist

    ### =============================================================================================
    ### 現在のミッションをダウンロードし、リストで返します。
    ### =============================================================================================
    def download_mission(self, ):
        dlog.LOG("DEBUG","START")
        """        
        save_mission() で、保存するファイル情報を取得するために使用される。
        """
        #print(" Download mission from vehicle")
        missionlist=[]
        cmds = self.vehicle.commands
        cmds.download()
        cmds.wait_ready()
        for cmd in cmds:
            missionlist.append(cmd)
        dlog.LOG("DEBUG","END")
        return missionlist

    ### =============================================================================================
    ### ファイルからミッションデータをアップロードする。
    ### =============================================================================================
    def upload_mission(self, aFileName):
        dlog.LOG("DEBUG","START")
        mission_count = 0
        #Read mission from file
        missionlist = self.readmission(aFileName)
        
        #print("\nUpload mission from a file: %s" % aFileName)
        #Clear existing mission from vehicle
        #print(' Clear mission')
        cmds = self.vehicle.commands
        cmds.clear()
        #Add new mission to vehicle
        dlog.LOG("DEBG","Mission upload")
        for command in missionlist:
            dlog.LOG("DEBG", str(command))
            cmds.add(command)
            mission_count = mission_count + 1
        cmds.upload()
        dlog.LOG("DEBUG","END")
        return mission_count

    ### =============================================================================================
    ### Save a mission in the Waypoint file format 
    ### (http://qgroundcontrol.org/mavlink/waypoint_protocol#waypoint_file_format).
    ### =============================================================================================
    def save_mission(self, aFileName):
        dlog.LOG("DEBUG","START")
        #Download mission from vehicle
        missionlist = self.download_mission()
        #Add file-format information
        output='QGC WPL 110\n'
        #Add home location as 0th waypoint
        home = self.vehicle.home_location
        output+="%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (0,1,0,16,0,0,0,0,home.lat,home.lon,home.alt,1)
        #Add commands
        for cmd in missionlist:
            commandline="%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (cmd.seq,cmd.current,cmd.frame,cmd.command,cmd.param1,cmd.param2,cmd.param3,cmd.param4,cmd.x,cmd.y,cmd.z,cmd.autocontinue)
            output+=commandline
        with open(aFileName, 'w') as file_:
            file_.write(output)
        dlog.LOG("DEBUG","END")
            
    ### =============================================================================================
    ### アップロードしたミッションをクリア
    ### =============================================================================================
    def clear_mission_all(self):
        dlog.LOG("DEBUG","START")
        cmds = self.vehicle.commands
        cmds.clear()
        cmds.upload()

    ### =============================================================================================
    ### Print a mission file to demonstrate "round trip"
    ### =============================================================================================
    def printfile(self, aFileName):
        dlog.LOG("DEBUG","START")
        #print("\nMission file: %s" % aFileName)
        with open(aFileName) as f:
            for line in f:
                print(' %s' % line.strip())     
        dlog.LOG("DEBUG","END")

    ### #############################################################################################

    ### =============================================================================================
    ### ### T.B.D ###
    ### Add square fence to vehicle
    ### =============================================================================================
    def adds_square_fence(self, aLocation, aSize):
        dlog.LOG("DEBUG","START")
        cmds = self.vehicle.commands
        cmds.clear() 
        # 新しいコマンドを追加します。パラメータの意味/順序はCommandクラスに記載されています。
        # MAV_CMD_NAV_TAKEOFF コマンドを追加しました。すでに空中にいる場合は無視されます。
        cmds.add(
            Command
            ( 
                4, 
                0, 
                0, 
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # グローバル（WGS84）座標フレーム+ホームポジションを基準とした高度。最初の値/x：緯度、2番目の値/ y：経度、3番目の値/ z：正の高度。0はホームポジションの高度です。
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,            # 地面/手からの離陸
                0, 0, 0, 0, 0, 0, 0, 0, 
                10
            )
        )

        # MAV_CMD_NAV_WAYPOINT を4 箇所定義し、コマンドを追加します。
        point1 = self.get_location_metres(aLocation, aSize, -aSize)
        point2 = self.get_location_metres(aLocation, aSize, aSize)
        point3 = self.get_location_metres(aLocation, -aSize, aSize)
        point4 = self.get_location_metres(aLocation, -aSize, -aSize)

        """
        https://mavlink.io/en/messages/common.html#enums
        ミッションメッセージ

        """

        cmds.add(
            Command( 
                0,                                              # Target System ID
                0,                                              # Target Component ID
                0,                                              # Waypoint ID
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # frame: グローバル（WGS84）座標フレーム+ホームポジションを基準とした高度。最初の値/x：緯度、2番目の値/ y：経度、3番目の値/ z：正の高度。0はホームポジションの高度です。
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,           # command: ウェイポイントへの移動 
                0,                                              # current: false=0, true=1
                0,                                              # autocontinue to next waypoint 
                0,                                              # param1:
                0,                                              # param2:
                0,                                              # param3:
                0,                                              # param4:
                point1.lat,                                     # 緯度(ローカル:x(m)x10^4, グローバル:緯度x10^7)
                point1.lon,                                     # 経度(ローカル:y(m)x10^4, グローバル:経度x10^7)
                11                                              # 高度(m) 相対、絶対
            )
        )
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point2.lat, point2.lon, 12))
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point3.lat, point3.lon, 13))
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point4.lat, point4.lon, 14))
        
        # 4地点にダミーのウェイポイント "5 "を追加（目的地に到着したことを知ることができる）
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point4.lat, point4.lon, 14))    

        cmds.upload()
        dlog.LOG("DEBUG","END")

    ### =============================================================================================
    ### ### T.B.D ###
    ### ファイルからジオフェンスデータをアップロードする。
    ### Refer: https://github.com/dronekit/dronekit-python/issues/1092
    ### =============================================================================================
    def upload_fence(self, aFileName):
        dlog.LOG("DEBUG","START")
        #Read mission from file
        missionlist = self.readmission(aFileName)
        
        #print("\nUpload fence from a file: %s" % aFileName)
        # Clear existing mission from vehicle
        # print(' Clear mission')
        cmds = self.vehicle.commands
        #cmds.clear()
        #Add new mission to vehicle
        for command in missionlist:
            # Missionの場合0のため、1に書き換える必要がある。
            command.mission_type = 1
            cmds.add(command)
        #self.vehicle.commands.upload()
        cmds.upload_fence()
        dlog.LOG("DEBUG","END")

    ### =============================================================================================
    ### End of file
    ### =============================================================================================