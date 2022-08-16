
mapboxgl.accessToken = 'pk.eyJ1IjoibGl1d2FubGkiLCJhIjoiY2tzczloYXhqMHVtZTJucHVndGo1cHA2bSJ9.77f8qFnHHiNSUTaLCKFZGg';
// マップ作成
var map = new mapboxgl.Map({
  container: 'map',
  zoom: 15,
  center:  [139.75715946670445, 35.65540359784979],
  style: 'mapbox://styles/mapbox-map-design/ckhqrf2tz0dt119ny6azh975y',
});

//気象情報表示
map.on("move",function(){
	display_wether()
})
display_wether()

function display_wether(){
  if($("div").hasClass("wether_panel")){
    let width = map.getContainer().offsetWidth/2
    const height = map.getContainer().offsetHeight/2
    if(!$('.sidebar_left').hasClass('sidebar_leftc')){
      width+=110  //サイドバーが開いているとき地図中心点を移動
    }
    const center_by_pixel = map.unproject([width, height]);
    let wether ="fas fa-cloud"
    let temperature = 27;
    let wind = 1.0;
    //緯度経度を表示しているがリバースジオコーディングして市区町村の表示をするが良いと思う
    $(".location").empty();
    $(".location").append("<span id=''langlat'>"+ center_by_pixel.lat.toFixed(4) +","+ center_by_pixel.lng.toFixed(4) +"</span>");
    $(".wether").empty();
    $(".wether").append("<span id=wether_icon><i class=' "+ wether +" fa-2x'></i></span>");
    $(".temperature").empty();
    $(".temperature").append("<span id='temperature'>" + temperature + "℃</span>");
    $(".wind").empty();
    $(".wind").append("<span id='wind'>風速<br>" + wind + "m/s</span>");
  }
}

// レイヤ切り替え
$("#layer_terrain").click(function() {
	 //map.setStyle('mapbox://styles/mapbox/satellite-streets-v11');
	switchBaseMap(map, 'mapbox-map-design/ckhqrf2tz0dt119ny6azh975y');
	$("#btn_layer").css('background', 'no-repeat url(../img/layer.png)');
	$("#btn_layer").css('background-position', 'center');
	$("#btn_layer").css('background-size', '90%');
});
$("#layer_traffic").click(function() {
	 //map.setStyle('mapbox://styles/mapbox/navigation-day-v1');
	switchBaseMap(map, 'mapbox/navigation-day-v1');
	$("#btn_layer").css('background', 'no-repeat url(../img/layer_item_traffic.png)');
	$("#btn_layer").css('background-position', 'center');
	$("#btn_layer").css('background-size', '90%');
});

$("#layer_transit").click(function() {
	 //map.setStyle('mapbox://styles/mapbox/streets-v11');
	switchBaseMap(map, 'mapbox/streets-v11');
	$("#btn_layer").css('background', 'no-repeat url(../img/layer_item_transit.png)');
	$("#btn_layer").css('background-position', 'center');
	$("#btn_layer").css('background-size', '90%');
});

$("#layer_did").click(function() {
	// DID飛行禁止エリア表示
	let polygonOffset = [map.getCenter().lng + 0.008, map.getCenter().lat];
	let point1 = [polygonOffset[0] + 0.0008, polygonOffset[1] + 0.0008];
	let point2 = [polygonOffset[0] - 0.0008, polygonOffset[1] + 0.0008];
	let point3 = [polygonOffset[0] - 0.0012, polygonOffset[1] + 0.0000];
	let point4 = [polygonOffset[0] - 0.0008, polygonOffset[1] - 0.0008];
	let point5 = [polygonOffset[0] + 0.0008, polygonOffset[1] - 0.0008];
	let point6 = [polygonOffset[0] + 0.0012, polygonOffset[1] - 0.0000];

	let geoCoordinate = [point1, point2, point3, point4, point5, point6];
	let srcName = 'geoDID';
	let layerName = 'geoDIDFill';

	var elementReference = document.getElementById("layer_did");

	if (map.getSource(srcName)) {
		elementReference.style.backgroundImage = "url(../img/layer_did_item_grayscale.png)";
		map.removeLayer(layerName);
		map.removeSource(srcName);
	} else {
		elementReference.style.backgroundImage = "url(../img/layer_did_item.png)";
		map.addSource(srcName, {
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
			'id': layerName,
			'type': 'fill',
			'source': srcName,
			'layout': {},
			'paint': {
				'fill-color': '#f26b66',
				'fill-opacity': 0.6
			}
		});
	}
});

 // レイヤ切り替えアイコン背景色
$("#btn_layer").mouseover(function() {
	$("#btn_layer").css('background-color', '#ffffff');
});
$("#btn_layer").mouseout(function() {
	$("#btn_layer").css('background-color', '');
});

// マップのスタイル変更
async function switchBaseMap(map, styleId) {
	const response = await fetch(
		`https://api.mapbox.com/styles/v1/${styleId}?access_token=${mapboxgl.accessToken}`
	);
	const responseJson = await response.json();
	const newStyle = responseJson;
	const currentStyle = map.getStyle();
	// if switch style is the same
	let tmp = currentStyle.sprite.split('/',5);
	if (styleId == (tmp[3] + '/' + tmp[4])) {
		return true;
	}
	// ensure any sources from the current style are copied across to the new style
	newStyle.sources = Object.assign({},
		currentStyle.sources,
		newStyle.sources
	);
	// find the index of where to insert our layers to retain in the new style
	let labelIndex = -1;
	// labelIndex = newStyle.layers.findIndex((el) => {
	// 	return el.id == 'country-label';
	// });
	// default to on top
	if (labelIndex === -1) {
		labelIndex = newStyle.layers.length;
	}
	const appLayers = currentStyle.layers.filter((el) => {
		// app layers are the layers to retain, and these are any layers which have a different source set
		return (
			el.source &&
			el.source != 'mapbox://mapbox.satellite' &&
			el.source != 'mapbox' &&
			el.source != 'composite' &&
			el.source != 'mapbox-traffic' &&
			el.source != 'mapbox-incidents' &&
			el.source != 'mapbox://mapbox.terrain-rgb'
		);
	});
	newStyle.layers = [
		...newStyle.layers.slice(0, labelIndex),
		...appLayers,
		//...newStyle.layers.slice(labelIndex, -1),
		//...newStyle.layers.slice(-1),
	];
	map.setStyle(newStyle);
	// ドローンアイコンを再ロード
	if (!map.hasImage('drone-icon')) {
		map.loadImage('../img/drone_top.png', (error, image) => {
			if (error) throw error;
			map.addImage('drone-icon', image, { 'sdf': true });
		});
	}
}

// ナビ（ズーム、キャンパス）機能追加 [2022/08/05]コンパスの無効化
var nav = new mapboxgl.NavigationControl({showCompass: false});
map.addControl(nav, 'bottom-right');
//マップ回転の無効化
map.dragRotate.disable();
map.touchZoomRotate.disableRotation();