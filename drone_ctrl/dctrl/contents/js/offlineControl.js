/////////////////////////////////////////////////////////////////////////////////
/// -----------------------------------------------------------------------------
/// File name: ard_mapctrl.js
///    配送Vehicle向け「SGC: Simpleグラウンドコントローラ」 
///    -- Communicate with ardupilot via websocket.
///    -- Offline control method
/// -----------------------------------------------------------------------------
// ^----^
//  *  * 
//   ~
/////////////////////////////////////////////////////////////////////////////////
/// Description: map control Java Script program for Delivery Drone Project
/// Detail: Get the geometric data from Bing map 
const mainTitle = "SGC(Simple Ground Controller) for Edge AI Delivery Drone";
const revision = " Rev4.0.0";
const update = "20220331";
const company = "Systena Co.ltd.,CTK,OST"
const auther = "y.saito"
/////////////////////////////////////////////////////////////////////////////////

let mapCanvas, mapContext, workCanvas, workContext;
let cposByGnss_x, cposByGnss_y;
let startByGnss_x, startByGnss_y
// このフラグがfalseの場合、マウス移動ポイントを取得する
let clickFlg = false;
let initDoneFlg = false;
let FirstPin;
let map, searchManager,loc, lat, pinNo = 0;
let move_x = 0;
let move_y = 0;
// 直前のVehicleのスタート位置
let pstartPos;
// マップクリックでTrue
let mapClickFlg = false;
// STEP1移動量を算出するパラメータ
const ASP_RATIO_H = 1440/640  // 実ピクセルサイズとVGSの横比率
const ASP_RATIO_V = 1080/480  // 実ピクセルサイズとVGSの縦比率
const PIXEL_PITCH = 0.0000014 // 画素のピクセルピッチ unit = m
const FOCAL_LENGTH = 0.00188  // 焦点距離 unit = m
const DRONE_HEIGHT = 30       // Vehicleの現在高度 = m
const ADJ_FACTOR = 0.93       // 補正値
// 初期位置：みなとみらい
let ognLat = 35.455261880692845;
let ognLon = 139.6309896066712;
let cntLat = ognLat;
let cntLon = ognLon;
// 飛行軌跡描画用
let tcounter = 0;
let tpoint_x = 0;
let tpoint_y = 0;
const tinterval = 10;
let flgSetCurrentPos = false;

//////////////////////////////////////////////////////////////////////////////////////
// ロード時に実行される
window.onload = function(){
    const agent = window.navigator.userAgent.toLowerCase()
    if (agent.indexOf("firefox") != -1) { 
        console.log("ブラウザはfirefoxです。") 
    }
    else { 
        console.log("ブラウザはfirefoxではありません。") 
        alert('【注意】\nお使いのブラウザはfirefoxではありません。本プログラムはfirefoxでの使用を推奨します。\n--- firefox以外のブラウザでは動作が悪くなる可能性があります。---');    
    }
    init();
    setMove2XClr(0);
    setMove2YClr(0);
    setGSpeedClr();
    sleep(1000);
    putDroneMapCenter();
    document.getElementById('camstream').data = 'http://127.0.0.1:8080/stream_viewer?topic=/usb_cam/image_raw';
};

//////////////////////////////////////////////////////////////////////////////////////
// 指定ミリ秒間だけループさせる（CPUは常にビジー状態）
const sleep = (waitMsec) => {
    var startMsec = new Date();
    while (new Date() - startMsec < waitMsec);
}

