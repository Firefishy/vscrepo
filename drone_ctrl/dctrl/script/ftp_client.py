#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
^----^
 *  * 

"""

import ftplib
import time
import dlogger as dlog

class FtpClientCls():

    ftp = ""
    
    def __init__(self):
        dlog.LOG("INFO", "ftp client class init")

    ### =================================================================================== 
    ### FTP接続
    ### =================================================================================== 
    def connect(self):
        dlog.LOG("DEBUG", "START")
        self.ftp = ftplib.FTP("192.168.1.13")
        self.ftp.set_pasv('true')
        msg = self.ftp.login("sayz", "Popo3113@")
        dlog.LOG("DEBUG", msg)
        dlog.LOG("DEBUG", "START")

    ### =================================================================================== 
    ### TEXTファイルのアップロード
    ### =================================================================================== 
    def upload_txt(self, 
        src_path,
        file_name,
        dst_path
    ):
        dlog.LOG("DEBUG", "START")
        try:
            msg = src_path + file_name + " --> " + dst_path
            dlog.LOG("DEBUG", msg)
            with open(src_path + file_name, "rb") as fp:
                rts = self.ftp.storlines("STOR " + dst_path + file_name, fp)
                dlog.LOG("DEBUG", rts)
        except ftplib.all_errors as e:
            print(e)
        dlog.LOG("DEBUG", "END")

    ### =================================================================================== 
    ### バイナリファイルのアップロード
    ### =================================================================================== 
    def upload_bin(self, 
        src_path,
        file_name,
        dst_path
    ):
        dlog.LOG("DEBUG", "START")
        try:
            src_path = src_path.rstrip('/')
            dst_path = dst_path.rstrip('/')
            src_path = src_path + '/'
            dst_path + dst_path + '/'
            msg = src_path + file_name + " --> " + dst_path
            dlog.LOG("DEBUG", msg)
            with open(src_path + file_name, "rb") as fp:
                rts = self.ftp.storbinary("STOR " + dst_path + file_name, fp)
                dlog.LOG("DEBUG", rts)
        except ftplib.all_errors as e:
            print(e)
        dlog.LOG("DEBUG", "END")
    
    ### =================================================================================== 
    ### ディレクトリの作成
    ### =================================================================================== 
    def mkdir(self, dir_name):
        dlog.LOG("DEBUG", "START")
        dlog.LOG("DEBUG", dir_name)
        self.ftp.mkd(dir_name)
        dlog.LOG("DEBUG", "START")
    
    ### =================================================================================== 
    ### ファイルの一覧の取得
    ### =================================================================================== 
    def get_file_list(self, dir_name):
        dlog.LOG("DEBUG", "START")
        dlog.LOG("DEBUG", dir_name)
        file_list = self.ftp.nlst(dir_name)
        print(len(file_list))
        dlog.LOG("DEBUG", str(file_list))
        dlog.LOG("DEBUG", "START")
        
    ### =================================================================================== 
    ### クローズ
    ### =================================================================================== 
    def close(self):
        dlog.LOG("DEBUG", "START")
        self.ftp.close()
        dlog.LOG("DEBUG", "START")

    