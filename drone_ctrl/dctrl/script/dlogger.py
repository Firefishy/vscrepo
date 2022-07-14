#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logger for debugging
 ^----^
  *  * 
   ~
"""
import inspect
import datetime
import sys
import os
import json

LEVEL = (0,0,1,2,3)

###############################################################################################
# ログレベルの設定について
#   DEBUG       : レベル1（最下層レベル）、デバック用ログ
#   INFO        : レベル2 情報
#   WARNING     : レベル3 ワーニング
# --- 以下はレベル設定にかかわらず常にコンソールとログファイルに記録されます。-----------------
#   ERROR       : エラー情報（プログラムエラー等）
#   CRITICAL    : 深刻な問題が発生
###############################################################################################

def init():
    msglevel = LEVEL[3]
    base_path = os.path.dirname(os.path.abspath(__file__))
    json_file_name = os.path.normpath(os.path.join(base_path, '../json/logfile.json'))

    json_open = open(json_file_name, 'r')
    json_load = json.load(json_open)
    msglevel = (json_load['logfile']['level'])
    log_file_path = (json_load['logfile']['path'])
    # create log file folder 
    #os.makedirs(log_file_path, exist_ok=True) # Python3.2 or later

    try:
        os.makedirs(log_file_path)
    except OSError:
        pass

    if msglevel == 'DEBUG' or msglevel == 'debug':
        msglevel = LEVEL[4] 
    elif msglevel == 'INFO' or msglevel == 'info':
        msglevel = LEVEL[3] 
    elif msglevel == 'WARNING' or msglevel == 'warning':
        msglevel = LEVEL[2] 
    else:
        msglevel = LEVEL[1]
    return log_file_path, msglevel

def __del__():
    print("end log file")

def LOG(level, msg):
    rts = init()
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    mn = calframe[1][3]

    today = datetime.datetime.now()
    now_day = today.strftime('%Y-%m-%d')
    now_datetime = today.strftime('%Y-%m-%d_%H:%M:%S')
    base_path = os.path.dirname(os.path.abspath(__file__))
    debug_log_file_name = os.path.normpath(os.path.join(base_path, rts[0] + now_day + ".log"))
    _file = open(debug_log_file_name, mode='a')   
    msg = "<" + level + "> " + now_datetime + " [" + mn + "] " + msg + "\r\n"

    # Error level CRITICAL and ERROR are always logged and console out
    if level == 'CRITICAL' or level == 'critical':
        #print('\035[41m'+msg+'\033[0m',end="") # for python3
        sys.stdout.write('\035[41m'+msg+'\033[0m') # for python2
        _file.write(msg)
    elif level == 'ERROR' or level == 'error':
        #print('\033[31m'+msg+'\033[0m',end="") # for python3
        sys.stdout.write('\033[31m'+msg+'\033[0m') # for python2
        _file.write(msg)
    elif (level == 'WARNING' or level == 'warning') and rts[1] >= LEVEL[2]:
        #print('\033[33m'+msg+'\033[0m',end="") # for python3
        sys.stdout.write('\033[33m'+msg+'\033[0m') # for python2
        _file.write(msg)
    elif (level == 'INFO' or level == 'info') and rts[1] >= LEVEL[3]:
        #print('\033[36m'+msg+'\033[0m',end="") # for python3
        sys.stdout.write('\033[36m'+msg+'\033[0m') # for python2
        _file.write(msg)
    elif (level == 'DEBUG' or level == 'debug') and rts[1] >= LEVEL[4]:
        #print('\033[36m'+msg+'\033[0m',end="") # for python3
        sys.stdout.write('\033[36m'+msg+'\033[0m') # for python2
        _file.write(msg)
    _file.close()