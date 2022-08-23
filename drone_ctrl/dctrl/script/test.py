#!usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

__msg = {
  "WP1_actions" : {
    "waypoint":1,                   # ウェイポイント番号
    "action_num" :2,                # ウェイポイントに紐づくアクション数
    # 1つめのアクションの詳細
    "WP1_action1" : {
      "action_type" : "hovering",   # アクションタイプ（ホバリング）
      "value" : 10,                 # ホバリング秒数（アクションタイプがホバリングの場合）
    },
    # 2つめのアクションの詳細
    "WP1_action2" : {
      "action_type" : "rotate",     # アクションタイプ（機体回転）
      "value" :90,                  # 機体回転角度（アクションタイプが機体回転の場合）
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
      "action_type" : "rotate",
      "value" : 10,
    },
    "WP3_action2" : {
      "action_type" : "hovering",
      "value" : 10,
    },
    "WP3_action3" : {
      "action_type" : "rotate",
      "value" : -10,
    },
    "WP3_action4" : {
      "value" : 10,
      "action_type" : "hovering",
      "value" : 10,
    }
  },
  # WP4_actions
  # WP5_actions
  # WP6_actions
  # WP7_actions
}

#// ウェイポイントアクションデータ
__wp_action = {
  "WP1_actions" : {
        "waypoint":1,                   #// ウェイポイント番号
        "action_num" :2,                #// ウェイポイントに紐づくアクション数
        #// 1つめのアクションの詳細
        "WP1_action1" : {
            "action_type" : "hovering",   #// アクションタイプ（ホバリング）
            "value" : 10,                 #// ホバリング秒数（アクションタイプがホバリングの場合）
        },
        #// 2つめのアクションの詳細
        "WP1_action2" : {
            "action_type" : "rotate",     #// アクションタイプ（機体回転）
            "value" :90,                  #// 機体回転角度（アクションタイプが機体回転の場合）
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
            "action_type" : "rotate",
            "value" : 10,
        },
        "WP3_action2" : {
            "action_type" : "hovering",
            "value" : 10,
        },
        "WP3_action3" : {
            "action_type" : "rotate",
            "value" : -10,
        },
        "WP3_action4" : {
            "action_type" : "hovering",
            "value" : 10,
        }
    },
    "WP4_actions" : {
        "waypoint" : 4,
        "action_num" : 3,
        "WP4_action1" : {
            "action_type" : "hovering",
            "value" : 5,
        },
        "WP4_action2" : {
            "action_type" : "rotate",
            "value" : -135,
        },
        "WP4_action3" : {
            "action_type" : "hovering",
            "value" : 5,
        }
    },
    "WP5_actions" : {
        "waypoint" : 5,
        "action_num" : 3,
        "WP5_action1" : {
            "action_type" : "hovering",
            "value" : 5,
        },
        "WP5_action2" : {
            "action_type" : "rotate",
            "value" : -135,
        },
        "WP5_action3" : {
            "action_type" : "hovering",
            "value" : 5,
        }
    },
    "WP6_actions" : {
        "waypoint" : 6,
        "action_num" : 3,
        "WP6_action1" : {
            "action_type" : "hovering",
            "value" : 5,
        },
        "WP6_action2" : {
            "action_type" : "rotate",
            "value" : -275,
        },
        "WP6_action3" : {
            "action_type" : "hovering",
            "value" : 5,
        }
    },
    "WP7_actions" : {
        "waypoint" : 7,
        "action_num" : 3,
        "WP7_action1" : {
            "action_type" : "hovering",
            "value" : 5,
        },
        "WP7_action2" : {
            "action_type" : "rotate",
            "value" : 45,
        },
        "WP7_action3" : {
            "action_type" : "hovering",
            "value" : 5,
        }
    },
    "WP8_actions" : {
        "waypoint" : 8,
        "action_num" : 3,
        "WP8_action1" : {
            "action_type" : "hovering",
            "value" : 5,
        },
        "WP8_action2" : {
            "action_type" : "rotate",
            "value" : 45,
        },
        "WP8_action3" : {
            "action_type" : "hovering",
            "value" : 5,
        }
    }
}



wp1_action_list = []
wp2_action_list = []
wp3_action_list = []
wp4_action_list = []
wp5_action_list = []
wp6_action_list = []
wp7_action_list = []
wp8_action_list = []


def clr_wp_action(wp_action, cnt):
  for i in range(cnt):
    wp_action[i].clear()


def set_wp_action(wp_action, msg, cnt):

  for wp_num in range(cnt):
    for ac_num in range(msg["WP" + str(wp_num+1) + "_actions"]["action_num"]):
        wp_action[wp_num].append(msg["WP" + str(wp_num+1) + "_actions"]["WP" + str(wp_num+1) + "_action" + str(ac_num+1)]["action_type"])
        wp_action[wp_num].append(msg["WP" + str(wp_num+1) + "_actions"]["WP" + str(wp_num+1) + "_action" + str(ac_num+1)]["value"])
    print (len(wp_action[wp_num]))
  
  # for i in range(int(len(wp_action[0])/2)):
  #   print(str(i) +":" + str(wp_action[i]))
  # for i in range(len(wp_action[1])/2):
  #   print("2"+ str(wp_action[i]))
  # for i in range(len(wp_action[2])/2):
  #   print("3"+ str(wp_action[i]))

# [
#   ['hovering', 10, 'rotate', 90], 
#   ['hovering', 10], 
#   ['rotate', 10, 'hovering', 10, 'rotate', -10, 'hovering', 10], 
#   ['hovering', 5, 'rotate', -135, 'hovering', 5], 
#   ['hovering', 5, 'rotate', -135, 'hovering', 5], 
#   ['hovering', 5, 'rotate', -275, 'hovering', 5], 
#   ['hovering', 5, 'rotate', 45, 'hovering', 5], 
#   ['hovering', 5, 'rotate', 45, 'hovering', 5]
# ]


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

    clr_wp_action(wp_action, 8)
    set_wp_action(wp_action, __wp_action, 8)


    print(wp_action)
