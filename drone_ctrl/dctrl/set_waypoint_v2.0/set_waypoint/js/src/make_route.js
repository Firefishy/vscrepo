
//var role = sessionStorage.getItem('role');
var WP_list=[//0番はサンプル
  [["lng","lat"],"WP_speed","WP_altitude"],
  [[139.759090444, 35.6564644750],5,50],
]

var markers=[];
var sub_markers=[]
var open_point=[];
var marker_hover_flg;
var add_marker_flg;


$(function () {
    //jQuery.support.cors = true;
    init();
});


//初期設定
function init() {
	$('.slider').each((_, e) => {
	  change_slider($(e))
	});
	map.on('load', function () {
		reset_markers()
	})
};

//スライダーの数値表示+変更チェック
$('.slider').on('input change', function(){
	change_slider($(this));
	edit_event()
	
});
$('.number_input').on('change', function(){
	change_input($(this))
	edit_event()
});
$('.sidebar_select').change( function(){
	edit_event()
});
function change_slider(obj){
	let resultFeild = $(obj).prev($(".numberinput_unit")).children(".number_input");
	let value = Number($(obj).val());
	resultFeild.val(value);
	if(open_point[0]=='waypoint'){
		if($(obj).attr('id')=='WP_altitude'){
			//console.log('altitude change')
			WP_list[open_point[1]][2]=value
		}else if($(obj).attr('id')=='WP_speed'){
			//console.log('speed change')
			WP_list[open_point[1]][1]=value
		}
	}
};
function change_input(obj){
	let resultFeild = $(obj).parent($(".numberinput_unit")).next(".slider");
	let value = Number($(obj).val());
	if(Number(resultFeild.attr("min"))>=value){
		value=Number(resultFeild.attr("min"))
	}else if(Number(resultFeild.attr("max"))<=value){
		value=Number(resultFeild.attr("max"))
	}resultFeild.val(value);
	change_slider(resultFeild);
};

//緯度経度の入力時に地図上のマーカーも移動させる
$('#longitude').on('change', function(){
	set_lnglat()
});
$('#latitude').on('change', function(){
	set_lnglat()
});
function set_lnglat(){
	if(open_point[0]=='waypoint'){
		WP_list[open_point[1]][0]=[Number($('#latitude').val()), Number($('#longitude').val())]
		markers[open_point[1]].setLngLat(WP_list[open_point[1]][0])
	}
	line_rewrite()
	edit_event()
}



//ポイントタブを開くときの処理
function open_point_tab(id,type){
    open_point=[type,id]
    $('#point-tab').removeClass('disabled');
    $(".nav-tabs a[href='#item1']").tab( 'show' );
    if(type=='waypoint'){//ウェイポイントがクリックされたとき
    	markers[id].setDraggable(true);
        $(".waypoint_info").removeClass('non_active')
        $('#point_type').html('ウェイポイント')
        $("#Waypoint_No").html(id)
        $('#longitude').val(WP_list[id][0][1])
        $('#latitude').val(WP_list[id][0][0])
        $('#WP_speed').val(WP_list[id][1])
        $('#WP_altitude').val(WP_list[id][2])
    }
    $('input').each((_, e) => { //スライダーを更新
	  change_input($(e))
	});
}

//地図上クリックでポイントの選択を外しタブを閉じる
map.on('click',function(){
	if(marker_hover_flg==false){
		close_point_tab(false);
	}
})
//ポイントタブを閉じるときの処理
function close_point_tab(delete_flg){
    $('#point-tab').addClass('disabled');
    $(".waypoint_info").addClass('non_active');
    $(".nav-tabs a[href='#item2']").tab( 'show' );
    let target1=document.getElementsByClassName("WP_marker")
    for(var i = 0; i < target1.length; i++) { 
        target1[i].style.backgroundColor="#00ff7f"
        markers[i+1].setDraggable(false);
    }
    if(delete_flg!=true){
        if(open_point[0]=='waypoint'){
            WP_list[open_point[1]]=[
				[Number($('#latitude').val()), Number($('#longitude').val())],
				Number($('#WP_speed').val()),
				Number($('#WP_altitude').val())
			]
			//console.log(WP_list[open_point[1]])
        }
    }
    edit_event()
    $('#columns li#WP_action').each(function() {$(this).remove()});
    open_point=[]
}


