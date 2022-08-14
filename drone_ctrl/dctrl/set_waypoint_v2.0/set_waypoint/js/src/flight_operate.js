//const LTE_SIGNAL_STRENGTH = { "1": "弱い", "2": "弱い", "3": "良", "4": "強い", "5": "強い" };
//const FLIGHT_PLAN_APPY_STATUS =  { "0": "未申請", "1": "申請中", "2": "承認済", "3": "要修正", "4": "取下中" };


const MISSION_STATUS = {
	"OVER":1,
	"BREAK":2,
	"RESUME":3,
	"RETURN_HOME":4,
	"EMERGENCY_LANDING":5
};// ミッションのステータス

const MISSION_CONTROL_NAME = {
	"1":"ホーム帰還",
	"2":"緊急着陸",
	"3":"ミッション再開",
};// ミッション中断時の操作名

/////////// ワイプ・マップ切り替え用 start//////////////////
const SMALL_MAP_WIDTH = '370px';// 小サイズマップの長さ(px)
const SMALL_MAP_HEIGHT = '180.3px';// 小サイズマップの高さ(px)
var bigMapWidth;// 大サイズマップの長さ(px)
var bigMapHeight;// 大サイズマップの高さ(px)
var mapCanvasWidthBig;
var mapCanvasHeightBig;
var bigMapZoom;
/////////// ワイプ・マップ切り替え用 end//////////////////

var centerLngLat;// 地図の中心位置
var routeSelectedFlg = false;
var geoCnt = 0;// 描画したジオフェンス数.
var geoCoordinates = [];// 選択したフライトルートのジオフェンス座標リスト
var mission_ready = false;
var mission_complete = false;


var routePointIndex = 0;// 飛行中ルートのポイントインデクス
var initDroneLngLat; // 初期表示ドローン経緯度
var initMapFlg = false;

const FLIGHT_ROUTE_SRC = "flightRoute";
const FLIGHT_ROUTE_LAYER = "routeOutline";

const geojsonFlightRoute = {// フライトルート表示用ソース
	'type': 'Feature',
	'properties': {
		'map_size_type': 'big'
	},
	'geometry': {
		'type': 'LineString',
		'coordinates': []
	}
};
var flightRoute;
var flight_path=[];//飛行経路保存用リスト
var drones=new Array();   // 緯度経度などの受信したデータを保存する連想配列




$(function() {
	flightRoute=JSON.parse(sessionStorage.getItem('flightRoute'));

	
	// イベント設定
	setEvent();
	
	// マップをロード
	map.on('load', function () {
		loadMap();
	})
	console.log(MISSION_CONTROL_NAME[flightRoute['missionControl']])
	setMissionControlBtn(MISSION_CONTROL_NAME[flightRoute['missionControl']]);
});


