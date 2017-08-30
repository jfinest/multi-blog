
$("body").on("click", "button.like_button", function(e){
	e.preventDefault();
	e.stopImmediatePropagation();
	var id = $(this).data("id");
	if (id){
		var url = "/blog/like/" + id;

		$.post(url,{"isLike": "1"}, function(data, status){
			
			var obj = data.replace(new RegExp("'", 'g'), '"');
			var objp = JSON.parse(obj);
			console.log(obj);
			console.log(objp.likes);
			$('#like-counter_' + id).html(objp.likes);
			$('#dislike-counter_' + id).html(objp.dislikes);
		});
	}
});

$("body").on("click", "button.dislike_button", function(e){
	e.preventDefault();
	e.stopImmediatePropagation();
	var id = $(this).data("id");
	if (id){
		var url = "/blog/like/" + id;

		$.post(url,{"isLike": "0"}, function(data, status){
			
			var obj = data.replace(new RegExp("'", 'g'), '"');
			var objp = JSON.parse(obj);
			console.log(obj);
			console.log(objp.dislikes);
			$('#like-counter_' + id).html(objp.likes);
			$('#dislike-counter_' + id).html(objp.dislikes);
		});
	}
});