//WP新規追加 
function add_new_marker(){
	if(add_marker_flg!=true){
	  add_marker_flg=true
	  map.once('click',make_new_marker_data);
	  $(".mapboxgl-canvas").css("cursor","crosshair");
    }
};
function make_new_marker_data(e){
    let id=WP_list.length;
    let lnglat=[e.lngLat.lng,e.lngLat.lat];
    WP_list[id]=[
        lnglat,
        Number($("#speed").val()),
        Number($("#altitude").val())
    ]
    create_marker(id);
    $(".mapboxgl-canvas").css("cursor","");
    edit_event();
    //追加したWPのタブを開く
    close_point_tab()
    let target =document.getElementsByClassName("WP_marker")
    target[target.length-1].style.backgroundColor="orange"
    open_point_tab(id,'waypoint');
    add_marker_flg=false
}
//WP描画
function create_marker(id) {
  const template = document.getElementById('marker');
  const clone = document.importNode(template.content, true);
  clone.getElementById('id').innerHTML = id;
  let el = clone.firstElementChild;
  //クリック時処理
  el.addEventListener('click', () => { 
	if(add_marker_flg!=true){
	  close_point_tab()
	  el.style.backgroundColor="orange";
	  open_point_tab(id,'waypoint');
	}
  });
  //マーカーホバー時に確認
  el.addEventListener('mouseover', () => {
    marker_hover_flg=true;
  });
  el.addEventListener('mouseout', () => {
    marker_hover_flg=false;
  });
  //マーカーをマップに追加
  one_marker = new mapboxgl.Marker(el)
    .setLngLat(WP_list[id][0])
    .addTo(map)
    .on('drag',function(){//ドラッグ時の処理
	    const lngLat = this.getLngLat();
        let coordinates = [lngLat.lng,lngLat.lat]
        WP_list[id][0]=coordinates
        $('#longitude').val(WP_list[id][0][1])
        $('#latitude').val(WP_list[id][0][0])
        line_rewrite()
        edit_event()
      })
  markers[id]=one_marker;
  //console.log(WP_list[id][0])
  if(id==WP_list.length-1){line_rewrite()};
};
//WP削除
function remove_WPmarker(){
	markers[open_point[1]].remove();
	let WP_list_copy=[];
	for(let i=0; i<WP_list.length; i++){
		if(i!=open_point[1]){
			WP_list_copy.push(WP_list[i])
		}
	}
	close_point_tab(true)
	WP_list.splice(0)
	WP_list=WP_list_copy;
	reset_markers()
}


//ライン描画 + サブマーカーの描画呼び出し
function line_rewrite(){
	let lnglat_list=[];
    for(let i=1; i<WP_list.length; i++){
        lnglat_list.push(WP_list[i][0]);
    }
    if(map.getSource("route")){
        map.getSource('route').setData({
          'type': 'geojson',
          'data': {
              'type': 'Feature',
              'properties': {},
              'geometry': {
                  'type': 'LineString',
                  'coordinates': lnglat_list
        }}}.data)
    }else{
	    map.addSource('route', {
	        'type': 'geojson',
	        'data': {
	            'type': 'Feature',
	            'properties': {},
	            'geometry': {
	                'type': 'LineString',
	                'coordinates': lnglat_list
	            }
	        }
	    });
	    map.addLayer({
	        'id': 'route',
	        'type': 'line',
	        'source': 'route',
	        'layout': {
	            'line-join': 'round',
	            'line-cap': 'round'
	        },
	        'paint': {
	            'line-color': 'yellow',
	            'line-width': 3
	        }
	    });
	}
	sub_markers.forEach(function(marker) {
		marker.remove();
	})
	if(WP_list.length<9){
		for (let i=1; i<WP_list.length-1; i++){
			create_submarker(i)
	}}
}