// イベント設定
function setEvent() {
	// 画面の「離陸準備」ボタン押下
	$('#mission_ready').click(function() {
		flightReady();
	});
	// 画面の「ミッション実行」ボタン押下
	$('#mission_execute').click(function() {
		flightExecuteConfirm();
	});
	// 画面の「ミッション中断」ボタン押下
	$("#mission_break").click(function(){
		var modalbody =
			`
			<div class="text-center mt-4">
			<span >ミッション中断します。<br>よろしいですか。</span>
			</div>
			`;
		//モーダルに表示
		$('#modal-confirm-body').html(modalbody);
		$('#execute').text("OK");
		$('#modal-confirm-body').removeClass("modal-body");
		$('#modal-confirm').modal('toggle');
	});
	
	// ホーム帰還オプションを選択
	$("#mission_rth").click(function() {
		setMissionControlBtn(MISSION_CONTROL_NAME['1']);
	});
	// 緊急着陸オプションを選択
	$("#mission_el").click(function() {
		setMissionControlBtn(MISSION_CONTROL_NAME['2']);
	});
	// ミッション再開オプションを選択
	$("#mission_fr").click(function() {
		setMissionControlBtn(MISSION_CONTROL_NAME['3']);
	});
	
	// ミッション制御
	$('#mission_control').click(function() {
		console.log('ミッション制御:', $(this).text());
		if ($(this).text() == MISSION_CONTROL_NAME['1']) {
			buttonDisplayControl(MISSION_STATUS.RETURN_HOME);
		} else if ($(this).text() == MISSION_CONTROL_NAME['2']) {
			buttonDisplayControl(MISSION_STATUS.EMERGENCY_LANDING);
		} else if ($(this).text() == MISSION_CONTROL_NAME['3']) {
			buttonDisplayControl(MISSION_STATUS.RESUME);
		}
	});
	
	// ダイアログの実行ボタン押下
	$('#execute').click(function() {
		switch ($(this).text()) {
			case 'フライト実行':
				excuteFilght(false);
				break;
			default:
				break;
		};
	});

	// ミッション中断確認ダイアログ「はい」ボタン押下
	$('#dialog_ok').click(function() {
		buttonDisplayControl(MISSION_STATUS.BREAK);
	});

	// 映像・地図表示切り替え
	$("#wipeMapDisplayControl").click(function() {
		// 地図：大サイズ、かつ映像：小サイズの場合
		if (($("#map").attr("class") == 'mapboxgl-map') && $("#fl-video").attr("class") == "fl-video-normal") {
			// 映像を非表示にする
			$("#fl-video").toggleClass("d-none");
			
		} else if($("#fl-video").attr("class") == "fl-video-normal fl-video-big-x") {
			// 地図の表示・非表示を制御
			$("#map").toggleClass("d-none");
		} else if($("#fl-video").attr("class") == "fl-video-normal d-none") {
			// 映像を表示にする
			$("#fl-video").toggleClass("d-none");
		}
		
		if ($("#wipeMapDisplayControl").attr("class") == "arrow-right-rotate") {
			$("#wipeMapDisplayControl").removeClass("arrow-right-rotate");
			$("#wipeMapDisplayControl").addClass("arrow-left-rotate");
			$("#wipeMapDisplayControl").css('top','93px');
		} else {
			$("#wipeMapDisplayControl").removeClass("arrow-left-rotate");
			$("#wipeMapDisplayControl").addClass("arrow-right-rotate");
			if ($("#fl-video").attr("class") == "fl-video-normal") {
				$("#wipeMapDisplayControl").css('top','269px');
			} else {
				$("#wipeMapDisplayControl").css('top','238px');
			}
		}
	});
	
	// 映像をクリック
	$("#video-element").click(function() {
		// 地図を表示している場合のみ
		if ($("#map").attr("class") != "mapboxgl-map d-none") {
			switchMapWipeSize();
		}
	});
}


// マップをロード
function loadMap() {
	// マップをクリック
	map.on('click', function(e) {
		// 地図を小サイズで表示している場合のみ
		if ($("#map").attr("class") == "mapboxgl-map" && $("#fl-video").attr("class") == "fl-video-normal fl-video-big-x") {
			switchMapWipeSize();
		}
	});
	
	// ドローンがオンラインの場合、映像を表示する MQTT over websoket接続時の位置に移動
	
	mapCanvasWidthBig = $('.mapboxgl-canvas')[0].style.width;
	mapCanvasHeightBig = $('.mapboxgl-canvas')[0].style.height;
	bigMapZoom = map.getZoom();
	
	bigMapWidth = $("#map").css('width');
	bigMapHeight = $("#map").css('height');
}

// マップ・ワイプ（小サイズ⇔大サイズ）表示の切り替え
function switchMapWipeSize() {
	// 小サイズマップ⇒大サイズマップに変更
	if ($("#map").css('width') != SMALL_MAP_WIDTH && $("#map").css('height') != SMALL_MAP_HEIGHT && $("#map").css('left') == '0px') {
		$('#map').css({ "width": `${SMALL_MAP_WIDTH}`, "height": `${SMALL_MAP_HEIGHT}`, "left": "75.9%", "z-index": "2" });
	} else {
		$('#map').css({ "width": `${bigMapWidth}`, "height": `${bigMapHeight}`, "left": "0px", "z-index": "2" });
	}
	$("#fl-video").toggleClass("fl-video-big-x");
	map.resize();
	
	if ($("#fl-video").attr("class") == "fl-video-normal fl-video-big-x") {
		$("#wipeMapDisplayControl").css('top','238px');
	} else {
		$("#wipeMapDisplayControl").css('top','269px');
	}
}