//////////////////////////////////////////////////////////////////////////////////////
// コンストラクタ
const init = () => {
    // Bing map on flight map -----------------
    let posto = blxy(__currentLat, __currentLon, 9);
    startByGnss_x = posto[1]; // odo
    startByGnss_y = posto[0]; // odo
    __statPointX = startByGnss_x;
    __statPointY = startByGnss_y; 
    console.log(__statPointX + "," + __statPointY)
    // インターネットに接続されていない場合は、マップを表示させない。 
    if (window.navigator.onLine) {
        console.log("BINGマップの初期化")
        initBingMap(__currentLat, __currentLon);
    }
    else{
        console.log("オフラインのため、BINGマップを表示しません。")
    }
    // ----------------------------------------
    // キャンバスレイヤ: ベースメッシュ描画用
    mapCanvas = document.getElementById("map");
    mapContext = mapCanvas.getContext('2d');
    // キャンバスレイヤ: Vehicle位置を示すアイコン（矢印アイコン）描画用
    arrowCanvas = document.getElementById("arrow");
    arrowContext = arrowCanvas.getContext("2d");
    // キャンバスレイヤ: Vehicleの飛行軌跡描画用
    trajCanvas = document.getElementById("trajectory");
    trajContext = trajCanvas.getContext("2d");
    // キャンバスレイヤ: マウスクリックにより座標データを取得するためのキャンバス
    infoCanvas = document.getElementById("info");
    infoContext = infoCanvas.getContext("2d");
    __destPointX = 0; 
    __destPointY = 0;
    __distanceX = 0;
    __distanceY = 0;
    __currentHeading = 0;
    __droneDir = 0;
    startByGnss_x = 0;
    startByGnss_y = 0;
    // Vehicleの現在位置を固定箇所から現在のグローバルポジションをマップ中央に変更
    // cntLat, cntLonはFCUから取得して配信されるデータ
    __currentLat = cntLat
    __currentLon = cntLon;    
    drawMesh(20, 0.3, "#FFFFFF");
    initDoneFlg = true;
    let emt_cbtn = document.getElementById('mapcanter_button');
    let ctx_cbtn = emt_cbtn.getContext("2d");    
    ctx_cbtn.fillStyle = 'white';  // 色
    ctx_cbtn.font = "14px arial";
    ctx_cbtn.fillText("Vehicleをマップ中心に表示", 10, emt_cbtn.height/2+5);
    emt_cbtn.addEventListener('click', cbutotnClicked, false);

    let emt_rbtn = document.getElementById('rmtrj_button');
    let ctx_rbtn = emt_rbtn.getContext("2d");    
    ctx_rbtn.fillStyle = 'white';  // 色
    ctx_rbtn.font = "16px arial";
    ctx_rbtn.fillText("飛行軌跡を消去", 60, emt_cbtn.height/2+5);
    emt_rbtn.addEventListener('click', rbutotnClicked, false);
    // 十字カーソル　クリアボタン
    let emt_clrbtn = document.getElementById('mclr_button');
    emt_clrbtn.addEventListener('click', mclrbtnClicked, false);
    setValue2ClrBtn("CLR", 'white', "rgba(22, 22, 21, 0.6)")
    // 十字カーソル　前進ボタン
    let emt_fwdbtn = document.getElementById('mfwd_button');
    emt_fwdbtn.addEventListener('mousedown', mfwdbtnClicked, false);
    setValue2fwdBtn("前進", 'black', "rgba(22, 22, 21, 0.6)")
    // 十字カーソル　後退ボタン
    let emt_bakbtn = document.getElementById('mbak_button');
    emt_bakbtn.addEventListener('click', mbakbtnClicked, false);
    setValue2bakBtn("後進", 'black', "rgba(22, 22, 21, 0.6)")
    // 十字カーソル　右移動ボタン
    let emt_rgtbtn = document.getElementById('mrgt_button');
    emt_rgtbtn.addEventListener('click', mrgtbtnClicked, false);
    setValue2rgtBtn("右＞", 'black', "rgba(22, 22, 21, 0.6)")
    // 十字カーソル　左移動ボタン
    let emt_lftbtn = document.getElementById('mlft_button');
    emt_lftbtn.addEventListener('click', mlftbtnClicked, false);
    setValue2lftBtn("＜左", 'black', "rgba(22, 22, 21, 0.6)")
    // 移動開始ボタン
    let emt_movebtn = document.getElementById('move_button');
    emt_movebtn.addEventListener('click', movebtnClicked, false);
    setValue2MoveBtn("移動開始", 'white', "rgba(22, 22, 21)")
    document.addEventListener('keydown', keydown_event);
    document.addEventListener('keyup', keyup_event);
    // STOPボタン
    let emt_stopbtn = document.getElementById('stop_button');
    emt_stopbtn.addEventListener('click', stopbtnClicked, false);
    setValue2StopBtn("STOP!", 'white', "rgba(22, 22, 21)")
    // info2(速度とかの情報）キャンバス
    let emt_info = document.getElementById('info2');
    //emt_stopbtn.addEventListener('click', stopbtnClicked, false);
    //setValue2StopBtn("STOP!", 'white', "rgba(22, 22, 21)")

    sleep(1000);
    putDroneMapCenter();
    sleep(1000);
    putDroneMapCenter();
}

let chkKeyDown = false;
function keydown_event(e) {
	//キーが押されている時の処理
	let key = '';
    console.log("PressedKey is " + e.key)
	switch (e.key) {
    case 'Shift':
        console.log("Shift key on");
        chkKeyDown = true;
        break;
    case ' ':
        console.log("Space key on");
        droneDcmd("STOP");
        break;
    }
}

function keyup_event(e) {
    console.log("Key is off")
    chkKeyDown = false;
}


//////////////////////////////////////////////////////////////////////////////////////
//　十字ボタン：ボタン位置はCSSで設定
const setValue2ClrBtn = (data, color, bkcolor) => {
    let emt = document.getElementById('mclr_button');
    let ctx = emt.getContext("2d");    
    ctx.clearRect(0,0,emt.width, emt.height);
    ctx.fillStyle = color;  // 色
    ctx.font = "18px arial";
    ctx.fillText(data, 5, emt.height/2+5);
}
const setValue2fwdBtn = (data, color, bkcolor) => {
    let emt = document.getElementById('mfwd_button');
    let ctx = emt.getContext("2d");    
    ctx.clearRect(0,0,emt.width, emt.height);
    ctx.fillStyle = color;  // 色
    ctx.font = "18px arial";
    ctx.fillText(data, 5, emt.height/2+5);
}
const setValue2bakBtn = (data, color, bkcolor) => {
    let emt = document.getElementById('mbak_button');
    let ctx = emt.getContext("2d");    
    ctx.clearRect(0,0,emt.width, emt.height);
    ctx.fillStyle = color;  // 色
    ctx.font = "18px arial";
    ctx.fillText(data, 5, emt.height/2+5);
}
const setValue2rgtBtn = (data, color, bkcolor) => {
    let emt = document.getElementById('mrgt_button');
    let ctx = emt.getContext("2d");    
    ctx.clearRect(0,0,emt.width, emt.height);
    ctx.fillStyle = color;  // 色
    ctx.font = "18px arial";
    ctx.fillText(data, 5, emt.height/2+5);
}
const setValue2lftBtn = (data, color, bkcolor) => {
    let emt = document.getElementById('mlft_button');
    let ctx = emt.getContext("2d");    
    ctx.clearRect(0,0,emt.width, emt.height);
    ctx.fillStyle = color;  // 色
    ctx.font = "18px arial";
    ctx.fillText(data, 5, emt.height/2+5);
}
const setValue2MoveBtn = (data, color, bkcolor) => {
    let emt = document.getElementById('move_button');
    let ctx = emt.getContext("2d");    
    ctx.clearRect(0,0,emt.width, emt.height);
    ctx.fillStyle = color;  // 色
    ctx.font = "18px arial";
    ctx.fillText(data, 12, emt.height/2+5);
}
const setValue2StopBtn = (data, color, bkcolor) => {
    let emt = document.getElementById('stop_button');
    let ctx = emt.getContext("2d");    
    ctx.clearRect(0,0,emt.width, emt.height);
    ctx.fillStyle = color;  // 色
    ctx.font = "24px arial";
    ctx.fillText(data, 12, emt.height/2+5);
}

