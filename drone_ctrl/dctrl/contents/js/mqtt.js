/*
 ^----^
  *  * 
   ~
*/

// WebSocket connection
let pub = mqtt.connect('ws://127.0.0.1:9001');
let sub = mqtt.connect('ws://127.0.0.1:9001');

// Topic definition
let topic_sub = "drone/frame";
let topic_pub = "drone/dinfo";

let dlat = 35.89;
let dlon = 139.95;
let dzoom = 15;

// ドローン情報保存用の配列
var drones = new Array();   // 緯度経度などのデータを保存する連想配列
var markers = new Array();  // マーカーハンドラを保存する連想配列

// mapidと名の付いたdiv要素に地図を作成し，視点は富士山頂付近，ズームレベルは13に設定
//var mymap = L.map('mapid').setView([35.370772,138.727305], 13);
var mymap = L.map('mapid').setView([dlat,dlon], dzoom);
    
// OpenStreetMapのタイルレイヤーを作る
var tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    attribution: '© <a href="http://osm.org/copyright">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
    maxZoom: 19
});
tileLayer.addTo(mymap); // 作成したtileLayerをmymapに追加する
    
// マーカーを作り，それに紐付けるポップアップも同時作成
// L.marker([dlat,dlon])
//     .addTo(mymap)       // 富士山頂にマーカーを追加
//     .bindPopup("現在位置").openPopup();   // ポップアップで出すメッセージ

// マーカーにする画像を読み込む
var quad_x_Icon = L.icon({ iconUrl: 'img/quad_x-90.png', iconRetinaUrl: 'img/quad_x-90.png', iconSize: [50, 50], iconAnchor: [25, 25], popupAnchor: [0, -50] });

// Subscriber
sub.subscribe(topic_sub);

// Interval
pubLoop = setInterval(() => {
  const time = Date.now().toString();
  const temp = Math.floor( Math.random() * 11 );
  let metric = '{"time":' + time + ', "name": "sensor1", "temp":' + temp + '}'
  pub.publish(topic_pub, metric);
  //console.log(metric.toString());
}, 1000);

// Callback
sub.on('message', function (topic_sub, message) { // message is Buffer
  var drone_name = message.destinationName;   // ドローン名はトピック名とする
  var drone_data = JSON.parse( message );   // ドローンのデータを連想配列にして格納
  //console.log(drone_data.toString());
  var arm  = drone_data.status.Arm;                       // ARM/DISARM
  var mode = drone_data.status.FlightMode;         let       // フライトモード
  dlat  = parseFloat( drone_data.position.latitude );  // 緯度
  dlon  = parseFloat( drone_data.position.longitude ); // 経度
  let alt  = parseFloat( drone_data.position.altitude );  // 高度
  let ang  = parseFloat( drone_data.position.heading );   // 方位

  document.getElementById('cmt1').innerHTML = dlat.toString();
  document.getElementById('cmt2').innerHTML = dlon.toString();
  document.getElementById('cmt3').innerHTML = alt.toString();
  document.getElementById('cmt4').innerHTML = ang.toString();

  // ポップアップ用に文字列を作る +=で追加していく
  var drone_popmessage = drone_name + '<br>';
  drone_popmessage += mode + ',' + arm + '<br>';
  drone_popmessage += dlon + ',' + dlat + '<br>';
  drone_popmessage += alt + '[m], ' + ang + '[deg]<br>';

  // L.marker([dlat,dlon])
  // .addTo(mymap)       // 富士山頂にマーカーを追加
  // .bindPopup("現在位置").openPopup();   // ポップアップで出すメッセージ

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


