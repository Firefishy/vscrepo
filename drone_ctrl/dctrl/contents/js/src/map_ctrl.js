/*
 ^----^
  *  * 
   ~
*/

// WebSocket connection
let sub = mqtt.connect('ws://127.0.0.1:9001');

// Topic definition
let topic_pub = "drone/dctrl";        // 操作コマンド、Simple Goto
let topic_mission = "drone/mission";  // ミッションデータ
let topic_sub = "drone/dinfo";        // 座標等のドローン情報

let dlat = 35.6566324;
let dlon = 139.7586453;
let dzoom = 15;

// ドローン情報保存用の配列
var drones = new Array();   // 緯度経度などのデータを保存する連想配列
var markers = new Array();  // マーカーハンドラを保存する連想配列

////////////////////////////////////////////////////////////////////////
// ドローン操作用送信コマンド
let drone_command = {
  "operation":"None",
  "subcode":"None",
  "d_lat":"0",
  "d_lon":"0",
  "d_alt":"0",
  "d_spd":"5"
}
// ドローンミッション用送信コマンド
let drone_mission = {
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

////////////////////////////////////////////////////////////////////////////////////////////////
// mapidと名の付いたdiv要素に地図を作成（[緯度,経度],拡大率）
let mymap = L.map('mapid').setView([dlat,dlon],dzoom);
    
////////////////////////////////////////////////////////////////////////////////////////////////
// OpenStreetMapのタイルレイヤーを作る
let tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    attribution: '© <a href="http://osm.org/copyright">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
    maxZoom: 19
});
tileLayer.addTo(mymap); // 作成したtileLayerをmymapに追加する

////////////////////////////////////////////////////////////////////////////////////////////////
// Goto/Missionの選択場所の判別
let flg_operation = 0;
let flg_mission_wp = 1;
const setOperation = (flg1, flg2) => {
  flg_operation = flg1;
  flg_mission_wp = flg2;
  console.log(flg1);
  console.log(flg2);
}


let mk;

////////////////////////////////////////////////////////////////////////////////////////////////
// 地図上を左クリックするとエディットボックスにその緯度/経度を書き込む
mymap.on('click', function(e) {
  console.log("Mouse clicked!");
  // Goto要素が選択されている場合
  if(flg_operation==0){
    document.getElementById('lat').value = e.latlng.lat;
    document.getElementById('lon').value = e.latlng.lng;
    console.log(e.latlng.lat);
    console.log(e.latlng.lng);

    //地図のclickイベント呼び出される
    //クリック地点の座標にマーカーを追加、マーカーのclickイベントでonMarkerClick関数を呼び出し
    //mk = L.marker(e.latlng).on('click', onMarkerClick).addTo(mymap);   

  }
  // Mission要素が選択されている場合：現状最大5箇所
  else{
    document.getElementById('mwp' +  flg_mission_wp.toString() + '_lat').innerHTML = e.latlng.lat;
    document.getElementById('mwp' +  flg_mission_wp.toString() + '_lon').innerHTML = e.latlng.lng;
    document.getElementById('mwp' +  flg_mission_wp.toString() + '_alt').innerHTML = 30.0;
  }

} );

// function onMarkerClick(e) {
//   //マーカーのclickイベント呼び出される
//   //クリックされたマーカーを地図のレイヤから削除する
//   mymap.removeLayer(e.target);
// }


////////////////////////////////////////////////////////////////////////////////////////////////
// マーカーにする画像を読み込む
let quad_x_Icon = L.icon({ iconUrl: '../img/quad_x-90.png', iconRetinaUrl: 'img/quad_x-90.png', iconSize: [50, 50], iconAnchor: [25, 25], popupAnchor: [0, -50] });

////////////////////////////////////////////////////////////////////////////////////////////////
// １秒毎にPublish実行
// pubLoop = setInterval(() => {
//   const time = Date.now().toString();
//   const temp = Math.floor( Math.random() * 11 );
//   let metric = '{"time":' + time + ', "name": "sensor1", "temp":' + temp + '}'
//   pub.publish(topic_pub, metric);
//   //console.log(metric.toString());
// }, 1000);

