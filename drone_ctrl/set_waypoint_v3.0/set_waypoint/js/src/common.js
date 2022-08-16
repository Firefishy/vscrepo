//ログインしない場合、エラー画面へ
if (sessionStorage.length == 0) {
    //location.href = 'session_error.html';
}

//共通のヘッダ
$.ajax({
    url: 'header.html', 
    cache: false,
    async: true,
    dataType: 'html',
    timeout: 10000
}).done(function(html) {
    $('#header').html(html);
    if(sessionStorage.getItem('username') != ''){
		var last_login_datetime = '2022/04/07 18:09:02.400'  //ログイン日時の取得を入れるならここ
	    $('.lastlogin-datetime').text(`最終ログイン日時:${last_login_datetime}`); // TODO
		let userName = sessionStorage.getItem('username');
		if (userName && userName.length > 16) {
			$("#login_user").css("width", "");
		}
		$("#login_user").text(`${userName} 様`);

        // 飛行中のドローンがある場合、アラートを表示
		$("#drone_in_flight").append(`<i class="fas fa-exclamation-triangle" style="color:red;"></i>`);
    } else {
        $('lastlogin_datetime').css('display','none');//表示欄のinline-blockを解除
    }
 
    $("#logoout").on('click', function() {
    	var modalbody =
			`
			<div style="text-align:center">ログアウトします。</div>
			<div style="text-align:center;">よろしいですか？</div>
	        `
    	//モーダルに表示
    	$('#logout-modal-body').html(modalbody);
		$('#logout-modal').modal('toggle');
		
	});
	$("#logoout-ok-btn").on('click', function() {
		location.href="../index.html";
		sessionStorage.clear();
	});
    
    var role = sessionStorage.getItem('role');
	// ゲストの場合
	if(role == 'guest'){
		// TODO　フライト状況画面のみ表示？
	}
});

/* //共通のフッター
$.ajax({
    url: 'footer.html', 
    cache: false,
    async: true,
    dataType: 'html',
    timeout: 10000
}).done(function(html) {
    $('#footer').html(html);
}); */

/*// ドローンデータの読み込み
var droneInfoList = JSON.parse(sessionStorage.getItem('droneInfo'));
if (!droneInfoList) {
	$.ajax({
		type: "GET",
		url: "drone_data.json",
		dataType: "json",
		async: false
	}).done(
		function(json) {
			// 読み込み成功時の処理
			console.log("ドローンデータの読み込みに成功しました。");
			Object.keys(json).forEach((key) => {
				// オブジェクトや値をJSON文字列に変換してセッションに保存する。
				sessionStorage.setItem(key, JSON.stringify(json[key]));
			});
		}
	).fail(function() {
		// 読み込み失敗時の処理
		console.log("ドローンデータの読み込みに失敗しました。");
	});
}*/