const mfwdbtnClicked = () => {
    if( chkKeyDown )
        setMove2XLongP();
    else
        setMove2XShortP();
    moveFwdBtnValue();
}

const moveFwdBtnValue = () => {
    if(move_x>0){
        setValue2fwdBtn(move_x.toFixed(1)+'m', 'black', "rgba(245, 141, 4, 0.8)");
        setValue2bakBtn("後進", 'black', "rgba(22, 22, 21, 0.6)");
    }
    else if(move_x<0){
        setValue2fwdBtn("前進", 'black', "rgba(22, 22, 21, 0.6)");
        setValue2bakBtn(move_x.toFixed(1)+'m', 'black', "rgba(245, 141, 4, 0.8)");
    }
    else{
        setValue2fwdBtn("前進", 'black', "rgba(22, 22, 21, 0.6)");
        setValue2bakBtn("後進", 'black', "rgba(22, 22, 21, 0.6)");
    }
}

const mbakbtnClicked = () => {
    if( chkKeyDown )
        setMove2XLongM();
    else
       setMove2XShortM();
    moveBakBtnValue();
}
const moveBakBtnValue = () => {
    if(move_x>0){
        setValue2fwdBtn(move_x.toFixed(1)+'m', 'black', "rgba(245, 141, 4, 0.8)");
        setValue2bakBtn("後進", 'black', "rgba(22, 22, 21, 1)");
    }
    else if(move_x<0){
        setValue2fwdBtn("前進", 'black', "rgba(22, 22, 21, 1)");
        setValue2bakBtn(move_x.toFixed(1)+'m', 'black', "rgba(245, 141, 4, 0.8)");
    }
    else{
        setValue2fwdBtn("前進", 'black', "rgba(22, 22, 21, 1)");
        setValue2bakBtn("後進", 'black', "rgba(22, 22, 21, 1)");
    }    
}

const mrgtbtnClicked = () => {
    if( chkKeyDown )
        setMove2YLongP();
    else
        setMove2YShortP();
    moveRgtBtnValue();
}

const moveRgtBtnValue = () => {
    if(move_y>0){
        setValue2rgtBtn(move_y.toFixed(1)+'m', 'black', "rgba(245, 141, 4, 0.8)");
        setValue2lftBtn("＜左", 'black', "rgba(22, 22, 21, 0.6)");
    }
    else if(move_y<0){
        setValue2rgtBtn("右＞", 'black', "rgba(22, 22, 21, 0.6)");
        setValue2lftBtn(move_y.toFixed(1)+'m', 'black', "rgba(245, 141, 4, 0.8)");
    }
    else{
        setValue2rgtBtn("右＞", 'black', "rgba(22, 22, 21, 0.6)");
        setValue2lftBtn("＜左", 'black', "rgba(22, 22, 21, 0.6)");
    }
}

const mlftbtnClicked = () => {
    if( chkKeyDown )
        setMove2YLongM();
    else
        setMove2YShortM();
    moveLftBtnValue();
}

const moveLftBtnValue = () => {
    if(move_y>0){
        setValue2rgtBtn(move_y.toFixed(1)+'m', 'black', "rgba(245, 141, 4, 0.8)");
        setValue2lftBtn("＜左", 'black', "rgba(22, 22, 21, 0.6)");
    }
    else if(move_y<0){
        setValue2rgtBtn("右＞", 'black', "rgba(22, 22, 21, 0.6)");
        setValue2lftBtn(move_y.toFixed(1)+'m', 'black', "rgba(245, 141, 4, 0.8)");
    }
    else{
        setValue2rgtBtn("右＞", 'black', "rgba(22, 22, 21, 0.6)");
        setValue2lftBtn("＜左", 'black', "rgba(22, 22, 21, 0.6)");
    }
}

const mclrbtnClicked = () => {
    setMove2XClr(0);
    setMove2YClr(0);
    setValue2fwdBtn("前進", 'black', "rgba(22, 22, 21, 0.6)");
    setValue2bakBtn("後進", 'black', "rgba(22, 22, 21, 0.6)");
    setValue2rgtBtn("右＞", 'black', "rgba(22, 22, 21, 0.6)");
    setValue2lftBtn("＜左", 'black', "rgba(22, 22, 21, 0.6)");
}

const movebtnClicked = () => {
    droneCtrl('MOVE_SLD');
}

const stopbtnClicked = () => {
    droneDcmd('STOP');
}