// ミッション制御ボタンの色と名称を設定
function setMissionControlBtn(missionControlName) {
	switch (missionControlName) {
		case MISSION_CONTROL_NAME['1']:
			$('#mission_control').text(MISSION_CONTROL_NAME['1']);
			if ($('#mission_control').attr('class') != 'btn btn-primary') {
				$('#mission_control').removeClass();
				$('#mission_control_dropdown').removeClass();
				$('#mission_control').addClass('btn btn-primary');
				$('#mission_control_dropdown').addClass('btn btn-primary dropdown-toggle dropdown-toggle-split border-left');
			}
			break;
		case MISSION_CONTROL_NAME['2']:
			$('#mission_control').text(MISSION_CONTROL_NAME['2']);
			if ($('#mission_control').attr('class') != 'btn btn-danger') {
				$('#mission_control').removeClass();
				$('#mission_control_dropdown').removeClass();
				$('#mission_control').addClass('btn btn-danger');
				$('#mission_control_dropdown').addClass('btn btn-danger dropdown-toggle dropdown-toggle-split border-left');
			}
			break;
		case MISSION_CONTROL_NAME['3']:
			$('#mission_control').text(MISSION_CONTROL_NAME['3']);
			if ($('#mission_control').attr('class') != 'btn btn-success') {
				$('#mission_control').removeClass();
				$('#mission_control_dropdown').removeClass();
				$('#mission_control').addClass('btn btn-success');
				$('#mission_control_dropdown').addClass('btn btn-success dropdown-toggle dropdown-toggle-split border-left');
			}
			break;
		default:
			break;
	}
}

// マップ表示(フライトルート)  ジオフェンスは一旦なし
function showMapWithRoute(start_lat,start_lon) {
	let routeCoordinates = [];
	let mapZoom = 0;
	if(flightRoute != ""){
		centerLngLat = flightRoute['centerLngLat'];
		mapZoom = flightRoute['mapZoom'];
		
		// ミッション中断後のボタン名を設定
		setMissionControlBtn(MISSION_CONTROL_NAME[flightRoute['missionControl']]);
	
		/*ジオフェンスのデータの持ち方がわからないので書き直しになると思う
		// フライトルートを再選択する前ジオフェンス数を保存する
		geoCnt = geoCnt == 0  ? flightRoute['geofenceIdList'].length : geoCoordinates.length;
		geoCoordinates = [];
		// ジオフェンス座標取得
		flightRoute['geofenceIdList'].forEach((geoId) => {
			JSON.parse(sessionStorage.getItem('geofenceInfoList')).forEach((geoInfo) => {
				if (geoInfo['geofenceId'] == geoId) {
					geoCoordinates.push(geoInfo['geofenceCoordinates']);
				}
			})
		});*/
	
		// フライトルート座標取得
		routeCoordinates.push([start_lon,start_lat]) //開始地点の追加
		routeCoordinates.push(flightRoute['routeCoordinates']);
		if(flightRoute['missionCompleteAction'=="RTH"]){ //完了時動作がホーム帰還の時ホームまでの経路も追加
			routeCoordinates.push([start_lon,start_lat])
		}
		
		if(lnglat_list==false){
			map.setCenter(centerLngLat);
			if (mapZoom > 0) {
				map.setZoom(mapZoom);
			}
		}
	}
	
	// フライトルートとジオフェンスを描画するメソッド
	function addRouteGeofencePolygon() {
		/* //ジオフェンスの描画
		$.each(geoCoordinates, function(index, geoCoordinate) {
			map.addSource('geofence' + index, {
				'type': 'geojson',
				'data': {
					'type': 'Feature',
					'geometry': {
						'type': 'Polygon',
						'coordinates': [geoCoordinate]
					}
				}
			});
			map.addLayer({
				'id': 'geofenceFill' + index,
				'type': 'fill',
				'source': 'geofence' + index,
				'layout': {},
				'paint': {
					'fill-color': '#ffff00',
					'fill-opacity': 0.5
				}
			});
		}); */
		geojsonFlightRoute.geometry.coordinates = routeCoordinates;
		map.addSource(FLIGHT_ROUTE_SRC, {
			'type': 'geojson',
			'data': geojsonFlightRoute
		});
		
		map.addLayer({
			'id': FLIGHT_ROUTE_LAYER,
			'type': 'line',
			'source': FLIGHT_ROUTE_SRC,
			'layout': {},
			'paint': {
				'line-color': '#3061b2',
				'line-width': 3
			}
		});
		initMapFlg = true;
	}
	// ドローン飛行ルートを作る
	if (routeSelectedFlg) {
		/*  let i = 0;
		while(i< geoCnt) {
			if (map.getLayer("geofenceFill" + i)) {
				map.removeLayer("geofenceFill" + i);
			}
			if (map.getSource("geofence" + i)) {
				map.removeSource("geofence" + i);
			}
			i++;
		}  */

		if (map.getLayer(FLIGHT_ROUTE_LAYER)) {
			map.removeLayer(FLIGHT_ROUTE_LAYER);
		}

		if (map.getSource(FLIGHT_ROUTE_SRC)) {
			map.removeSource(FLIGHT_ROUTE_SRC);
		}
		addRouteGeofencePolygon();
		
		// ドローンアイコンをフライトルートの上に移動する
		//map.moveLayer(FLIGHT_ROUTE_LAYER, DRONE_ICON_LAYER);
	} else {
		map.on('load', addRouteGeofencePolygon);
	}
}


