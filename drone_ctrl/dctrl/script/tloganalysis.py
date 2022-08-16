#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
tlog解析プログラム (T.B.D.)

"""
from __future__ import print_function

from dronekit import connect, Command, VehicleMode, LocationGlobalRelative
from pymavlink import mavutil
import json, urllib, math
import time

import fnmatch

# events from EV messages, taken from AP_Logger.h
events = {
    7 : "DATA_AP_STATE",
    8 : "DATA_SYSTEM_TIME_SET",
    9 : "DATA_INIT_SIMPLE_BEARING",
    10 : "DATA_ARMED",
    11 : "DATA_DISARMED",
    15 : "DATA_AUTO_ARMED",
    17 : "DATA_LAND_COMPLETE_MAYBE",
    18 : "DATA_LAND_COMPLETE",
    28 : "DATA_NOT_LANDED",
    19 : "DATA_LOST_GPS",
    21 : "DATA_FLIP_START",
    22 : "DATA_FLIP_END",
    25 : "DATA_SET_HOME",
    26 : "DATA_SET_SIMPLE_ON",
    27 : "DATA_SET_SIMPLE_OFF",
    29 : "DATA_SET_SUPERSIMPLE_ON",
    30 : "DATA_AUTOTUNE_INITIALISED",
    31 : "DATA_AUTOTUNE_OFF",
    32 : "DATA_AUTOTUNE_RESTART",
    33 : "DATA_AUTOTUNE_SUCCESS",
    34 : "DATA_AUTOTUNE_FAILED",
    35 : "DATA_AUTOTUNE_REACHED_LIMIT",
    36 : "DATA_AUTOTUNE_PILOT_TESTING",
    37 : "DATA_AUTOTUNE_SAVEDGAINS",
    38 : "DATA_SAVE_TRIM",
    39 : "DATA_SAVEWP_ADD_WP",
    41 : "DATA_FENCE_ENABLE",
    42 : "DATA_FENCE_DISABLE",
    43 : "DATA_ACRO_TRAINER_DISABLED",
    44 : "DATA_ACRO_TRAINER_LEVELING",
    45 : "DATA_ACRO_TRAINER_LIMITED",
    46 : "DATA_GRIPPER_GRAB",
    47 : "DATA_GRIPPER_RELEASE",
    49 : "DATA_PARACHUTE_DISABLED",
    50 : "DATA_PARACHUTE_ENABLED",
    51 : "DATA_PARACHUTE_RELEASED",
    52 : "DATA_LANDING_GEAR_DEPLOYED",
    53 : "DATA_LANDING_GEAR_RETRACTED",
    54 : "DATA_MOTORS_EMERGENCY_STOPPED",
    55 : "DATA_MOTORS_EMERGENCY_STOP_CLEARED",
    56 : "DATA_MOTORS_INTERLOCK_DISABLED",
    57 : "DATA_MOTORS_INTERLOCK_ENABLED",
    58 : "DATA_ROTOR_RUNUP_COMPLETE",
    59 : "DATA_ROTOR_SPEED_BELOW_CRITICAL",
    60 : "DATA_EKF_ALT_RESET",
    61 : "DATA_LAND_CANCELLED_BY_PILOT",
    62 : "DATA_EKF_YAW_RESET",
    63 : "DATA_AVOIDANCE_ADSB_ENABLE",
    64 : "DATA_AVOIDANCE_ADSB_DISABLE",
    65 : "DATA_AVOIDANCE_PROXIMITY_ENABLE",
    66 : "DATA_AVOIDANCE_PROXIMITY_DISABLE",
    67 : "DATA_GPS_PRIMARY_CHANGED",
    68 : "DATA_WINCH_RELAXED",
    69 : "DATA_WINCH_LENGTH_CONTROL",
    70 : "DATA_WINCH_RATE_CONTROL",
    71 : "DATA_ZIGZAG_STORE_A",
    72 : "DATA_ZIGZAG_STORE_B",
    73 : "DATA_LAND_REPO_ACTIVE",

    80 : "FENCE_FLOOR_ENABLE",
    81 : "FENCE_FLOOR_DISABLE",

    163 : "DATA_SURFACED",
    164 : "DATA_NOT_SURFACED",
    165 : "DATA_BOTTOMED",
    166 : "DATA_NOT_BOTTOMED",
}

subsystems = {
    1 : "MAIN",
    2 : "RADIO",
    3 : "COMPASS",
    4 : "OPTFLOW",
    5 : "FAILSAFE_RADIO",
    6 : "FAILSAFE_BATT",
    7 : "FAILSAFE_GPS",
    8 : "FAILSAFE_GCS",
    9 : "FAILSAFE_FENCE",
    10 : "FLIGHT_MODE",
    11 : "GPS",
    12 : "CRASH_CHECK",
    13 : "FLIP",
    14 : "AUTOTUNE",
    15 : "PARACHUTES",
    16 : "EKFCHECK",
    17 : "FAILSAFE_EKFINAV",
    18 : "BARO",
    19 : "CPU",
    20 : "FAILSAFE_ADSB",
    21 : "TERRAIN",
    22 : "NAVIGATION",
    23 : "FAILSAFE_TERRAIN",
    24 : "EKF_PRIMARY",
    25 : "THRUST_LOSS_CHECK",
    26 : "FAILSAFE_SENSORS",
    27 : "FAILSAFE_LEAK",
    28 : "PILOT_INPUT",
    29 : "FAILSAFE_VIBE",
}

error_codes = { # not used yet
    "ERROR_RESOLVED" : 0,
    "FAILED_TO_INITIALISE" : 1,
    "UNHEALTHY" : 4,
    # subsystem specific error codes -- radio
    "RADIO_LATE_FRAME" : 2,
    # subsystem specific error codes -- failsafe_thr, batt, gps
    "FAILSAFE_RESOLVED" : 0,
    "FAILSAFE_OCCURRED" : 1,
    # subsystem specific error codes -- main
    "MAIN_INS_DELAY" : 1,
    # subsystem specific error codes -- crash checker
    "CRASH_CHECK_CRASH" : 1,
    "CRASH_CHECK_LOSS_OF_CONTROL" : 2,
    # subsystem specific error codes -- flip
    "FLIP_ABANDONED" : 2,
    # subsystem specific error codes -- terrain
    "MISSING_TERRAIN_DATA" : 2,
    # subsystem specific error codes -- navigation
    "FAILED_TO_SET_DESTINATION" : 2,
    "RESTARTED_RTL" : 3,
    "FAILED_CIRCLE_INIT" : 4,
    "DEST_OUTSIDE_FENCE" : 5,
    # parachute failed to deploy because of low altitude or landed
    "PARACHUTE_TOO_LOW" : 2,
    "PARACHUTE_LANDED" : 3,
    # EKF check definitions
    "EKFCHECK_BAD_VARIANCE" : 2,
    "EKFCHECK_VARIANCE_CLEARED" : 0,
    # Baro specific error codes
    "BARO_GLITCH" : 2,
    "BAD_DEPTH" : 3,
    # GPS specific error coces
    "GPS_GLITCH" : 2,
}

def timestring(msg):
    '''return string for msg timestamp'''
    ts_ms = int(msg._timestamp * 1000.0) % 1000
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg._timestamp)) + ".%.03u" % ts_ms


def get_distance_metres(aLocation1, aLocation2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.

    This method is an approximation, and will not be accurate over large distances and close to the 
    earth's poles. It comes from the ArduPilot test code: 
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5


def position_messages_from_tlog(filename):
    """
    Given telemetry log, get a series of wpts approximating the previous flight
    """

    # Pull out just the global position msgs
    messages = []
    mlog = mavutil.mavlink_connection(filename)
    
    # nvert = False
    # wildcard = filename
    # invert = False

    # # Pull out just the global position msgs
    # messages = []
    # mlog = mavutil.mavlink_connection(filename)

    # #mestate.mlog.rewind()
    # types = set(['MSG','EV','ERR', 'STATUSTEXT'])
    # while True:
    #     m = mlog.recv_match(type=types)
    #     if m is None:
    #         break
    #     if m.get_type() == 'MSG':
    #         mstr = m.Message
    #     elif m.get_type() == 'EV':
    #         mstr = "Event: %s" % events.get(m.Id, str(m.Id))
    #     elif m.get_type() == 'ERR':
    #         mstr = "Error: Subsys %s ECode %u " % (subsystems.get(m.Subsys, str(m.Subsys)), m.ECode)
    #     else:
    #         mstr = m.text
    #     matches = fnmatch.fnmatch(mstr.upper(), wildcard.upper())
    #     if invert:
    #         matches = not matches
    #     if matches:
    #         print("%s %s" % (timestring(m), mstr))
    while True:
        try:
            # m = mlog.recv_match(type=['GLOBAL_POSITION_INT'])
            m = mlog.recv_match(type=['STATUSTEXT'])
            if m is None:
                break
            else:
                print(m)

        except Exception:
            break

    print("-------------------------------------")


    while True:
        try:
            # m = mlog.recv_match(type=['GLOBAL_POSITION_INT'])
            m = mlog.recv_match(type=['MSG'])
            if m is None:
                #print("m is none")
                break
            else:
                print(m)

        except Exception:
            break

    print("-------------------------------------")

    while True:
        try:
            # m = mlog.recv_match(type=['GLOBAL_POSITION_INT'])
            m = mlog.recv_match(type=['EV'])
            if m is None:
                break
            else:
                mstr = "Event: %s" % events.get(m.Id, str(m.Id))
                print("EV is :" + mstr)

        except Exception:
            break
        
    print("-------------------------------------")

    while True:
        try:
            # m = mlog.recv_match(type=['GLOBAL_POSITION_INT'])
            m = mlog.recv_match(type=['ERR'])
            if m is None:
                break
            else:
                mstr = "Error: Subsys %s ECode %u " % (subsystems.get(m.Subsys, str(m.Subsys)), m.ECode)
                print("ERR is :" + mstr)

        except Exception:
            break

    print("- end ------------------------------")


    # Shrink the number of points for readability and to stay within autopilot memory limits. 
    # For coding simplicity we:
    #   - only keep points that are with 3 metres of the previous kept point.
    #   - only keep the first 100 points that meet the above criteria.
    # num_points = len(messages)
    # keep_point_distance=3 #metres
    # kept_messages = []
    # kept_messages.append(messages[0]) #Keep the first message
    # pt1num=0
    # pt2num=1
    # while True:
    #     #Keep the last point. Only record 99 points.
    #     if pt2num==num_points-1 or len(kept_messages)==99:
    #         kept_messages.append(messages[pt2num])
    #         break
    #     pt1 = LocationGlobalRelative(messages[pt1num].lat/1.0e7,messages[pt1num].lon/1.0e7,0)
    #     pt2 = LocationGlobalRelative(messages[pt2num].lat/1.0e7,messages[pt2num].lon/1.0e7,0)
    #     distance_between_points = get_distance_metres(pt1,pt2)
    #     if distance_between_points > keep_point_distance:
    #         kept_messages.append(messages[pt2num])
    #         pt1num=pt2num
    #     pt2num=pt2num+1

    #return kept_messages