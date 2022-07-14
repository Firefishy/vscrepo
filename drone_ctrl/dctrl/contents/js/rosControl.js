/////////////////////////////////////////////////////////////////////////////////
/// -----------------------------------------------------------------------------
/// File name: ard_mapctrl.js
///    配送Vehicle向け「SGC: Simpleグラウンドコントローラ」 
///    -- Communicate with PX4 via websocket.
///    -- Offline control method
/// -----------------------------------------------------------------------------
//
// ^-----^
//  *   * 
//    ~ 
//
/////////////////////////////////////////////////////////////////////////////////
/// Description: map control Java Script program for Delivery Drone Project
/// Detail: Get the geometric data from Bing map
/// const mainTitle = "SGC(Simple Ground Controller) for Edge AI Delivery Drone";
/// const revision = " Rev4.0.0";
/// const update = "20220331";
/// const company = "Systena Co.ltd.,CTK,OST"
/// const auther = "y.saito"
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
let pubDroneCtrl = new Float32Array(12);
let headingAngle = 0;
//let dstatus;
let droneRoll = 0;
let dronePitch = 0;
let droneDir = 0;
let flgMoveBtnPushed = false;
// バッテリ関係
let batPower = 0;
let batCurrent = 0;
let batRemain = 0;
// 対地速度
let gndSpeed = 0; 

//////////////////////////////////////////////////////////////////////////////////////
// WebSocket設定
var ros = new ROSLIB.Ros({ url: 'ws://' + location.hostname + ':9090' });
ros.on('connection', function () { console.log('websocker: connected'); });
ros.on('error', function (error) { console.log('websocker error: ', error); });
ros.on('close', function () {
    console.log('websocker closed');
    //location.reload(); 
    msg = 'Vehicleに接続していません。'
    alert(msg);
    document.getElementById('cntstatus').innerHTML = msg;
    document.getElementById("cntstatus").style.backgroundColor = 'red';
});

//////////////////////////////////////////////////////////////////////////////////////
// WebSocket接続
const wscon = () => {
    url = 'ws://' + location.hostname + ':9090'
    ros.connect(url);
    console.log(url);
    sleep(2);
    cmdpub('WSCONNECT');
}

//////////////////////////////////////////////////////////////////////////////////////
// WebSocket切断
const wsdiscon = () => {
    ros.close();
}

//////////////////////////////////////////////////////////////////////////////////////
// ステップ１判定結果イメージ表示ページを開く
const openstep1imgpage = () => {
    window.open('stepimage.html', '_blank');
}

let flgCheckFlight = false;
let flightmode = 'Unknown';
//////////////////////////////////////////////////////////////////////////////////////
// Vehicleの各種情報を取得するサブスクライバ
// 取得した各種データを設定し、Web画面に表示する
var sub_info = new ROSLIB.Topic({
    ros: this.ros, name: 'drone_info',
    messageType: 'drone_ctrl/DroneInfo'
});
sub_info.subscribe(message => {
    cntLat = message.lat;
    cntLon = message.long;
    cntAlt = message.alt_abs;
    pubDroneCtrl[6] = cntLat.toString();
    pubDroneCtrl[7] = cntLon.toString();;
    __currentLat = cntLat;
    __currentLon = cntLon;
    // 対地高度
    calt = message.alt_rel;
    // 小数点２位で四捨五入
    droneCntAlt = Math.round((calt) * 100) / 100;
    // Vehicleの向き
    let heading = message.heading;
    droneDir = heading;
    __droneDir = heading;
    //let dstatus = heading.toString();
    headingAngle = Math.round(heading * 1000) / 1000;
    __currentHeading = headingAngle;
    // 現在のフライトモード
    flightmode = message.flight_mode;
    document.getElementById('flightmode').innerHTML = flightmode;
    if ((flightmode === 'OFFBOARD')||(flightmode == 'GUIDED')){
        document.getElementById('modewrap2').style.backgroundColor = '#008000';
        flgCheckFlight = true;
    } 
    else if ((flightmode === 'HOLD')||(flightmode == 'RTL')){
        document.getElementById('modewrap2').style.backgroundColor = '#ff8c00';   // darkorange
        if(flgCheckFlight){
            sleep(1);
            // HOLDモード時はVehicleアイコンをマップの中心に表示 ... 廃止
            // putDroneMapCenter();
            flgCheckFlight = false;
        } 
    }
    else if (flightmode === 'LAND'){
        document.getElementById('modewrap2').style.backgroundColor = '#000080';   // navy
    } 
    else if (flightmode === 'BRAKE'){
        document.getElementById('modewrap2').style.backgroundColor = '#dc143c'; // crimson
    }
    else{
        document.getElementById('modewrap2').style.backgroundColor = '#000000';
    }
    // バッテリ
    batPower = Math.round(message.battery_volt * 100) / 100;
    batCurrent = Math.round(message.battery_current * 100) / 100;
    batRemain = Math.round(message.battery_remaining * 100) / 100;
    // ARM状態
    if(message.armed){
        document.getElementById('armstatus').innerHTML = "ARMED";
        document.getElementById('modewrap1').style.backgroundColor = '#FF0000';
    }
    else{
        document.getElementById('armstatus').innerHTML = "DISARMED";
        document.getElementById('modewrap1').style.backgroundColor = '#000000';
    }
    // GPS情報
    document.getElementById('gpsfix').innerHTML = message.gps_fix_type;
    document.getElementById('satcnt').innerHTML = message.gps_num_sat.toString();
    // Vehicleの姿勢
    droneRoll = message.roll;
    dronePitch = message.pitch;
    // Vehicleの対地速度
    gndSpeed = round((Math.sqrt(message.vx ** 2 + message.vy ** 2)*100),2);
    // ランディング状態
    document.getElementById('systemstatus').innerHTML = message.landed_state;
    if(message.landed_state=='IN_AIR')
        document.getElementById('modewrapland').style.backgroundColor = '#4169e1';
    else if ((message.landed_state=='TAKING_OFF') || (message.landed_state=='LANDING'))  
        document.getElementById('modewrapland').style.backgroundColor = '#008000';
    else        
        document.getElementById('modewrapland').style.backgroundColor = '#000000';
});