////////////////////////////////////////////////////////////////////////////////////////////////
// MQTT over WebSocketの初期化
// MQTTブローカーは自分自身
//var wsbroker = location.hostname;   
var wsbroker = "127.0.0.1";   
// MQTTの標準ポート番号は1883だが，WebSocketは15675とした(RabbitMQと同じ仕様)
var wsport = 9001; 

////////////////////////////////////////////////////////////////////////////////////////////////
// MQTTのクライアントを作成する クライアントID名はランダムに作る
var client = new Paho.MQTT.Client(
  wsbroker, 
  wsport, 
  "/ws", "myclientid_" + parseInt(Math.random() * 100, 10)
);

////////////////////////////////////////////////////////////////////////////////////////////////
// ドローンの情報を取得するMQTTサブスクライバ
sub.subscribe(topic_sub);
// サブスクライバのCallback
sub.on('message', function (topic_sub, message) {
  document.getElementById('msg1').innerHTML = "Vehicle: Connected !";
  document.getElementById('msg1').style.color = '#FFFF00';
  // ドローン名はトピック名とする"
  let drone_name = message.destinationName;
  // ドローンのデータを連想配列にして格納
  let drone_data = JSON.parse( message );         
  // ARM/DISARM
  let arm  = drone_data.status.Arm;                         
  // フライトモード
  let mode = drone_data.status.FlightMode;                  
  // 緯度
  dlat  = parseFloat( drone_data.position.latitude );       
  // 経度
  dlon  = parseFloat( drone_data.position.longitude );      
  // 高度
  let alt  = parseFloat( drone_data.position.altitude );    
  // 方位
  let ang  = parseFloat( drone_data.position.heading );
  // 速度
  let spd  = parseFloat( drone_data.position.speed );
  // バッテリ電圧
  let bvolt = parseFloat( drone_data.battery.voltage );
  // バッテリ電流
  let bcrnt = parseFloat( drone_data.battery.current );
  // GPS数
  let gpscnt = parseFloat( drone_data.gps.count );

  document.getElementById('carm').innerHTML = arm;
  if (arm == 'True'){
    document.getElementById('carm').style.color = '#ffff00';
  }
  else{
    document.getElementById('carm').style.color = '#777777';
  }
  document.getElementById('cmode').innerHTML = mode;
  document.getElementById('clat').innerHTML = dlat.toString();
  document.getElementById('clon').innerHTML = dlon.toString();
  document.getElementById('calt').innerHTML = alt.toString();
  if (alt > 1.0){
    document.getElementById('calt').style.color = '#ffff00';
  }
  else{
    document.getElementById('calt').style.color = '#777777';
  }
  document.getElementById('cang').innerHTML = ang.toString();
  document.getElementById('cvlt').innerHTML = bvolt.toString();
  document.getElementById('ccnt').innerHTML = bcrnt.toString();
  document.getElementById('cgps').innerHTML = gpscnt.toString();
  document.getElementById('cspd').innerHTML = spd.toString();

  // ポップアップ用に文字列を作る +=で追加していく
  let drone_popmessage = drone_name + '<br>';
  drone_popmessage += mode + ',' + arm + '<br>';
  drone_popmessage += dlon + ',' + dlat + '<br>';
  drone_popmessage += alt + '[m], ' + ang + '[deg]<br>';

  // drone_nameで登録されている連想配列があるか？ ない->新規にマーカー作成 ある->なにもしない
  if( !drones[drone_name] ) {
    // movingMarkerでマーカーを作成し，rotatedMarkerのrotationオプションをつける
    markerHandle = L.Marker.movingMarker([[dlat, dlon]], [], 
                    {   rotationAngle: 0,   // 回転角度
                        rotationOrigin: 'center center',    // 回転中心
                        title:drone_name,
                        contextmenu: true,
                        contextmenuItems: [{
                            text: drone_name,
                            index: 0
                        }, {
                            separator: true,
                            index: 1
                        }]
                    });
    markerHandle.bindPopup( drone_popmessage ); // ポップアップメッセージの設定
    markerHandle.options.icon = quad_x_Icon;    // マーカーアイコンをオリジナル画像に
    markerHandle.options.autostart = true;      // MovingMarker機能を自動スタート
    markerHandle.addTo( mymap );                // 地図へ追加

    markers[drone_name] = markerHandle; // マーカー用連想配列に今回作ったマーカー情報を保存
  } 
  else {
    markerHandle = markers[drone_name]  // 保存されているマーカー情報をdrone_name(トピック名)をキーにして呼び出す
    markerHandle.moveTo([dlat,dlon], 1000);  // MovingMarkerの移動機能
    markerHandle.setRotationAngle(ang);    // ratatedMarkerの回転機能
    markerHandle.setPopupContent( drone_popmessage );   // メッセージ更新
  }
  drones[drone_name] = drone_data; // ドローンデータ用連想配列の情報を最新のメッセージに更新
});