//////////////////////////////////////////////////////////////////////////////////////
// 画面上のボタンクリックイベントハンドラ
const cbutotnClicked = () => {
    putDroneMapCenter();
}

const rbutotnClicked = () => {
    clearCanvas(); 
} 

//////////////////////////////////////////////////////////////////////////////////////
// 移動距離設定方式選択ラジオボタン選択イベントハンドラ
const fomvalueChange = () => {
    setMove2XClr(0);
    setMove2YClr(0);
}

//////////////////////////////////////////////////////////////////////////////////////
// チェックボックス状態変化イベントハンドラ
// チェックボックスの状態が変化した場合にキャンバスとライン、アイコン等を削除する。
const mcbxvalueChange = () => {
    clearCanvas(); 
    document.getElementById('pixel_dx').value = 0;
    document.getElementById('pixel_dy').value = 0;    
    let obj1 = document.getElementById('open_dmove').style;
    let obj2 = document.getElementById('open_mclk').style;
    let element = document.getElementById('check_mmode');
    if(element.checked){
        obj1.display = 'block'
        obj2.display = 'none';
    }
    else{
        obj1.display = 'none';
        obj2.display = 'block'
    }
}

//////////////////////////////////////////////////////////////////////////////////////
//　エラーコールバック
const errorCallback = error => {
    // 取得に失敗した場合，エラーコードを表示
    alert("Error code: " + error.code);
}

//////////////////////////////////////////////////////////////////////////////////////
// BINGマップを初期化
const initBingMap = (lat,lon) => {
    map = new Microsoft.Maps.Map('#bonlinemap', {
        center: new Microsoft.Maps.Location(lat, lon),
        zoom: 20,
        disableZooming: true,       // Zoom button disable
        disableBirdseye: true,      // Bird view disable
        showLocateMeButton: false,  // Current location button disable
        mapTypeId: Microsoft.Maps.MapTypeId.aerial
    });
    loc = map.getCenter();    
    //検索モジュール指定
    Microsoft.Maps.loadModule('Microsoft.Maps.Search', function () {
        searchManager = new Microsoft.Maps.Search.SearchManager(map);
    });
    console.log(__currentLat + ',' + __currentLon + ',' + __currentHeading)
    setCenterToCpos(__currentLat, __currentLon);
}

//////////////////////////////////////////////////////////////////////////////////////
// 現在位置をマップの中央に設定
const setCenterToCpos = (lat, lon) => {
    // 60進法の緯度経度から直角平面座標を計算
    let retAddressfrom = blxy(lat, lon, 9);
    __statPointX = retAddressfrom[0];
    __statPointY = retAddressfrom[1];
    if (window.navigator.onLine) {
        // Webからマップを取得できる場合
        let droneInitPos = new Microsoft.Maps.Location(lat, lon);
        map.setView({center: droneInitPos});
        pstartPos = droneInitPos;
    }
}

//////////////////////////////////////////////////////////////////////////////////////
// マップキャンバスに方眼メッシュを描く
//  stroke: メッシュ間隔
//  lwidth: メッシュライン幅
//  color: メッシュラインカラー
const drawMesh = (stroke, lwidth, color) => {
    let x1 = 0;
    let y1 = 0;  
    let x2 = 0;
    let y2 = 0;
    document.getElementById('mmsg').innerHTML = "マップ初期化完了";
    mapContext.strokeStyle = color;
    const cx = mapCanvas.width;
    const cy = mapCanvas.height;
    // Horizontal
    for (i = 1; i < cx/stroke; i++){
        if(i%5===0){
            mapContext.lineWidth = lwidth*2;
        }
        else{
            mapContext.lineWidth = lwidth;
        }
        x1 = i * stroke;
        y1 = 0;  
        x2 = x1;
        y2 = cy;
        mapContext.beginPath();
        mapContext.moveTo(x1, y1);
        mapContext.lineTo(x2, y2);
        mapContext.stroke();
    }
    // Vertical
    for (i = 1; i < cy/stroke; i++){
        if(i%5===0){
            mapContext.lineWidth = lwidth*2;
        }
        else{
            mapContext.lineWidth = lwidth;
        }
        y1 = i * stroke;
        x1 = 0;  
        y2 = y1;
        x2 = cx;
        mapContext.beginPath();
        mapContext.moveTo(x1, y1);
        mapContext.lineTo(x2, y2);
        mapContext.stroke();
    }
    mapContext.font = "36px sans-serif";
    mapContext.fillStyle = color;
    mapContext.fillText("N", mapCanvas.width/2-14, 34);
    mapContext.fillText("S", mapCanvas.width/2-12, mapCanvas.height-10);
    mapContext.fillText("E", mapCanvas.width-25, mapCanvas.height/2+10);
    mapContext.fillText("W", 8, mapCanvas.height/2+10);
    mapContext.lineWidth = lwidth*10;
    mapContext.beginPath();
    x1 = stroke * 44;
    x2 = stroke * 49;
    y1 = stroke * 28.5;
    y2 = stroke * 28.5;
    mapContext.moveTo(x1, y1);
    mapContext.lineTo(x2, y2);
    mapContext.stroke();
}