//////////////////////////////////////////////////////////////////////////////////////
// 少数点位置を取得
const decimalPart = (num, decDigits) => {
    let decPart = num - ((num >= 0) ? Math.floor(num) : Math.ceil(num));
    return decPart.toFixed(decDigits);
}

//////////////////////////////////////////////////////////////////////////////////////
// Vehicleのバージョン情報を取得するサブスクライバ 
var sub_version = new ROSLIB.Topic({
    ros: this.ros, name: 'vehicle_version',
    messageType: 'std_msgs/String'
});
sub_version.subscribe(message => {
    let res = message.data;
    document.getElementById('vehicleVer').innerHTML = res.toString();
    //console.log('Version:' + res);
});

//////////////////////////////////////////////////////////////////////////////////////
// Vehicleの現在の状態を取得するサブスクライバ 
var sub_status = new ROSLIB.Topic({
    ros: this.ros, name: 'drone_status',
    messageType: 'std_msgs/String'
});
sub_status.subscribe(message => {
    let res = message.data;
    document.getElementById('mmsg').innerHTML = res.toString();
    // 目的地に到着したらピンを削除する
    if (res.toString() === "移動終了") {
        setMove2XClr(0);
        setMove2YClr(0);
        // 移動ボタン多重クリック防止フラグをディセーブルにする
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "シンプル移動END") {
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "ステップ連続") {
        clear_step1_info();
        clear_step2_info();
        clear_step3_info();
    }
    else if (res.toString() === "ステップ１開始") {
        clear_step1_info();
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "ステップ１判定") {
        flgMoveBtnPushed = false;
    }
    // ここで判定結果をキャンバスに表示する
    else if (res.toString() === "Step1JdgEnd"){
        console.log("STEP1結果を別ページに表示します。");
        // 別ウィンドウにステップ１の結果イメージを表示する。
        openstep1imgpage();
    }
    else if (res.toString() === "ステップ１移動") {
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "ステップ１終了") {
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "ステップ２開始") {
        clear_step2_info();
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "ステップ２判定") {
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "ステップ２移動開始") {
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "ステップ２移動完了") {
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "ステップ２終了") {
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "ステップ３開始") {
        clear_step3_info();
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "ステップ３判定") {
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "ステップ３移動") {
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "ステップ３終了") {
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "ブレーキ！") {
        console.log("Brake!");
        flgMoveBtnPushed = false;
    }
    else if (res.toString() === "ガイドモードに設定") {
        clear_step1_info();
        clear_step2_info();
        clear_step3_info();
    }
});

//////////////////////////////////////////////////////////////////////////////////////
// ステップ１の各種情報をクリア
const clear_step1_info = () => {
}

//////////////////////////////////////////////////////////////////////////////////////
// ステップ２の各種情報をクリア
const clear_step2_info = () => {
    //function clear_step2_info(){
}

//////////////////////////////////////////////////////////////////////////////////////
// ステップ３の各種情報をクリア
const clear_step3_info = () => {
}

//////////////////////////////////////////////////////////////////////////////////////
// ターゲットに問い合わせを送信するパブリッシャ 
var pub_sndinq = new ROSLIB.Topic({ 
    ros: this.ros, name: 'inq_req', 
    messageType: 'std_msgs/String' 
});
// Use for send/recv inq between client server
const sendinq = () => {
    let comment = "hello";
    let str = new ROSLIB.Message({ data: comment });
    pub_sndinq.publish(str);
};
setInterval(() => { sendinq(); }, 500);

//////////////////////////////////////////////////////////////////////////////////////
// ターゲットからの返答情報（日時時間）を受信するサブスクライバ 
var sub_inqack = new ROSLIB.Topic({ 
    ros: this.ros, name: 'inq_ack', 
    messageType: 'std_msgs/String' 
});
sub_inqack.subscribe(message => {
    document.getElementById('cntstatus').innerHTML = '接続中: ' + message.data.toString();
    document.getElementById('cntstatus').style.backgroundColor = '#008000';
});


//////////////////////////////////////////////////////////////////////////////////////
// ターゲットにダイレクトメッセージを送信するパブリッシャ  
var pub_dcmd = new ROSLIB.Topic({ 
    ros: this.ros, name: 'drone_ddcmd', 
    messageType: 'std_msgs/String' 
});
const droneDcmd = cmd => {
    let str = new ROSLIB.Message({ data: cmd });
    console.log(str);
    pub_dcmd.publish(str);
};

