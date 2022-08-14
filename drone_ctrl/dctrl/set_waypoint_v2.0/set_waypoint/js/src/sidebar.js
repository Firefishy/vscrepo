
$(function() {
	// sidebar collapse
	$('#btn_list').on('click', function() {
		$('#btn_list').toggleClass('side_btnc');
		$('.sidebar_left').toggleClass('sidebar_leftc');
		$('.layer-icon').toggleClass('layer-iconc');
		$('.layer-nav').toggleClass('layer-navc');
	});
	
	// レイヤをクリックする
	$("#btn_layer").click(function(){
		if ($("#layer_nav").css('display') == 'block') {
			$("#layer_nav").css('display','none');
		} else {
			$("#layer_nav").css('display','block');
	
		}
	});
	// レイヤナビ上のカーソル移動
	$("#layer_nav").mouseout(function(){
		$("#layer_nav").css('display','none');
	});
	$("#layer_nav").mouseover(function(){
		$("#layer_nav").css('display','block');
	});
	
	// レイヤナビのクリック レイヤ切り替え
	$("#layer_more").click(function() {
		alert("more");
	});

});