function reset_markers(){
	markers.forEach(function(marker) {
		marker.remove();
	});
	for(let j=1; j<WP_list.length; j++){
		create_marker(j);
	}
	sub_markers.forEach(function(marker) {
		marker.remove();
	})
	if(WP_list.length<9){
		for (let i=1; i<WP_list.length-1; i++){
			create_submarker(i)
	}}
	close_point_tab();
	edit_event();//編集操作のカウント
}

function create_submarker(id) {
  const template = document.getElementById('sub_marker');
  const clone = document.importNode(template.content, true);
  let el = clone.firstElementChild;
  el.addEventListener('mouseover', () => {
    marker_hover_flg=true;
  });
  el.addEventListener('mouseout', () => {
    marker_hover_flg=false;
  });
  let lnglat=[
	(WP_list[id][0][0]+WP_list[id+1][0][0])/2,
	(WP_list[id][0][1]+WP_list[id+1][0][1])/2
  ]
  el.id=id;
  el.addEventListener('click', () => {
      if(WP_list.length<=9){
		if(add_marker_flg!=true){
	      close_point_tab()
	      subMarker_to_WPmarker(id);
	      edit_event();
		}
	}
  });
  // add marker to map
  sub_marker = new mapboxgl.Marker(el)
    .setLngLat(lnglat)
    .addTo(map)
  sub_markers[id]=sub_marker;
};

//サブマーカーをマーカーへ昇格させるイベント
function subMarker_to_WPmarker(id){
  let new_WP_list=[];
  const add_lngLat = [
	(WP_list[id][0][0]+WP_list[id+1][0][0])/2,
	(WP_list[id][0][1]+WP_list[id+1][0][1])/2
  ]
  const add_WPdata=[//サブマーカーをマーカにする際に入れるデータ WP間なので速度なども中間値とる？
        add_lngLat,
        Number($("#speed").val()),
        Number($("#altitude").val()),
    ]
  for(let i=0; i<WP_list.length; i++){
    new_WP_list.push(WP_list[i])
    if(i==id){
	  new_WP_list.push(add_WPdata)
    }
  }
  
  WP_list.splice(0)
  WP_list=new_WP_list
  reset_markers()
  //console.log(WP_list)
  //追加したWPのタブを開く
  let target =document.getElementsByClassName("WP_marker")
  target[id].style.backgroundColor="orange"
  open_point_tab(id+1,'waypoint');
}


//編集確認時イベント 保存ボタンの有効化、ページ遷移時警告の有効化
function edit_event(){
	page_chenge_alert=true;
	$("#saveicon").css('pointer-events', '').css("background-color", "#ffffff");
	//WPの数を確認
    if(WP_list.length<=2){//WPが１つで削除制限
		$("#WP_remove_button").prop('disabled', true);
	}else{
		$("#WP_remove_button").prop('disabled', false);
		if(WP_list.length>=9){//WPが８個で追加制限
			$("#add_icon").css('pointer-events', 'none').css("background-color", "#e0e0e0");
		}else{
			$("#add_icon").css('pointer-events', '').css("background-color", "#ffffff");
		}
	}
}

