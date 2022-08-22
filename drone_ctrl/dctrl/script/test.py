#!usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

msg = {
  "WP1_actions" : {
    "waypoint":1,                           # ウェイポイント番号
    "action_num" :2,                        # ウェイポイントに紐づくアクション数
    # 1つめのアクションの詳細
    "WP1_action1" : {
      "action_type" : "hovering",           # アクションタイプ（ホバリング）
      "value" : 10,                 # ホバリング秒数（アクションタイプがホバリングの場合）
    },
    # 2つめのアクションの詳細
    "WP1_action2" : {
      "action_type" : "aircraft_rotate",    # アクションタイプ（機体回転）
      "value" :90,                   # 機体回転角度（アクションタイプが機体回転の場合）
    }
  },
  "WP2_actions" : {
    "waypoint" : 2,
    "action_num" : 1,
    "WP2_action1" : {
      "action_type" : "hovering",
      "value" : 10,
    }
  },
  "WP3_actions" : {
    "waypoint" : 3,
    "action_num" : 4,
    "WP3_action1" : {
      "action_type" : "aircraft_rotate",
      "value" : 10,
    },
    "WP3_action2" : {
      "action_type" : "hovering",
      "value" : 10,
    },
    "WP3_action3" : {
      "action_type" : "aircraft_rotate",
      "value" : -10,
    },
    "WP3_action4" : {
      "action_type" : "hovering",
      "value" : 10,
    }
  },
}

wp1_action_list = []
wp2_action_list = []
wp3_action_list = []
wp4_action_list = []
wp5_action_list = []
wp6_action_list = []
wp7_action_list = []
wp8_action_list = []





def set_wp_action(wp_action, cnt):

  for wp_num in range(cnt):
      for ac_num in range(msg["WP" + str(wp_num+1) + "_actions"]["action_num"]):
          wp_action[wp_num].append(msg["WP" + str(wp_num+1) + "_actions"]["WP" + str(wp_num+1) + "_action" + str(ac_num+1)]["action_type"])
          wp_action[wp_num].append(msg["WP" + str(wp_num+1) + "_actions"]["WP" + str(wp_num+1) + "_action" + str(ac_num+1)]["value"])

def clr_wp_action(wp_action, cnt):
  for i in range(3):
    wp_action[i].clear()




if __name__ == '__main__':

  for i in range(3):

    wp_action = [
        wp1_action_list,
        wp2_action_list,
        wp3_action_list,
        wp4_action_list,
        wp5_action_list,
        wp6_action_list,
        wp7_action_list,
        wp8_action_list
    ]

    clr_wp_action(wp_action, 3)
    set_wp_action(wp_action, 3)
    print(wp_action)