//////////////////////////////////////////////////////////////////////////////////////
// ターゲットにVehicle制御コマンドを送信するパブリッシャ  
var pub_cmd = new ROSLIB.Topic({ 
    ros: this.ros, name: 'commander', 
    messageType: 'std_msgs/String' 
});
const cmdpub = pubcmd => {
    let str = new ROSLIB.Message({ data: pubcmd });
    pub_cmd.publish(str);
    if ((pubcmd == 'RTL_MODE') || (pubcmd == 'LAND_MODE')) {
        document.getElementById('takeoffBtn').disabled = true;
    }
};

//////////////////////////////////////////////////////////////////////////////////////
// イベントハンドラ：Yaw方向の回転 for PX4
const px4_droneCtrl = () => {
    console.log("Yaw Rotation")
    let elements;
    let len;
    let checkValue1;
    let checkValue2;
    elements = document.getElementsByName('rottype');
    len = elements.length;
    checkValue1 = '';
    for (var i = 0; i < len; i++) {
        if (elements.item(i).checked) {
            checkValue1 = elements.item(i).value;
        }
    }
    console.log(checkValue1 + ',' + checkValue2);
    console.log("Yaw Rotation");
    if (checkValue1 === "YAW_ABS") {
        droneCtrl('YAW_ROT_ABS');
    }
    else if (checkValue1 === "YAW_REL") {
        droneCtrl('YAW_ROT_REL');
    }
    // スライダをクリア
    setMove2XClr(1); // 引数1の場合目的地フラグを「クリア」させる
    setMove2YClr(1); // 引数1の場合目的地フラグを「クリア」させる
}
//////////////////////////////////////////////////////////////////////////////////////
// イベントハンドラ：Yaw方向の回転 for Ardupilot
const ard_droneCtrl = () => {
    console.log("Yaw Rotation")
    let elements;
    let len;
    let checkValue1;
    let checkValue2;
    elements = document.getElementsByName('rottype');
    len = elements.length;
    checkValue1 = '';
    for (var i = 0; i < len; i++) {
        if (elements.item(i).checked) {
            checkValue1 = elements.item(i).value;
        }
    }
    elements = document.getElementsByName('rotmetype');
    len = elements.length;
    checkValue2 = '';
    for (var i = 0; i < len; i++) {
        if (elements.item(i).checked) {
            checkValue2 = elements.item(i).value;
        }
    }
    console.log(checkValue1 + ',' + checkValue2);
    if (checkValue2 === "YAW_ROT_TYPEA") {
        console.log("Yaw Rotation Type A");
        if (checkValue1 === "YAW_ABS") {
            droneCtrl('YAW_ROT_ABS');
        }
        else if (checkValue1 === "YAW_REL") {
            droneCtrl('YAW_ROT_REL');
        }
    }
    else if (checkValue2 === "YAW_ROT_TYPEB") {
        console.log("Yaw Rotation Type B");
        if (checkValue1 === "YAW_ABS") {
            droneCtrl('YAW_ROT_ABS_B');
        }
        else if (checkValue1 === "YAW_REL") {
            droneCtrl('YAW_ROT_REL_B');
        }
    }
    // スライダをクリア
    setMove2XClr(1); // 引数1の場合目的地フラグを「クリア」させる
    setMove2YClr(1); // 引数1の場合目的地フラグを「クリア」させる
}

//////////////////////////////////////////////////////////////////////////////////////
// 回転のタイプを設定
const radio_rot_changed = () => {
    document.getElementById('yawrotvalue').innerHTML = 0;
    let elements = document.getElementsByName('rottype');
    let len = elements.length;
    let checkValue = '';
    for (let i = 0; i < len; i++) {
        if (elements.item(i).checked) {
            checkValue = elements.item(i).value;
        }
    }
    elements = document.getElementById('yawrotate_deg');
    if (checkValue === "YAW_ABS") {
        console.log("SET_ABS!");
        elements.min = 0;
        elements.max = 359;
        elements.step = 1;
        elements.value = 0;
    }
    else if (checkValue === "YAW_REL") {
        console.log("SET_REL!");
        elements.min = -180;
        elements.max = 180;
        elements.step = 1;
        elements.value = 0;
    }
}

//////////////////////////////////////////////////////////////////////////////////////
// 回転角度（絶対角度／相対角度）設定
const radio_rotmetype_changed = () => {
    let elements = document.getElementsByName('rotmetype');
    let len = elements.length;
    let checkValue = '';
    for (let i = 0; i < len; i++) {
        if (elements.item(i).checked) {
            checkValue = elements.item(i).value;
        }
    }
    elements = document.getElementById('yawrotate_deg');
    if (checkValue === "YAW_ABS") {
        console.log("SET_ABS!");
        elements.min = 0;
        elements.max = 359;
        elements.step = 1;
        elements.value = 0;
    }
    else if (checkValue === "YAW_REL") {
        console.log("SET_REL!");
        elements.min = -180;
        elements.max = 180;
        elements.step = 1;
        elements.value = 0;
    }
}