// 画面のボタン表示・非表示の制御
function buttonDisplayControl(missionStatus) {
	switch (missionStatus) {
		case MISSION_STATUS.OVER:
			// ドローンが捉えている映像を消す
			$('#alert_area').css('display', 'none');
			//ミッション実行ボタン:表示 ミッション中断ボタン:非表示
			$('#mission_break_btn_group').addClass("d-none");
			$('#mission_break').addClass("d-none");
			$('#mission_execute').removeClass("d-none");

			// 初期表示に戻る
			$('#mission_execute').prop('disabled', false);
			$('#mission_execute').removeClass();
			$('#mission_execute').addClass("btn btn-success rounded ml-4 mt-2");
			$("#flight_route_select").css('pointer-events', 'auto');
			setMissionControlBtn(MISSION_CONTROL_NAME[flightRoute['missionControl']]);
			break;
		case MISSION_STATUS.BREAK:  //ミッション中断
			if (mission_complete==false) {
				// ミッション中断ボタン:非表示 
				$('#mission_break').addClass("d-none");
				// ミッション中断時処理選択ボタン:表示
				$('#mission_break_btn_group').removeClass("d-none");
				$('#mission_break_btn_group').prop('disabled', false);
				$('#mission_control').prop('disabled', false);
				$('#mission_control_dropdown').prop('disabled', false);
				
				MQQTT_publish("MISSION_BREAK_HOVERING")
				
			} else { // ミッション終了後にミッション中断できない
				buttonDisplayControl(MISSION_STATUS.OVER);

			}
			break;
		case MISSION_STATUS.RESUME:  //ミッション再開
			// ミッション中断ボタン:表示  ミッション中断時処理選択ボタン:非表示
			$('#mission_break').removeClass("d-none");
			$('#mission_break_btn_group').addClass("d-none");;
			//ミッション中断＞ミッション再開の時の処理 ここから
			
			MQQTT_publish("MISSION_RESUME")
			
			break;
		case MISSION_STATUS.RETURN_HOME:  //ホームに帰還
			//ミッション実行ボタン:表示 ミッション中断ボタン:非表示
			$('#mission_break_btn_group').prop('disabled', true);
			$('#mission_control').prop('disabled', true);
			$('#mission_control_dropdown').prop('disabled', true);
			$('#mission_break').addClass("d-none");
			$('#mission_execute').addClass("d-none");
			$("#flight_route_select").css('pointer-events', 'none');
			//ミッション中断＞RTHの時の処理  ここから
			
			MQQTT_publish("MISSION_STOP_RTL")
			break;
		/* 緊急着陸は実装しない
		case MISSION_STATUS.EMERGENCY_LANDING:
			//ミッション実行ボタン:表示 ミッション中断ボタン:非表示
			$('#mission_break_btn_group').prop('disabled', true);
			$('#mission_control').prop('disabled', true);
			$('#mission_control_dropdown').prop('disabled', true);
			$('#mission_break').addClass("d-none");
			$('#mission_execute').addClass("d-none");
			$("#flight_route_select").css('pointer-events', 'none');
			//ミッション中断＞緊急着陸の時の処理  ここから
			break;
		*/
		default:
			break;
	}
}