//////////////////////////////////////////////////////////////////////////////////////
// 矢アイコンを作成して表示
//  cx: x 位置
//  cy: y 位置
//  heading: 向き
const createRedArrowIcon = (cx, cy, heading) => {
    let corarray;
    // キャンバスをクリア
    arrowContext.clearRect(0,0,arrowCanvas.width,arrowCanvas.height);
    //Draw a path in the shape of an arrow.
    if(droneCntAlt>1.0) arrowContext.strokeStyle = "#00bfff" ;
    else arrowContext.strokeStyle = "#aaaaaa" ;
    arrowContext.beginPath();
    corarray = rotateCoord(0, 0, heading);
    arrowContext.arc(corarray[0]+cx, corarray[1]+cy, 30, 0, Math.PI * 2, true);
    arrowContext.lineWidth = 3;
    arrowContext.stroke();
    // cross vertical line
    if(droneCntAlt>1.0) arrowContext.strokeStyle = "#00ffff";
    else arrowContext.strokeStyle = "#aaaaaa";
    arrowContext.lineWidth = 1;
    arrowContext.beginPath();
    corarray = rotateCoord(0, -60, heading);
    arrowContext.moveTo(corarray[0]+cx, corarray[1]+cy);
    corarray = rotateCoord(0, 50, heading);
    arrowContext.lineTo(corarray[0]+cx, corarray[1]+cy);
    arrowContext.closePath();
    arrowContext.stroke();
    // arrow right side
    if(droneCntAlt>1.0) arrowContext.strokeStyle = "#00ffff";
    else arrowContext.strokeStyle = "#aaaaaa";
    arrowContext.lineWidth = 2;
    arrowContext.beginPath();
    corarray = rotateCoord(0, -60, heading);
    arrowContext.moveTo(corarray[0]+cx, corarray[1]+cy);
    corarray = rotateCoord(6, -45, heading);
    arrowContext.lineTo(corarray[0]+cx, corarray[1]+cy);
    arrowContext.closePath();
    arrowContext.stroke();
    // arrow left side
    if(droneCntAlt>1.0) arrowContext.strokeStyle = "#00ffff";
    else arrowContext.strokeStyle = "#aaaaaa";
    arrowContext.lineWidth = 2;
    arrowContext.beginPath();
    corarray = rotateCoord(0, -60, heading);
    arrowContext.moveTo(corarray[0]+cx, corarray[1]+cy);
    corarray = rotateCoord(-6, -45, heading);
    arrowContext.lineTo(corarray[0]+cx, corarray[1]+cy);
    arrowContext.closePath();
    arrowContext.stroke();
    // cross horizontal line
    if(droneCntAlt>1.0) arrowContext.strokeStyle = "#00ffff";
    else arrowContext.strokeStyle = "#aaaaaa";
    arrowContext.lineWidth = 1;
    arrowContext.beginPath();
    corarray = rotateCoord(-40, 0, heading);
    arrowContext.moveTo(corarray[0]+cx, corarray[1]+cy);
    corarray = rotateCoord(40, 0, heading);
    arrowContext.lineTo(corarray[0]+cx, corarray[1]+cy);
    arrowContext.closePath();
    arrowContext.stroke();
    if(droneCntAlt>1.0) arrowContext.strokeStyle = "#00bfff";
    else arrowContext.strokeStyle = "#aaaaaa"
    if(droneCntAlt>1.0) arrowContext.fillStyle = "#ff0000";
    else arrowContext.fillStyle = "#aaaaaa"
    arrowContext.lineWidth = 1;
    arrowContext.beginPath();
    corarray = rotateCoord(0, -30, heading);
    arrowContext.moveTo(corarray[0]+cx, corarray[1]+cy);
    corarray = rotateCoord(-23, 14, heading);
    arrowContext.lineTo(corarray[0]+cx, corarray[1]+cy);
    corarray = rotateCoord(0, 7, heading);
    arrowContext.lineTo(corarray[0]+cx, corarray[1]+cy);
    corarray = rotateCoord(23, 14, heading);
    arrowContext.lineTo(corarray[0]+cx, corarray[1]+cy);
    corarray = rotateCoord(0, -30, heading);
    arrowContext.lineTo(corarray[0]+cx, corarray[1]+cy);
    arrowContext.closePath();
    arrowContext.fill();
    arrowContext.stroke();
    arrowContext.font = "18px sans-serif";
    if((heading>=0)&&(heading<90)){
        corarray = rotateCoord(40, 40, heading);
    }
    else if((heading>=90)&&(heading<180)){
        corarray = rotateCoord(60, 100, heading);
    }
    else if((heading>=180)&&(heading<270)){
        corarray = rotateCoord(40, 40, heading);
    }
    else if((heading>=270)&&(heading<360)){
        corarray = rotateCoord(40, 40, heading);
    }
    arrowContext.fillStyle = "#ffff00";
}

//////////////////////////////////////////////////////////////////////////////////////
// 飛行軌跡をマップに描画
const putTrajectoryPoint = (x, y) => {
    console.log("Tra:"+x+','+y)
    let px, py;
    if((px!=x) && (py!=y)) {
        trajContext.strokeStyle = '#00ffff';
        trajContext.fillStyle = '#00ffff';
        trajContext.lineWidth = 1;    
        trajContext.beginPath();
        trajContext.arc(x, y, 3, 0, Math.PI * 2, false);
        trajContext.fill();
        trajContext.stroke();
        px = x;
        py = y;
    }
}