//////////////////////////////////////////////////////////////////////////////////////
// 上昇・降下速度を設定
// const getudspeed = () => {
//     let elements = document.getElementsByName('speed_ud');
//     let len = elements.length;
//     let checkValue = '';
//     for (let i = 0; i < len; i++) {
//         if (elements.item(i).checked) {
//             checkValue = elements.item(i).value;
//         }
//     }
//     return checkValue;
// }

//////////////////////////////////////////////////////////////////////////////////////
// Vehicle制御コマンドメッセージのパブリッシャ
var pub_ctrl = new ROSLIB.Topic({
    ros: this.ros, name: 'drone_ctrl',
    messageType: 'drone_ctrl/DroneCtrl'
});
const droneCtrl = (mode) => {
    let scode = 0;
    console.log('send droneCtrl: ' + mode + ':' + droneCntAlt);

    let elements = document.getElementsByName('flyopmode');
    let len = elements.length;
    let cv_flyopmode;
    for (let i = 0; i < len; i++) {
        if (elements.item(i).checked) {
            cv_flyopmode = elements.item(i).value;
            console.log(cv_flyopmode);
        }
    }

    if (mode === "ARM") {
        document.getElementById('mmsg').innerHTML = 'ARM';
        document.getElementById('takeoffBtn').disabled = false;
    }
    else if (mode === "TAKEOFF") {
        //let alt = document.getElementById('distance_Alt').value;
        let alt = document.getElementById('takeoff_alt_in').value;
        document.getElementById('mmsg').innerHTML = 'テイクオフ: ' + alt.toString() + 'm';
        pubDroneCtrl[9] = alt;
   }
    else if (mode === "ARMTOFF") {
        let alt = document.getElementById('distance_Alt').value;
        document.getElementById('mmsg').innerHTML = 'ARM+テイクオフ: ' + alt.toString() + 'm';
        pubDroneCtrl[9] = alt;
    }
    else if (mode === "STEP1JS") {
        if (droneCntAlt > 0.5) {
            console.log('STEP1判定開始');
            document.getElementById('mmsg').innerHTML = 'STEP1判定開始';
        }
        ognLat = cntLat;
        ognLon = cntLon;
    }
    else if (mode === "STEP1MS") {
        if (droneCntAlt > 0.5) {
            console.log('STEP1移動');
            document.getElementById('mmsg').innerHTML = 'STEP1移動';
            pubDroneCtrl[2] = document.getElementById('pixel_dx').value;
            pubDroneCtrl[3] = document.getElementById('pixel_dy').value;
            pubDroneCtrl[4] = droneDir;
            pubDroneCtrl[5] = document.getElementById('speed_gs').value;
        }
        ognLat = cntLat;
        ognLon = cntLon;
        flgMoveBtnPushed = true;
    }
    else if (mode === "STEP2") {
        if (droneCntAlt > 0.5) {
            console.log('STEP2移動');
            document.getElementById('mmsg').innerHTML = 'STEP2移動';
            pubDroneCtrl[2] = document.getElementById('pixel_dx3d').value;
            pubDroneCtrl[3] = document.getElementById('pixel_dy3d').value;
            pubDroneCtrl[4] = droneDir;
            pubDroneCtrl[5] = document.getElementById('speed_gs').value;
            pubDroneCtrl[10] = document.getElementById('dist_dz3d').value;
        }
        ognLat = cntLat;
        ognLon = cntLon;
        flgMoveBtnPushed = true;
    }
    else if ((mode === "STEP3")||(mode === "SETALT")) {
        if (droneCntAlt > 0.5) {
            console.log('STEP3移動');
            document.getElementById('mmsg').innerHTML = 'STEP3移動';
            alt = document.getElementById('distance_Alt').value;
            pubDroneCtrl[9] = alt;
            pubDroneCtrl[5] = document.getElementById('speed_ud').value;
            pubDroneCtrl[11] = document.getElementById('distance_SAlt').value;
            console.log(pubDroneCtrl[5], pubDroneCtrl[11]);
        }
        ognLat = cntLat;
        ognLon = cntLon;
        flgMoveBtnPushed = true;
    }
    else if (mode === "MOVE_CLK") { // Move to set point from to
        if (droneCntAlt > 0.5) {
            console.log('地図上の目的地へ移動');
            scode = 1002; // Velocity
            if( mapClickFlg ){
                // マップクリック検出フラグがtrueの場合に移動を開始する
                document.getElementById('mmsg').innerHTML = 'マップ上の指定目的地へ移動';
                pubDroneCtrl[0] = __statPointY;
                pubDroneCtrl[1] = __statPointX;
                pubDroneCtrl[2] = __destPointY;
                pubDroneCtrl[3] = __destPointX;
                pubDroneCtrl[4] = droneDir;
                pubDroneCtrl[5] = document.getElementById('speed_gs').value;

                console.log("Dest by Map: " + 
                    pubDroneCtrl[0].toString() + ',' + 
                    pubDroneCtrl[1].toString() + ',' + 
                    pubDroneCtrl[2].toString() + ',' + 
                    pubDroneCtrl[3].toString() + ',' + 
                    pubDroneCtrl[4].toString() + ',' + 
                    pubDroneCtrl[5].toString()
                );
                __statPointX = __destPointX;
                __statPointY = __destPointY;
                // マップクリック検出フラグをfalseにする
                mapClickFlg = false;
            }
            else{
                // マップをクリックしていない場合、移動しない。
                pubDroneCtrl[0] = 0;
                pubDroneCtrl[1] = 0;
                pubDroneCtrl[2] = 0;
                pubDroneCtrl[3] = 0;                    
            }
            pubDroneCtrl[11] = document.getElementById('min_dis2_Obj').value;;
            console.log('地図上の目的地へ移動します');
            ognLat = cntLat;
            ognLon = cntLon;
            flgMoveBtnPushed = true;
        }
        else {
            console.log('!!!!!!地上高さが足りませんもしくはARMしていません');
            document.getElementById('mmsg').innerHTML = '地上高さエラー';
            mode = "NONE";
            document.getElementById("mmsg").style.color = "#ffffff";
            document.getElementById("mmsg").style.backgroundColor = '#000000';
        }
    }
    else if (mode === "MOVE_SLD") { // Move to set point from to
        if (droneCntAlt > 0.5) {
            console.log('スライダ指定距離分目的地へ移動');
            scode = 2002; // Velocity
            document.getElementById('mmsg').innerHTML = 'スライダ指定距離分目的地へ移動';
            pubDroneCtrl[0] = 0;
            pubDroneCtrl[1] = 0;          
            pubDroneCtrl[2] = document.getElementById('move2_xin').value;
            pubDroneCtrl[3] = document.getElementById('move2_yin').value;
            pubDroneCtrl[4] = droneDir;
            pubDroneCtrl[5] = document.getElementById('speed_gs').value;
            console.log(pubDroneCtrl[2] + ',' + pubDroneCtrl[3] + ',' + pubDroneCtrl[5]);
            // マップクリック検出フラグをfalseにする。falseにしないとマップクリックに切り替えてクリックをしない場合に
            // とんでもない場所に移動する
            mapClickFlg = false;
            // pubDroneCtrl[11] = document.getElementById('min_dis2_Obj').value;;
            console.log('地図上の目的地へ移動します');
            ognLat = cntLat;
            ognLon = cntLon;
            flgMoveBtnPushed = true;
        }
        else {
            console.log('!!!!!!地上高さが足りませんもしくはARMしていません');
            document.getElementById('mmsg').innerHTML = '地上高さエラー/ボタン多重クリックフラグがクリアされていません';
            mode = "NONE";
            document.getElementById("mmsg").style.color = "#ffffff";
            document.getElementById("mmsg").style.backgroundColor = '#000000';
        }
    }
    else if (mode === "SET_SPEED") {
        document.getElementById('mmsg').innerHTML = '対地速度設定';
        pubDroneCtrl[5] = document.getElementById('speed_gs').value;
        console.log("SPEED=" + pubDroneCtrl[5]);
    }
    else if ((mode === "YAW_ROT_ABS") || (mode === "YAW_ROT_ABS_B")){
        elements = document.getElementsByName('rottype');
        len = elements.length;        
        let checkValue1 = '';
        for (var i = 0; i < len; i++) {
            if (elements.item(i).checked) {
                checkValue1 = elements.item(i).value;
            }
        }
        document.getElementById('mmsg').innerHTML = 'YAW回転（絶対角度）';
        var rotabs = document.getElementById('yawrotate_deg').value;
        if (rotabs > 360) {
            rotabs = 0;
            document.getElementById('yawrotate_abs').value = 0;
        }
        else if ((rotrel > 180) || (rotrel <= 360)) {
            rotrel -= 360;
        }
        pubDroneCtrl[4] = rotabs;
    }
    else if((mode === "YAW_ROT_REL") || (mode === "YAW_ROT_REL_B")){
        elements = document.getElementsByName('rottype');
        len = elements.length;        
        let checkValue1 = '';
        for (var i = 0; i < len; i++) {
            if (elements.item(i).checked) {
                checkValue1 = elements.item(i).value;
            }
            pubDroneCtrl[4] = rotrel;
        }
        document.getElementById('mmsg').innerHTML = 'YAW回転（相対角度）';
        var rotrel = document.getElementById('yawrotate_deg').value;
        if ((rotrel > 180) || (rotrel < -180)) {
            rotrel = 0;
        }
            pubDroneCtrl[4] = rotrel;
    }
    // Vehicle制御コマンドメッセージ
    const mapInfo = new ROSLIB.Message({
        'mode': mode,               // 0
        'scode': scode,             // 1
        'sx': pubDroneCtrl[0],      // 2
        'sy': pubDroneCtrl[1],      // 3
        'dx': pubDroneCtrl[2],      // 4
        'dy': pubDroneCtrl[3],      // 5
        'yawrot': pubDroneCtrl[4],  // 6
        'speed': pubDroneCtrl[5],   // 7
        'lat': pubDroneCtrl[6],     // 8
        'long': pubDroneCtrl[7],    // 9
        'alt': pubDroneCtrl[8],     // 10
        'setalt': pubDroneCtrl[9],  // 11
        'res1': pubDroneCtrl[10],   // 12
        'res2': pubDroneCtrl[11]    // 13
    });
    console.log('publish command');
    pub_ctrl.publish(mapInfo);
};