function flightReady() {
	$('#mission_execute').prop('disabled', false);
	window.alert("Send ARM comand");
	MQQTT_publish("ARM");
}

// フライト実行確認ダイアログ
function flightExecuteConfirm() {
	//機体のアラートがある場合は非活性とする  アラートチェックは一時削除 飛行準備のチェックがいるならここでする
	let checked_text=""
//	if(mission_ready != true){
//		checked_text = `<td class="text-danger"><i class="fas fa-times-circle ml-1"></i>ARM</td>
//						<td class="">NG</td>`
//		$('#execute').prop('disabled', true);
//	}else{
		checked_text = `<td class="text-success"><i class="fas fa-check-circle fa-lg ml-1"></i>ARM</td>
						<td class="">OK</td>`
		$('#execute').prop('disabled', false);
//	}
	
	//ミッション実行確認モーダル
	var modalbody ="<table cellspacing=0  align='center' class='table table-borderless' style='width:90%' ><tr >";
	modalbody = modalbody + checked_text;
	modalbody = modalbody +`</tr></table><div class="text-center mt-4">
			<span>ミッションを実行します。よろしいですか？</span>
			</div>`;
	//モーダルに表示
	$('#modal-title').text('フライト確認');
	$('#modal-title').addClass('w-100 text-center mt-2');
	$('#modal >.modal-dialog').addClass('modal-lg');
	$('#modal .mt-4.mb-4.position-relative').css("left","28%");
	$('#modal-body').html(modalbody);
	$('#execute').text("フライト実行");
	$('#modal').modal('show');
}

// フライト実行
function excuteFilght(isInit) {
	//ミッション実行ボタン:非表示 ミッション中断ボタン:表示
	$('#mission_ready').addClass("d-none");
	$('#mission_execute').addClass("d-none");
	$('#mission_break').removeClass("d-none");

	// ドローンが捉えている映像を表示
	if ($('#fl-video').css('display') == 'none') {
		$('#fl-video').css('display', 'block');
	}
	$('#alert_area').css('display', 'block');
	$("#wipeMapDisplayControl").css('display', 'block');
	if (!isInit) {
		$('#modal').modal('toggle');
	}
	MQQTT_publish("TAKEOFF")
}



// ##############################################################################



//==============MQTT over WebSocketの設定・初期化・接続==========================

//function init_MQTT(){
	// MQTT over WebSocketの初期化
	//var wsbroker = location.hostname;   // MQTTブローカーは自分自身
	var wsbroker = "127.0.0.1";   
	var wsport = 15676; // MQTTの標準ポート番号は1883だが，WebSocketは15675とした(RabbitMQと同じ仕様)
	var clientId = "myclientid_" + parseInt(Math.random() * 100,10)//クライアントID名はランダムに作る
	
	var client = new Paho.MQTT.Client(
		wsbroker, 
		Number(wsport), 
		"/ws", 
		clientId
		);// MQTTのクライアントを作成する
	
	// コールバックの設定
	client.onConnectionLost = onConnectionLost;
	client.onMessageArrived = onMessageArrived;
	
	
	// MQTTの接続オプション
	var options = {
		timeout: 3,
		onSuccess: function () {
			// debug("CONNECTION SUCCESS");
			client.subscribe('drone/#', {qos: 1});  //subscribe(受信)するトピック
			MQTTconnect(true)
		},
		onFailure: function (message) {
			console.log("CONNECTION FAILURE - " + message.errorMessage);
			MQTTconnect(false)
		}
	};
	// サーバーがHTTPS対応だった時の処理
	
	if (location.protocol == "https:") {
		options.useSSL = true;
	}
	
	// 最初にメッセージを表示してMQTTをブローカーに接続
	console.log("CONNECT TO " + wsbroker + ":" + wsport);
	client.connect(options);        // 接続