//////////////////////////////////////////////////////////////////////////////////////
// Vehicleアイコン（矢印アイコン）をマップ中心にセット
const putDroneMapCenter = () => {
    clearCanvas();
    let posto = blxy(__currentLat, __currentLon, 9);
    startByGnss_x = posto[1];
    startByGnss_y = posto[0];
    createRedArrowIcon(mapCanvas.width/2, mapCanvas.height/2, __currentHeading);
    // set center position to current map location
    setCenterToCpos(__currentLat, __currentLon);
}

//////////////////////////////////////////////////////////////////////////////////////
// Vehicleの現在地から目的地までの線を描画
const putLine = (dx, dy) => {
    infoContext.strokeStyle = "#ff69b4";
    infoContext.lineWidth = 1;
    infoContext.beginPath();
    infoContext.moveTo(cposByGnss_x, cposByGnss_y);
    infoContext.lineTo(dx, dy);
    infoContext.closePath();
    infoContext.stroke();
    __statPointX = cposByGnss_x / 10;
    __statPointY = (cposByGnss_y/10) * -1;
    __destPointX = dx/10;
    __destPointY = dy/10 * -1;
    __distanceX = __destPointX - __statPointX;
    __distanceY = __destPointY - __statPointY;
}

//////////////////////////////////////////////////////////////////////////////////////
// 目的地フラッグを設定
const putGoalFlag = (cx, cy, img) => {
    infoContext.clearRect(0,0,infoCanvas.width,infoCanvas.height);
    const chara = new Image();
    chara.src = img;
    chara.onload = () => {
        infoContext.drawImage(chara, cx-chara.width/2, cy-chara.height/2);
    };
    putLine(cx, cy);
    tpoint_x = 0;
    tpoint_y = 0;
    tcounter = 0;
}

//////////////////////////////////////////////////////////////////////////////////////
// 移動先位置の座標をNEDから進行方向座標に座標変換
const rotateCoord = (x, y, angle) => {
    let rx = x*Math.cos(angle*Math.PI/180) - y*Math.sin(angle*Math.PI/180);
    let ry = x*Math.sin(angle*Math.PI/180) + y*Math.cos(angle*Math.PI/180);
    return [rx, ry];
}

//////////////////////////////////////////////////////////////////////////////////////
// キャンバスをクリア: Vehicleアイコン、情報、飛行軌跡
const clearCanvas = () => {
    arrowContext.clearRect(0,0,arrowCanvas.width, arrowCanvas.height);
    infoContext.clearRect(0,0,infoCanvas.width, infoCanvas.height);
    trajContext.clearRect(0,0,trajCanvas.width, trajCanvas.height);
    clickFlg = false; // Use for getting mouse move point when this flag is false
}

//////////////////////////////////////////////////////////////////////////////////////
// 一定間隔で実行(300msec): 現在緯度経度からの位置を取得
setInterval( () => {
    // 飛行軌跡描画用：指定回数分の平均ポイントを描画する
    if(initDoneFlg){
        let posto = blxy(__currentLat, __currentLon, 9);
        cposByGnss_x = mapCanvas.width/2-(startByGnss_x-posto[1])*10;
        cposByGnss_y = mapCanvas.height/2+(startByGnss_y-posto[0])*10;
        createRedArrowIcon(cposByGnss_x, cposByGnss_y, __currentHeading);
        tpoint_x += cposByGnss_x;
        tpoint_y += cposByGnss_y;
        tcounter++;
        if( tcounter >= tinterval){
            // 指定回数の平均位置へ飛行機席を描画する
            putTrajectoryPoint(tpoint_x/tinterval, tpoint_y/tinterval);
            tpoint_x = 0;
            tpoint_y = 0;
            tcounter = 0;
        }
    }

    let emt = document.getElementById('info2');
    let ctx = emt.getContext("2d");    
    ctx.clearRect(0,0,emt.width, emt.height);
    ctx.fillStyle = 'black';  // 色
    ctx.font = "19px arial";
    gspeed = document.getElementById('speed_gs').value;
    gspeed = parseFloat(gspeed).toFixed(1) + " m/s";
    udspeed = document.getElementById('speed_ud').value;
    udspeed = parseFloat(udspeed).toFixed(1) + " m/s";
    ctx.fillText(gspeed, 87, 45); 
    ctx.fillText(udspeed, 87, 70);
    ctx.fillText("Flight", 5, 45)
    ctx.fillText("UpDown", 5, 70)
    ctx.fillText("Speed", 5, 20); 

}, 300);

//////////////////////////////////////////////////////////////////////////////////////
// 離陸高度設定クリア
const setTakeoffAltClr = () => {
    const alt = 3.0;
    document.getElementById('takeoff_alt_in').value = alt;
    document.getElementById("takeoff_alt_dsp").innerText = alt.toFixed(1) + "m";
}

//////////////////////////////////////////////////////////////////////////////////////
// 離陸高度をスライダ入力値に設定
const setTakeoffAlt = () => {
    const alt = document.getElementById('takeoff_alt_in').value;
    document.getElementById("takeoff_alt_dsp").innerText = parseFloat(alt).toFixed(1) + "m";
}

//////////////////////////////////////////////////////////////////////////////////////
// X方向の移動量設定クリア
const setMove2XClr = flg => {
    move_x = 0;
    document.getElementById("move2_x").innerText = move_x.toFixed(1) + "m";
    document.getElementById('move2_xin').value = move_x;
    setDestPos(move_x, move_y, flg);
}