//////////////////////////////////////////////////////////////////////////////////////
// 対象物までの距離トピックを取得するサブスクライバ
var sub_depth_dist = new ROSLIB.Topic({
    ros: this.ros, name: "depth_dist",
    messageType: 'std_msgs/Float32'
});
sub_depth_dist.subscribe(function (message) {
    document.getElementById('stp2_dist').innerHTML = message.data.toString();
});

//////////////////////////////////////////////////////////////////////////////////////
// ステップ３のスコアを取得するサブスクライバ
var sub_step3_score = new ROSLIB.Topic({
    ros: this.ros, name: "step3_score",
    messageType: 'std_msgs/Float32'
});
sub_step3_score.subscribe(function (message) {
    document.getElementById('stp3_score').innerHTML = message.data.toString();
});

//////////////////////////////////////////////////////////////////////////////////////
// ステップ１メッセージ
// var sub_step1msg = new ROSLIB.Topic({
//     ros: this.ros, name: "step1msg",
//     messageType: 'std_msgs/String'
// });
// sub_step1msg.subscribe(function (message) {

// });

//////////////////////////////////////////////////////////////////////////////////////
// ステップ２メッセージ
// var sub_step2msg = new ROSLIB.Topic({
//     ros: this.ros, name: "step2msg",
//     messageType: 'std_msgs/String'
// });
// sub_step2msg.subscribe(function (message) {

