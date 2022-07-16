/*
 ^----^
  *  * 
   ~
*/

// WebSocket connection
//let pub = mqtt.connect('ws://127.0.0.1:9001');
let sub = mqtt.connect('ws://127.0.0.1:9001');

// Topic definition
let topic_pub = "drone/dctrl"; // コマンド、ミッションデータ
let topic_sub = "drone/dinfo"; // 座標等のドローン情報

let dlat = 35.89;
let dlon = 139.95;
let dzoom = 15;

// ドローン情報保存用の配列
var drones = new Array();   // 緯度経度などのデータを保存する連想配列
var markers = new Array();  // マーカーハンドラを保存する連想配列

// ドローン操作用のコマンドの連想配列
let command = {
  "command":"None",
  "d_lat":"0",
  "d_lon":"0",
  "d_alt":"0",
}

// ドローンミッション用のコマンドの連想配列
let mission_data = {
  "index":"0",
  "cntwp":"0",
  "frame":"0",
  "command":"0",
  "para1":"0",
  "para2":"0",
  "para3":"0",
  "para4":"0",
  "lat":"0",
  "lon":"0",
  "alt":"0",
  "acnt":"0"
}

// mapidと名の付いたdiv要素に地図を作成’（[緯度,経度],拡大率）
let mymap = L.map('mapid').setView([dlat,dlon],dzoom);
    
// OpenStreetMapのタイルレイヤーを作る
let tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    attribution: '© <a href="http://osm.org/copyright">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
    maxZoom: 19
});
tileLayer.addTo(mymap); // 作成したtileLayerをmymapに追加する

// 地図上を左クリックするとエディットボックスにその緯度/経度を書き込む
mymap.on('click', function(e) {
  console.log("Mouse clicked!");
  document.getElementById('lat').value = e.latlng.lat;
  document.getElementById('lon').value = e.latlng.lng;
} );

// マーカーにする画像を読み込む
let quad_x_Icon = L.icon({ iconUrl: 'img/quad_x-90.png', iconRetinaUrl: 'img/quad_x-90.png', iconSize: [50, 50], iconAnchor: [25, 25], popupAnchor: [0, -50] });


// １秒毎にPublish実行
// pubLoop = setInterval(() => {
//   const time = Date.now().toString();
//   const temp = Math.floor( Math.random() * 11 );
//   let metric = '{"time":' + time + ', "name": "sensor1", "temp":' + temp + '}'
//   pub.publish(topic_pub, metric);
//   //console.log(metric.toString());
// }, 1000);

// サブスクライバ
sub.subscribe(topic_sub);
// サブスクライバのCallback
sub.on('message', function (topic_sub, message) {
  // ドローン名はトピック名とする
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

  // document.getElementById('lat').innerHTML = dlat.toString() + " deg";
  // document.getElementById('lon').innerHTML = dlon.toString() + " deg";
  // document.getElementById('alt').innerHTML = alt.toString() + " m";
  //document.getElementById('ang').innerHTML = ang.toString() + " deg";
  document.getElementById('lat').value = dlat;
  document.getElementById('lon').value = dlon;
  document.getElementById('alt').value = alt;
  document.getElementById('ang').value = ang;

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
  clearInterval( pubLoop );
  pub.end();
  sub.end();
}, 100000); // stop after 100sec


// MQTT over WebSocketの初期化
// MQTTブローカーは自分自身
//var wsbroker = location.hostname;   
var wsbroker = "127.0.0.1";   
// MQTTの標準ポート番号は1883だが，WebSocketは15675とした(RabbitMQと同じ仕様)
var wsport = 9001; 

// MQTTのクライアントを作成する クライアントID名はランダムに作る
var client = new Paho.MQTT.Client(
  wsbroker, 
  wsport, 
  "/ws", "myclientid_" + parseInt(Math.random() * 100, 10)
);


// HTML上のボタンが押された時の処理
//function droneCtrl(str) {
const droneCtrl = (str) => {
  command["command"] = str;   // 引数の文字列がそのままコマンドになる
  // GOTOのときは，緯度/経度/高度も取得してコマンドを作る
  if( str == "GOTO" ) {
    console.log("###");
    let _lat = document.getElementById('lat').value;
    console.log(_lat);
    let _lon = document.getElementById('lon').value;
    console.log(_lon);
    let _alt = document.getElementById('alt').value;
    console.log(_alt);
    command["d_lat"] = _lat;
    command["d_lon"] = _lon;
    command["d_alt"] = _alt;
  }
  else{
    command["d_lat"] = 0;
    command["d_lon"] = 0;
    command["d_alt"] = 0;  
  }
  pubCommand(command);
}

// JSON型にしてからMQTTでPublishする
const pubCommand = (command) => {
  // JSON型にする
  json_command = JSON.stringify(command);
  // MQTTのメッセージパケットを作る
  message = new Paho.MQTT.Message(json_command);  
  // トピック名を設定
  message.destinationName = "drone/dctrl";            
  // MQTTでPubする
  client.send(message); 
  console.log("SEND ON " + message.destinationName + " PAYLOAD " + message.payloadString);   //debugボックスに表示
}

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

let print_first = pipe('#first', function(data) {
    message = new Paho.MQTT.Message(data);
    message.destinationName = "test";
    debug("SEND ON " + message.destinationName + " PAYLOAD " + data);
    client.send(message);
});

let debug = pipe('#second');




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