//////////////////////////////////////////////////////////////////////////////////////
// X方向の移動量スライダ入力値に設定
const setMove2X = () => {
    document.getElementById('pixel_dx').value = 0;
    document.getElementById('pixel_dy').value = 0;
    move_x = document.getElementById('move2_xin').value;
    document.getElementById("move2_x").innerText = parseFloat(move_x).toFixed(1) + "m";
    setDestPos(move_x, move_y, 1);
    moveFwdBtnValue();
    moveBakBtnValue();
}

//////////////////////////////////////////////////////////////////////////////////////
// X方向の移動量の現在の設定値-1mに設定
const setMove2XShortM = () => {
    let data = 1;
    move_x = move_x * 10;
    move_x = move_x - data;
    move_x = move_x / 10;
    console.log(move_x);
    if(move_x<-50) move_x = -50;
    document.getElementById("move2_x").innerText = move_x.toFixed(1) + "m";
    document.getElementById('move2_xin').value = move_x;
    setDestPos(move_x, move_y, 1);
}

//////////////////////////////////////////////////////////////////////////////////////
// X方向の移動量の現在の設定値-10mに設定
const setMove2XLongM = () => {
    let data = 10;
    move_x = move_x * 10;
    move_x = move_x - data;
    move_x = move_x / 10;
    if(move_x<-50) move_x = -50;
    console.log(move_x);
    document.getElementById("move2_x").innerText = move_x.toFixed(1) + "m";
    document.getElementById('move2_xin').value = move_x;
    setDestPos(move_x, move_y, 1);
}

//////////////////////////////////////////////////////////////////////////////////////
// X方向の移動量設定 +1
const setMove2XShortP = () => {
    let data = 1;
    move_x = move_x * 10;
    move_x = move_x + data;
    move_x = move_x / 10;
    if(move_x>50) move_x = 50;
    console.log(move_x);
    document.getElementById("move2_x").innerText = move_x.toFixed(1) + "m";
    document.getElementById('move2_xin').value = move_x;
    setDestPos(move_x, move_y, 1);
}

//////////////////////////////////////////////////////////////////////////////////////
// X方向の移動量設定 +10
const setMove2XLongP = () => {
    let data = 10;
    move_x = move_x * 10;
    move_x = move_x + data;
    move_x = move_x / 10;
    if(move_x>50) move_x = 50;
    console.log(move_x);
    document.getElementById("move2_x").innerText = move_x.toFixed(1) + "m";
    document.getElementById('move2_xin').value = move_x;
    setDestPos(move_x, move_y, 1);
}

//////////////////////////////////////////////////////////////////////////////////////
// 対地速度設定をクリア
const setGSpeedClr = () => {
    document.getElementById('speed_gs_set').innerText = "0.6m/s(2.16km/h)";
    document.getElementById('speed_gs').value = 0.6;
}

//////////////////////////////////////////////////////////////////////////////////////
// 対地速度をスライダ入力値に設定
const setGroundSpeed = () => {
    let gsps = document.getElementById('speed_gs').value;
    let gsph = gsps * 3600 / 1000;
    document.getElementById('speed_gs_set').innerText 
        = parseFloat(gsps).toFixed(1) + "m/s (" + parseFloat(gsph).toFixed(2) + "km/h)";
}

//////////////////////////////////////////////////////////////////////////////////////
// 上昇降下速度をスライダ入力値に設定
const setUpdownSpeed = () => {
    let udps = document.getElementById('speed_ud').value;
    let udph = udps * 3600 / 1000;
    document.getElementById('speed_ud_set').innerText 
        = parseFloat(udps).toFixed(1) + "m/s (" + parseFloat(udph).toFixed(2) + "km/h)";
}

//////////////////////////////////////////////////////////////////////////////////////
// Y方向の移動量設定クリア
const setMove2YClr = flg => {
    move_y = 0;
    document.getElementById("move2_y").innerText = move_y.toFixed(1) + "m";
    document.getElementById('move2_yin').value = move_y.toFixed(1);
    setDestPos(move_x, move_y, flg);
}

//////////////////////////////////////////////////////////////////////////////////////
// Y方向の移動量をスライダ入力値に設定
const setMove2Y = () => {
    document.getElementById("move2_y").innerText = parseFloat(move_y).toFixed(1) + "m";
    move_y = document.getElementById('move2_yin').value;
    setDestPos(move_x, move_y, 1);
    moveRgtBtnValue();
    moveLftBtnValue();    
}

//////////////////////////////////////////////////////////////////////////////////////
// Y方向の移動量の現在の設定値-1mに設定
const setMove2YShortM = () => {
    // JavaScriptの少数計算は誤差が発生するため、整数で計算してから少数に戻す。
    let data = 1;
    move_y = move_y * 10;
    move_y = move_y - data;
    move_y = move_y / 10;
    if(move_y<-50) move_y = -50;
    console.log(move_y);
    document.getElementById("move2_y").innerText = move_y.toFixed(1) + "m";
    document.getElementById('move2_yin').value = move_y;
    setDestPos(move_x, move_y, 1);
}

//////////////////////////////////////////////////////////////////////////////////////
// Y方向の移動量の現在の設定値-10mに設定
const setMove2YLongM = () => {
    // JavaScriptの少数計算は誤差が発生するため、整数で計算してから少数に戻す。
    let data = 10;
    move_y = move_y * 10;
    move_y = move_y - data;
    move_y = move_y / 10;
    if(move_y<-50) move_y = -50;
    console.log(move_y);
    document.getElementById("move2_y").innerText = move_y.toFixed(1) + "m";
    document.getElementById('move2_yin').value = move_y;
    setDestPos(move_x, move_y, 1);
}