// });

//////////////////////////////////////////////////////////////////////////////////////
// ドア判定結果メッセージ
// var sub_door_result_msg = new ROSLIB.Topic({
//     ros: this.ros, neme: 'door_result_msg',
//     messageType: 'std_msgs/String'
// });
// sub_door_result_msg.subscribe(function (message) {

// });

//////////////////////////////////////////////////////////////////////////////////////
// ドア判定のスコアを取得するサブスクライバ
var sub_door_score = new ROSLIB.Topic({
    ros: this.ros, name: 'door_result_scr',
    messageType: 'std_msgs/Float32'
});
sub_door_score.subscribe(function (message) {
    document.getElementById('stp2_score').innerHTML = message.data.toString();
});

//////////////////////////////////////////////////////////////////////////////////////
// ドアまでの距離
var sub_door_dist = new ROSLIB.Topic({
    ros: this.ros, name: 'door_distance',
    messageType: 'std_msgs/Float32'
});
sub_door_dist.subscribe(function (message) {
});

//////////////////////////////////////////////////////////////////////////////////////
// ドアまでのCCX
var sub_door_ccx = new ROSLIB.Topic({
    ros: this.ros, name: 'door_ccx',
    messageType: 'std_msgs/Int32'
});
sub_door_ccx.subscribe(function (message) {
    document.getElementById('stp2_x').innerHTML = message.data.toString();
});

//////////////////////////////////////////////////////////////////////////////////////
// ドアまでのCCY
var sub_door_ccy = new ROSLIB.Topic({
    ros: this.ros, name: 'door_ccy',
    messageType: 'std_msgs/Int32'
});
sub_door_ccy.subscribe(function (message) {
    document.getElementById('stp2_y').innerHTML = message.data.toString();
});

let emt_slt = document.getElementById('slottle_meter');
let ctx_slt = emt_slt.getContext("2d");
let emt_rpy = document.getElementById('rpy_meter');
let ctx_rpy = emt_rpy.getContext("2d");
let emt_cps = document.getElementById('dir_meter');
let ctx_cps = emt_cps.getContext("2d");
let emt_hgt = document.getElementById('hgt_meter');
let ctx_hgt = emt_hgt.getContext("2d");
const rpy_r = 40;