//ルートの保存とデータの整形
var saved_WP_list = [];
var saved_WP_num;
function save_event(){
	const WP_list_copy = Array.from(WP_list);
	saved_WP_list = []
	// WPごとに [[ 緯度, 経度 ], 高度 , 速度]のリストにしてまとめる
	for (let i=0; i<WP_list_copy.length-1; i++){
		saved_WP_list.push([
			[WP_list_copy[i+1][0][1], WP_list_copy[i+1][0][0]],
			WP_list_copy[i+1][2],
			WP_list_copy[i+1][1]
		])
	}
	
	saved_WP_num=saved_WP_list.length;
	var toJSON_WP_list = {
		"WP_num":saved_WP_num,
		"command":"GOTO"
	}
	for(let j=0; j<saved_WP_num; j++){
		let WP_data={
			"lat":saved_WP_list[j][0][0],
			"lon":saved_WP_list[j][0][1],
			"alt":saved_WP_list[j][1],
			"speed":saved_WP_list[j][2]
		}
		toJSON_WP_list["WP_data"+j]=WP_data
		//console.log(toJSON_WP_list)
	}
	console.log(toJSON_WP_list)
	json_WP_data = JSON.stringify(toJSON_WP_list);     // JSON型にする
	
	send_message(json_WP_data)
	
	pagechange(WP_list_copy,$('#mission_complete').val(), $('#interruption').val())
}

function send_message(msg) {
	// JSON型にしてからMQTTでPublishする
	message = new Paho.MQTT.Message(msg);      // MQTTのメッセージパケットを作る
	message.destinationName = "ctrl/001";   // トピック名を設定
	client.send(message);   // MQTTでPubする
	console.log("SEND ON " + message.destinationName + " PAYLOAD " + message.payloadString)
	// debug("SEND ON " + message.destinationName + " PAYLOAD " + message.payloadString);   //debugボックスに表示
	}
	

//==============MQTT over WebSocketの設定・初期化・接続==========================
// MQTT over WebSocketの初期化
var wsbroker = location.hostname;   // MQTTブローカーは自分自身
var wsport = 15675; // MQTTの標準ポート番号は1883だが，WebSocketは15675とした(RabbitMQと同じ仕様)
var clientId = "myclientid_" + parseInt(Math.random() * 100,10)//クライアントID名はランダムに作る

var client = new Paho.MQTT.Client(wsbroker, Number(wsport), "/ws", clientId);// MQTTのクライアントを作成する

// コールバックの設定
client.onConnectionLost = onConnectionLost;
//client.onMessageArrived = onMessageArrived;
	

// MQTTの接続オプション
var options = {
	timeout: 3,
	onSuccess: function () {
		// debug("CONNECTION SUCCESS");
		client.subscribe('drone/#', {qos: 1});
	},
	onFailure: function (message) {
		console.log("CONNECTION FAILURE - " + message.errorMessage);
	}
};
// サーバーがHTTPS対応だった時の処理
if (location.protocol == "https:") {
	options.useSSL = true;
}
// 最初にメッセージを表示してMQTTをブローカーに接続
	console.log("CONNECT TO " + wsbroker + ":" + wsport);
	client.connect(options);        // 接続


// 切断時のコールバック
function onConnectionLost(responseObject) {
	if (responseObject.errorCode !== 0) {
		console.log("onConnectionLost:"+responseObject.errorMessage);
	}
}

// メッセージ受信時のコールバック
/*function onMessageArrived(message) {
	console.log("onMessageArrived:"+message.payloadString);
}*/
//=======================================================================



//アップロード成功で操作画面に画面移動(予定)
function pagechange(saved_WP_list,missionCompleteAction,missionControl){
	let flight_route={
		"aircraftName": "Drone/001",  //パケット名
		"missionControl": missionControl,  //中断時動作
		"missionCompleteAction":missionCompleteAction,  //完了時動作
		"centerLngLat":map.getCenter(),//地図中心
		"mapZomm":map.getZoom(),  //ズームレベル
		"routeCoordinates": [],  //WPルートの頂点座標
	}
	let lnglat_list=[];
	for(let i=1; i<WP_list.length; i++){
		lnglat_list.push(saved_WP_list[i][0]);
	}
	flight_route['routeCoordinates']=lnglat_list;
	let flight_route_json =JSON.stringify(flight_route)
	
	sessionStorage.setItem("flightRoute",flight_route_json) //WPのリスト？
	location.href="../html/flight_operate.html"
}