//////////////////////////////////////////////////////////////////////////////////////
// Y方向の移動量の現在の設定値+1mに設定
const setMove2YShortP = () => {
    // JavaScriptの少数計算は誤差が発生するため、整数で計算してから少数に戻す。
    let data = 1;
    move_y = move_y * 10;
    move_y = move_y + data;
    move_y = move_y / 10;
    console.log(move_y);
    if(move_y>50) move_y = 50;
    document.getElementById("move2_y").innerText = move_y.toFixed(1) + "m";
    document.getElementById('move2_yin').value = move_y;
    setDestPos(move_x, move_y, 1);
}

//////////////////////////////////////////////////////////////////////////////////////
// Y方向の移動量の現在の設定値+10mに設定
const setMove2YLongP = () => {
    // JavaScriptの少数計算は誤差が発生するため、整数で計算してから少数に戻す。
    let data = 10;
    move_y = move_y * 10;
    move_y = move_y + data;
    move_y = move_y / 10;
    if(move_y>50) move_y = 50;
    document.getElementById("move2_y").innerText = move_y.toFixed(1) + "m";
    document.getElementById('move2_yin').value = move_y;
    setDestPos(move_x, move_y, 1);
}

//////////////////////////////////////////////////////////////////////////////////////
// 目的地フラッグを描画
const setDestPos = (move_x, move_y, flg) => {
    let odom = rotateCoord(move_x, move_y, __currentHeading);
    let mpos_x = parseFloat(cposByGnss_x) + odom[1] * 10;
    let mpos_y = parseFloat(cposByGnss_y) + odom[0] * 10 * -1;
    if(flg==1){
        putGoalFlag(mpos_x, mpos_y, "img/goalFlag32x32.png");
        let point = ('--- m , --- m');  
    }
}

//////////////////////////////////////////////////////////////////////////////////////
// YAW回転角度を取得  
const yawrotchange = () => {
    setMove2XClr(0);
    setMove2YClr(0);
    let yawv = document.getElementById('yawrotate_deg').value;
    document.getElementById('yawrotvalue').innerHTML = yawv;
}

//////////////////////////////////////////////////////////////////////////////////////
// ステップ１移動量を取得  
const stp1inchange = () => {
    setMove2XClr(0);
    setMove2YClr(0);
    let stp1pos_x = document.getElementById('pixel_dx').value;
    let stp1pos_y = document.getElementById('pixel_dy').value;
    document.getElementById('s1_xpix').innerHTML = stp1pos_x;
    document.getElementById('s1_ypix').innerHTML = stp1pos_y;
    setDestPosStp1(stp1pos_x, stp1pos_y);
}

//////////////////////////////////////////////////////////////////////////////////////
// ステップ１ゴールフラッグを描画
const setDestPosStp1 = (pix_x, pix_y) => {
    // ピクセル値を実距離に変換
    if (pix_x != 0){
        move_x = Math.cos(Math.atan(Math.abs(pix_y/pix_x))) * PIXEL_PITCH * DRONE_HEIGHT * pix_x * ASP_RATIO_H / FOCAL_LENGTH * ADJ_FACTOR
        move_y = Math.sin(Math.atan(Math.abs(pix_y/pix_x))) * PIXEL_PITCH * DRONE_HEIGHT * pix_y * ASP_RATIO_V / FOCAL_LENGTH * ADJ_FACTOR
    }
    else{
        move_x = 0
        move_y = PIXEL_PITCH * DRONE_HEIGHT * pix_y * ASP_RATIO_V / FOCAL_LENGTH * ADJ_FACTOR
    }
    let odom = rotateCoord(move_x, move_y, __currentHeading);
    let mpos_x = parseFloat(cposByGnss_x) + odom[1] * 10;
    let mpos_y = parseFloat(cposByGnss_y) + odom[0] * 10 * -1;
    console.log("mpos_x="+ mpos_x + ", mpos_y=" + mpos_y);
    if((pix_x!=0)||(pix_y!=0)){
        putGoalFlag(mpos_x, mpos_y, "img/roof32x32.png");
    }
}

//////////////////////////////////////////////////////////////////////////////////////
// スライダをクリア
const clarPixMoveSliderValue = () =>{
    document.getElementById('pixel_dx').value = 0;
    document.getElementById('pixel_dy').value = 0; 
    document.getElementById('pixel_dx3d').value = 0;
    document.getElementById('pixel_dy3d').value = 0;
    document.getElementById('dist_dz3d').value = 0;
    document.getElementById('distance_Alt').value = 0;
}

//////////////////////////////////////////////////////////////////////////////////////
// ステップ２移動量を取得  
const stp2inchange = () => {
    let stp1pos_x = document.getElementById('pixel_dx3d').value;
    let stp1pos_y = document.getElementById('pixel_dy3d').value;
    let stp1pos_z = document.getElementById('dist_dz3d').value;
    document.getElementById('s2_xpix').innerHTML = stp1pos_x;
    document.getElementById('s2_ypix').innerHTML = stp1pos_y;
    document.getElementById('s2_zdst').innerHTML = stp1pos_z;
}

//////////////////////////////////////////////////////////////////////////////////////
// ステップ３移動量を取得  
const stp3inchange = () => {
    let stp3pos_z = document.getElementById('distance_Alt').value;
    document.getElementById('s3_hgt').innerHTML = stp3pos_z;
}