// Finish
setTimeout(function() {
  //clearInterval( pubLoop );
  pub.end();
  sub.end();
}, 100000); // stop after 100sec

////////////////////////////////////////////////////////////////////////////////////////////////
// イベントハンドラ（HTML上のボタンが押下）
const droneCtrl = (ope) => {
  let latData, lonData, altData, speed;

  drone_command["d_lat"] = 0;
  drone_command["d_lon"] = 0;
  drone_command["d_alt"] = 0; 
  
  // Simple GOTO: 緯度/経度/高度を取得してコマンドをドローンに送信
  if(ope == "GOTO") {
    // 操作画面から目的地の座標を取得して設定する
    drone_command["operation"] = ope;
    drone_command["subcode"] = document.getElementById('msgid').innerHTML;
    latData = document.getElementById('lat').value;
    console.log(latData);
    lonData = document.getElementById('lon').value;
    console.log(lonData);
    altData = document.getElementById('alt').value;
    console.log(altData);
    spdData = document.getElementById('spd').value;
    console.log(spdData);
    drone_command["d_lat"] = latData;
    drone_command["d_lon"] = lonData;
    drone_command["d_alt"] = altData;
    drone_command["d_spd"] = spdData;

    // MQTTでパブリッシュする
    pubCommand(topic_pub,drone_command);
  }

  // Mission: ミッションポイントを取得してドローンへ送信
  else if(ope == "MISSION_UPLOAD"){
    let cmdAry = [];
    let mission_cmd;

    let clatData = document.getElementById('clat').innerHTML;
    let clonData = document.getElementById('clon').innerHTML;
    let caltData = document.getElementById('calt').innerHTML;

    let idx = 0;
    // 現在のウェイポイント
    mission_cmd = makeMissionCmdWithTab(
      idx++,
      1,
      3,
      document.getElementById('mwp1_cmd').value, 
      clatData, clonData, caltData, 1
    );         
    cmdAry.push(mission_cmd) 

    // 現在位置で離陸: 離陸高度を5mとする（暫定）
    // mission_cmd = makeMissionCmdWithTab(idx++, 0, 3, 22, clatData, clonData, 5.0, 1);     
    // cmdAry.push(mission_cmd) 

    // ミッションウェイポイントの設定
    for (let i = 1; i < 6; i++){
      if( document.getElementById("achk" + i.toString()).checked == true ){
        latData = document.getElementById('mwp' + i.toString() + '_lat').innerHTML;
        lonData = document.getElementById('mwp' + i.toString() + '_lon').innerHTML;
        altData = document.getElementById('mwp' + i.toString() + '_alt').innerHTML;
        mission_cmd = makeMissionCmdWithTab(
                        idx++,
                        0, 
                        3,
                        document.getElementById('mwp' + i.toString() + '_cmd').value, 
                        latData, lonData, altData, 1
        );
        console.log(mission_cmd);
        cmdAry.push(mission_cmd);
      }       
    }

    // RTL
    if(document.getElementById("achke").checked == true){
      mission_cmd = makeMissionCmdWithTab(idx, 0, 3, 20, clatData, clonData, caltData, 1); 
      cmdAry.push(mission_cmd)  
    }

    // コマンドの送信
    pubCommand(topic_mission,cmdAry);

    // Goto、Mission以外のコマンド送信時
    drone_command["operation"] = ope;
    console.log(drone_command["operation"] = ope)

    // MQTTでパブリッシュする
    pubCommand(topic_pub,drone_command);

  }
  else{
    // Goto、Mission以外のコマンド送信時
    drone_command["operation"] = ope;
    console.log(drone_command["operation"] = ope)
    // MQTTでパブリッシュする
    pubCommand(topic_pub,drone_command);
  }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// ミッションデータ（各WPのデータ）を作成
const makeMissionCmdWithTab = (
  idx,              // index: 0,1,2 ...
  cwp,              // current waypoint: 0, 1
  frame,            // 0: global+MSL, 3:global+rel
  cmd,              // command: 16, 22
  lat , lon, alt,
  cnt
) => {
  missionData =   idx + '\t' 
                + cwp + '\t' + frame + '\t' + cmd + '\t' 
                + 0 + '\t' + 0 + '\t' + 0 + '\t'  + 0 + '\t'
                + lat + '\t' 
                + lon + '\t' 
                + alt + '\t'
                + cnt + '\r\n';
  return missionData;
}

////////////////////////////////////////////////////////////////////////////////////////////////
// JSON型にしてからMQTTでPublishする
const pubCommand = (topic, cmd) => {
  console.log("Pub command");
  // JSON型にする
  json_command = JSON.stringify(cmd);
  // MQTTのメッセージパケットを作る
  message = new Paho.MQTT.Message(json_command);  
  // トピック名を設定
  message.destinationName = topic;            
  // MQTTでPubする
  client.send(message); 
  //debugボックスに表示
  console.log("SEND ON " + message.destinationName + " PAYLOAD " + message.payloadString);   
}

////////////////////////////////////////////////////////////////////////////////////////////////
// Missionファイルを作成
const createMissionFile = () =>{
  // 1. Blobオブジェクトを作成する
  const blob = new Blob(['あいうえお'],{type:"text/plain"});
  // 2. HTMLのa要素を生成
  const link = document.createElement('a');
  // 3. BlobオブジェクトをURLに変換
  link.href = URL.createObjectURL(blob);
  // 4. ファイル名を指定する
  link.download = 'aaa.txt';
  // 5. a要素をクリックする処理を行う
  link.click();
}

////////////////////////////////////////////////////////////////////////////////////////////////
let has_had_focus = false;
let pipe = function(el_name, send) {
  let div  = $(el_name + ' div');
  let inp  = $(el_name + ' input');
  let form = $(el_name + ' form');

  let print = function(m, p) {
        p = (p === undefined) ? '' : JSON.stringify(p);
        div.append($("<code>").text(m + ' ' + p));
        div.scrollTop(div.scrollTop() + 10000);
    };

    if (send) {
        form.submit(function() {
            send(inp.val());
            inp.val('');
            return false;
        });
    }
    return print;
};

////////////////////////////////////////////////////////////////////////////////////////////////
let print_first = pipe('#first', function(data) {
    message = new Paho.MQTT.Message(data);
    message.destinationName = "test";
    debug("SEND ON " + message.destinationName + " PAYLOAD " + data);
    client.send(message);
});

let debug = pipe('#second');

////////////////////////////////////////////////////////////////////////////////////////////////
// MQTTの接続オプション
var options = {
  timeout: 3,
  onSuccess: function () {
    debug("CONNECTION SUCCESS");
    client.subscribe('drone/#', {qos: 1});
  },
  onFailure: function (message) {
    debug("CONNECTION FAILURE - " + message.errorMessage);
  }
};

// サーバーがHTTPS対応だった時の処理
if (location.protocol == "https:") {
  options.useSSL = true;
}

// 最初にメッセージを表示してMQTTをブローカーに接続
debug("CONNECT TO " + wsbroker + ":" + wsport);
client.connect(options);        // 接続