//}


// 切断時のコールバック
function onConnectionLost(responseObject) {
	if (responseObject.errorCode !== 0) {
		console.log("onConnectionLost:"+responseObject.errorMessage);
		
	}
}


//// メッセージ受信時のコールバック start
function onMessageArrived(message) {
	console.log("RECEIVE ON " + message.destinationName + " PAYLOAD " + message.payloadString)
	
	let drone_name = message.destinationName;   // ドローン名はトピック名とする
	var drone_data = JSON.parse( message.payloadString );   // ドローンのデータを連想配列にして格納
	
	let arm = drone_data.status.Arm;           // ARM/DISARM
	let mode  = drone_data.status.FlightMode;    // フライトモード
	let lat  = parseFloat( drone_data["position"]["latitude"] );   // 緯度
	let lon  = parseFloat( drone_data["position"]["longitude"] );  // 経度
	let alt  = parseFloat( drone_data["position"]["altitude"] );   // 高度
	let ang  = parseFloat( drone_data["position"]["heading"] );    // 方位
	console.log("11111");
	write_drone(lat,lon,ang)//ドローン描画
	flight_path.push([lon,lat]) //飛行経路描画用のリストに追加
	write_flight_path()//飛行経路の描画
	console.log("22222");
	
	/////////////////表示情報の更新 ここから///////////////////////
	// 機体名が空->表示中の機体名の更新  ある->何もしない
	if( $('#aircraftName').text === "" ) {
		$('#aircraftName').text(drone_name);
	}
	$('#flightLat').text(lat.toFixed(4));  //緯度経度
	$('#flightLng').text(lon.toFixed(4));  //緯度経度
	$('#flightHeight').text(alt.toFixed(2) + "m");  //高度
	//$('#flightSpeed').text(speed.toFixed(2) + "m/s");  //速度  速度があるかわからなかったのでコメントアウト中
	$('#flightAngle').text(ang.toFixed(2) + "度");  //方位
	

	console.log("333333");


	//電波強度などの更新  データ形式など不明なのでコメントアウト
	//show_sidber_flight_info(drone_data)
	
	//飛行前の場合 現在の位置に応じてルートの描画を更新(離陸地点が変わるため)
	//// if(mission_ready==false){
	//// 	showMapWithRoute(lat,lon)
	//// 	if(mode=="ARM"){  //離陸準備の確認（仮） これ以外に確認する事項があれば要追加  441行あたりのfunction flightExecuteConfirm()もセットで修正
	//// 		mission_ready=true
	//// 	}
	//// }
	

	console.log("444444");


	/////////////////表示情報の更新 ここまで///////////////////////
	
	drones[drone_name] = drone_data; // ドローンデータ用連想配列の情報を最新のメッセージに更新
}
///// メッセージ受信時のコールバック end


//==============メッセージ送信==============
//各操作の際に送るMQTTメッセージ  それっぽいのをmap_r_click.htmlから持ってきただけなので多分修正がいる
var MQTT_comand= {
	//離陸準備の時(ミッション開始を２段階に分けたときの１段階目)
	"ARM":{
		"command":"ARM",
		"d_lat":"0",
		"d_lon":"0",
		"d_alt":"0",
	},
	//ミッション開始(ミッション開始を２段階に分けたときの２段階目)
	"MISSION_START":{ 
		"command":"TAKEOFF",
		"d_lat":"0",
		"d_lon":"0",
		"d_alt":"0",
	},
	//ミッション中断
	"MISSION_BREAK_HOVERING":{
		"command":"PAUSE",
		"d_lat":"0",
		"d_lon":"0",
		"d_alt":"0",
	},
	//ミッション中断＞ホーム帰還の時
	"MISSION_STOP_RTL":{
		"command":"RTL",
		"d_lat":"0",
		"d_lon":"0",
		"d_alt":"0",
	},
	//ミッション中断＞ミッション再開の時
	"MISSION_RESUME":{
		"command":"RESUME",
		"d_lat":"0",
		"d_lon":"0",
		"d_alt":"0",
	}
}
function MQQTT_publish(str){	
	let msg=MQTT_comand[str]
	
	message = new Paho.MQTT.Message(msg);      // MQTTのメッセージパケットを作る
	message.destinationName = "ctrl/001";   // トピック名を設定
	client.send(message);   // MQTTでPubする
	console.log("SEND ON " + message.destinationName + " PAYLOAD " + message.payloadString)
	// debug("SEND ON " + message.destinationName + " PAYLOAD " + message.payloadString);   //debugボックスに表示
}
//=================メッセージ送信=====================================