let flgStartInterval = true;
//////////////////////////////////////////////////////////////////////////////////////
// 一定間隔で簡易GCSの画面に表示する情報を更新する
// 表示する情報は「drone_info」メッセージでROSトピックで配信される
setInterval(() => {
    if (droneCntAlt > 1.0) {
        ctx_hgt.strokeStyle = 'yellow';
        enableControlBtn();
        document.getElementById("mmsg").style.color = "#000000";
        document.getElementById("mmsg").style.backgroundColor = '#ffff00';
    }
    else {
        ctx_hgt.strokeStyle = 'gray';
        disableControlBtn();
        document.getElementById("mmsg").style.color = "#ffffff";
        document.getElementById("mmsg").style.backgroundColor = '#000000';
    }
    if(flgStartInterval){
        // ------------------------------------------------------------
        // モータ出力メータ
        let x_offset = 100;
        let y_base = 0;
        let y_offset = 30;
    	ctx_slt.fillStyle = '#eeeeee';
    	ctx_slt.clearRect(0, 0, emt_slt.width, emt_slt.height);
    	ctx_slt.font = "16px arial";
        ctx_slt.font = "26px arial";
        ctx_slt.fillText("速度", 0,  y_base+y_offset*1+4);
        ctx_slt.fillText("電圧", 0,  y_base+y_offset*2+4);
        ctx_slt.fillText("電流", 0,  y_base+y_offset*3+4);
        ctx_slt.fillText("残量", 0,  y_base+y_offset*4+4);
        ctx_slt.fillText((gndSpeed/100*3600/1000).toFixed(3)+' km/h', x_offset, y_base+y_offset*1+4);
        ctx_slt.fillText(batPower.toFixed(2)+" V", x_offset, y_base+y_offset*2+4);
        ctx_slt.fillText(batCurrent.toFixed(2)+" mA", x_offset, y_base+y_offset*3+4);
        if(batRemain>=0.8) ctx_slt.fillStyle = 'lightgreen';
        else if(batRemain>=0.7) ctx_slt.fillStyle = 'yellow';
        else ctx_slt.fillStyle = 'red';
        ctx_slt.fillText((batRemain*100).toFixed(2)+" %", x_offset, y_base+y_offset*4+4);
        ctx_slt.fillStyle = 'white';
        // ピッチ・ロールメータ
        let rpy_height = emt_rpy.height - 10
        ctx_rpy.fillStyle = 'white';
        ctx_rpy.clearRect(0, 0, emt_rpy.width, emt_rpy.height);
        ctx_rpy.font = "14px arial";
        ctx_rpy.fillText("ピッチ   ロール", 5, emt_rpy.height - 20);
        ctx_rpy.fillText((Math.round(dronePitch * 1000) / 1000).toFixed(2)+'°', 5, emt_rpy.height - 5);
        ctx_rpy.fillText((Math.round(droneRoll * 1000) / 1000).toFixed(2)+'°', 55, emt_rpy.height - 5);
        ctx_rpy.save();
        ctx_rpy.beginPath();
        ctx_rpy.lineWidth = 1;
        ctx_rpy.strokeStyle = 'white';
        ctx_rpy.translate(emt_rpy.width / 2, rpy_height / 2);
        ctx_rpy.rotate(droneRoll * Math.PI / 180);
        ctx_rpy.translate(-emt_rpy.width / 2, -rpy_height / 2);
        ctx_rpy.arc(emt_rpy.width / 2, emt_rpy.width / 2, rpy_r, 0 * Math.PI / 180, 360 * Math.PI / 180, 360 * Math.PI / 180, false);
        ctx_rpy.moveTo(emt_rpy.width / 2 - rpy_r, rpy_height / 2);
        ctx_rpy.lineTo(emt_rpy.width / 2 + rpy_r, rpy_height / 2);
        ctx_rpy.moveTo(emt_rpy.width / 2, rpy_height / 2 - rpy_r);
        ctx_rpy.lineTo(emt_rpy.width / 2, rpy_height / 2 + rpy_r);
        ctx_rpy.stroke();
        ctx_rpy.beginPath();
        ctx_rpy.lineWidth = 8;
        if (droneCntAlt > 1.0)
            ctx_rpy.strokeStyle = 'yellow';
        else
            ctx_rpy.strokeStyle = 'gray';
        if ((dronePitch > 0) && (dronePitch < 90)) {
            ctx_rpy.moveTo(emt_rpy.width / 2 - rpy_r / 2, rpy_height / 2 - dronePitch / 2);
            ctx_rpy.lineTo(emt_rpy.width / 2 + rpy_r / 2, rpy_height / 2 - dronePitch / 2);
        }
        else if ((dronePitch < 0) && (dronePitch > -90)) {
            ctx_rpy.moveTo(emt_rpy.width / 2 - rpy_r / 2, rpy_height / 2 + dronePitch / 2);
            ctx_rpy.lineTo(emt_rpy.width / 2 + rpy_r / 2, rpy_height / 2 + dronePitch / 2);
        }
        ctx_rpy.stroke();
        ctx_rpy.restore();
        // 高度メータ
        let hgt_height = emt_hgt.height - 40
        ctx_hgt.clearRect(0, 0, emt_hgt.width, emt_hgt.height);
        ctx_hgt.font = "12px arial";
        ctx_hgt.fillStyle = 'yellow';
        ctx_hgt.fillText("対地高度", 0, emt_hgt.height - 20);
        ctx_hgt.font = "14px arial";
        ctx_hgt.fillText((Math.round(droneCntAlt * 100) / 100).toFixed(2)+"m", 0, emt_hgt.height - 1);
        ctx_hgt.fillkeStyle = 'white';
        ctx_hgt.font = "12px arial";
        for (i = 1; i < 5 + 1; i++) {
            ctx_hgt.strokeText(((i - 1) * 10).toString(), 0, hgt_height / 5 * (5 - i + 1));
            ctx_hgt.save();
            ctx_hgt.beginPath();
            ctx_hgt.lineWidth = 1;
            ctx_hgt.strokeStyle = 'white';
            ctx_hgt.moveTo(0, hgt_height / 5 * i);
            ctx_hgt.lineTo(emt_hgt.width, hgt_height / 5 * i);
            ctx_hgt.stroke();
        }
        ctx_hgt.save();
        ctx_hgt.beginPath();
        ctx_hgt.lineWidth = 20;
        if (droneCntAlt > 1.0)
            ctx_hgt.strokeStyle = 'yellow';
        else
            ctx_hgt.strokeStyle = 'gray';
        if (droneCntAlt > 50) {
            ctx_hgt.strokeStyle = 'red';
            ctx_hgt.moveTo(35, hgt_height);
            ctx_hgt.lineTo(35, hgt_height - (droneCntAlt / 28) * 100);
        }
        else {
            ctx_hgt.strokeStyle = 'yellow';
            ctx_hgt.moveTo(35, hgt_height);
            ctx_hgt.lineTo(35, hgt_height - (droneCntAlt / 28) * 100);
        }
        ctx_hgt.stroke();
        ctx_hgt.restore();
        // コンパスメータ
        let cps_height = emt_cps.height - 10
        ctx_cps.clearRect(0, 0, emt_cps.width, emt_cps.height);
        ctx_cps.font = "16px arial";
        ctx_cps.fillStyle = 'white';
        ctx_cps.fillText("N", emt_cps.width / 2 - 6, 25);
        ctx_cps.fillText("E", emt_cps.width - 25, cps_height / 2 + 4);
        ctx_cps.fillText("S", emt_cps.width / 2 - 6, cps_height - 11);
        ctx_cps.fillText("W", 15, cps_height / 2 + 4);
        ctx_cps.fillText("方位: " + headingAngle.toFixed(2)+'°', 5, emt_cps.height - 5);
        ctx_cps.save();
        ctx_cps.beginPath();
        ctx_cps.lineWidth = 1;
        ctx_cps.strokeStyle = 'white';
        ctx_cps.translate(emt_cps.width / 2, cps_height / 2);
        ctx_cps.translate(-emt_cps.width / 2, -cps_height / 2);
        ctx_cps.arc(emt_cps.width / 2, emt_cps.width / 2, rpy_r, 0 * Math.PI / 180, 360 * Math.PI / 180, 360 * Math.PI / 180, false);
        ctx_cps.moveTo(emt_cps.width / 2 - rpy_r, cps_height / 2);
        ctx_cps.lineTo(emt_cps.width / 2 + rpy_r, cps_height / 2);        
        ctx_cps.moveTo(emt_cps.width / 2, cps_height / 2 - rpy_r);
        ctx_cps.lineTo(emt_cps.width / 2, cps_height / 2 + rpy_r);
        ctx_cps.stroke();
        ctx_cps.save();
        ctx_cps.beginPath();
        ctx_cps.lineWidth = 1;
        ctx_cps.strokeStyle = 'red';
        ctx_cps.translate(emt_cps.width / 2, cps_height / 2);
        ctx_cps.rotate(droneDir * Math.PI / 180);
        ctx_cps.translate(-emt_cps.width / 2, -cps_height / 2);
        ctx_cps.stroke();
        ctx_cps.beginPath();
        ctx_cps.lineWidth = 6;
        if (droneCntAlt > 1.0){
            ctx_cps.strokeStyle = 'yellow';
        }
        else{
            ctx_cps.strokeStyle = 'gray';
        }
        ctx_cps.moveTo(emt_cps.width / 2 + rpy_r / 3, cps_height / 2);
        ctx_cps.lineTo(emt_cps.width / 2, cps_height / 2 - rpy_r);
        ctx_cps.moveTo(emt_cps.width / 2, cps_height / 2 - rpy_r);
        ctx_cps.lineTo(emt_cps.width / 2 - rpy_r / 3, cps_height / 2);
        ctx_cps.moveTo(emt_cps.width / 2, cps_height / 2 - rpy_r);
        ctx_cps.lineTo(emt_cps.width / 2, cps_height / 2 + rpy_r);
        ctx_cps.stroke();
        ctx_cps.restore();
    }
    else{
        ctx_cps.strokeStyle = 'gray';
    }
}, 300);