//ドローンの描画
function write_drone(lat,lon,ang){
	if(!$('div').hasClass('drone_marker')){//ドローンのマーカーがないとき、新しく作る
		console.log("1")
		const el = document.createElement('div');
		console.log("2")
		el.className = 'drone_marker';
		console.log("3")
		////elDiv.id = 'droneIcon';
		console.log("4")
		//// drone_marker = new mapboxgl.Marker(el)
		//// 	.setLngLat([lon, lat])
		//// 	.setRotation(ang)
		//// 	.addTo(map);  //マーカーをマップに追加
		map.setCenter([lon, lat]) //初期表示時にドローンをマップ中心にする？
	}else{
		drone_marker.set.setLngLat([lon, lat])
		drone_marker.setRotation(ang)
	}
}

//MQTTの接続状態に応じてボタンなどの有効化切り替え
function MQTTconnect(MQTTconect){
	if(MQTTconect){//MQTT接続時処理
		$('#fl-video').css('display', 'block');
		$("#wipeMapDisplayControl").css('display', 'block');
	}else{MQTT切断時処理
		//(仮)ドローンとの接続切断時、映像表示を消す
		$('#fl-video').css('display', 'none');
		$("#wipeMapDisplayControl").css('display', 'none');
	}
}

//ドローンの軌跡の描画
function write_flight_path(){
	if(map.getSource("flight_path")){//２回目以降 ソースの更新
		map.getSource('flight_path').setData({
			'type': 'geojson',
			'data': {
			'type': 'Feature',
				'properties': {},
				'geometry': {
					'type': 'LineString',
					'coordinates': flight_path
		}}}.data)
	}else{//初回描画 ソースとレイヤーを作成
		map.addSource('flight_path', {
			'type': 'geojson',
			'data': {
				'type': 'Feature',
				'properties': {},
				'geometry': {
					'type': 'LineString',
					'coordinates': flight_path
				}
			}
		});
		map.addLayer({
			'id': 'flight_path',
			'type': 'line',
			'source': 'flight_path',
			'layout': {},
			'paint': {
				'line-color': 'red',
				'line-width': 3,
			}
		});
	}
}
function show_sidber_flight_info(drone_data){ 
	//////// テレメトリ情報表示 ////////
	// 電波強度
	$('#LTESignalStrength').text(LTE_SIGNAL_STRENGTH[drone_data['LTESignalStrength']]);
	if (Number(drone_data['LTESignalStrength']) <= 2) {
		$('#LTESignalStrengthLine').addClass("telemetry-danger");
	} else {
		$('#LTESignalStrengthLine').addClass("telemetry-normal");
	}
	
	// 電池残量
	$('#batteryRemaining').text(new Intl.NumberFormat('ja', { style: 'percent' }).format(drone_data['batteryRemaining']));
	if (Number(drone_data['batteryRemaining']) <= 0.3) {
		$('#batteryRemainingLine').addClass("telemetry-danger");
	} else {
		$('#batteryRemainingLine').addClass("telemetry-normal");
	}
	
	// GPS接続数
	$('#GPSSatellitesCnt').text(drone_data['GPSSatellitesCnt']);
	if (Number(drone_data['GPSSatellitesCnt']) <= 2) {
		$('#GPSSatellitesCntLine').addClass("telemetry-danger");
	} else {
		$('#GPSSatellitesCntLine').addClass("telemetry-normal");
	}
	// RTK接続数
	$('#RTKStatus').text(drone_data['RTKStatus']);
	if (Number(drone_data['RTKStatus']) <= 2) {
		$('#RTKStatusLine').addClass("telemetry-danger");
	} else {
		$('#RTKStatusLine').addClass("telemetry-normal");
	}
}