//////////////////////////////////////////////////////////////////////////////////////
// 全ての飛行制御ボタンを無効にする
const disableControlBtn = () => {
    document.getElementById('bnt_step1js').disabled = true;
    document.getElementById('bnt_step1js').value = '無効(低高度/非ARM)';
    document.getElementById('bnt_step1ms').disabled = true;
    document.getElementById('bnt_step1ms').value = '無効(低高度/非ARM)';
    document.getElementById('bnt_step2').disabled = true;
    document.getElementById('bnt_step2').value = '無効(低高度/非ARM)';
    document.getElementById('bnt_step3').disabled = true;
    document.getElementById('bnt_step3').value = '無効(低高度/非ARM)';
    document.getElementById('bnt_brake').disabled = true;
    document.getElementById('bnt_brake').value = '無効(低高度/非ARM)';
    document.getElementById('bnt_land').disabled = true;
    document.getElementById('bnt_land').value = '無効(低高度/非ARM)';
    document.getElementById('bnt_step_all').disabled = true;
    document.getElementById('bnt_step_all').value = '無効(低高度/非ARM)';
}

//////////////////////////////////////////////////////////////////////////////////////
// 全ての飛行制御ボタンを有効にする
const enableControlBtn = () => {
    document.getElementById('bnt_step1js').disabled = false;
    document.getElementById('bnt_step1js').value = 'ステップ１判定開始';
    document.getElementById('bnt_step1ms').disabled = false;
    document.getElementById('bnt_step1ms').value = 'ステップ１移動開始';
    document.getElementById('bnt_step2').disabled = false;
    document.getElementById('bnt_step2').value = 'ステップ２開始';
    document.getElementById('bnt_step3').disabled = false;
    document.getElementById('bnt_step3').value = 'ステップ３開始';
    document.getElementById('bnt_brake').disabled = false;
    document.getElementById('bnt_brake').value = '移動停止';
    document.getElementById('bnt_land').disabled = false;
    document.getElementById('bnt_land').value = 'セーフLAND開始';
    document.getElementById('bnt_step_all').disabled = false;
    document.getElementById('bnt_step_all').value = 'ステップ連続開始';
}