
$("body").on("click", "button.like_button", function(e){
	e.preventDefault();
	e.stopImmediatePropagation();
	var id = $(this).data("id");
	if (id){
		var url = "/blog/like/" + id;

		$.post(url,{"isLike": "1"}, function(data, status){
			//console.log(data.replace(new RegExp("'", 'g'), '"'));
			var obj = data.replace(new RegExp("'", 'g'), '"');
			var objp = JSON.parse(obj);
			console.log(obj);
			console.log(objp.likes);
			$('#like-counter_' + id).html(objp.likes);
			$('#dislike-counter_' + id).html(objp.dislikes);
			//var obj = JSON.parse(data.replace(new RegExp("'", 'g'), '"'));
			//console.log( JSON.stringify(data) + "\nStatus: " + status);
			//console.log(obj.likes);

			//alert("Data: " + JSON.stringify(data) + "\nStatus: " + status);

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
			//console.log(data.replace(new RegExp("'", 'g'), '"'));
			var obj = data.replace(new RegExp("'", 'g'), '"');
			var objp = JSON.parse(obj);
			console.log(obj);
			console.log(objp.dislikes);
			$('#like-counter_' + id).html(objp.likes);
			$('#dislike-counter_' + id).html(objp.dislikes);
			//var obj = JSON.parse(data.replace(new RegExp("'", 'g'), '"'));
			//console.log(JSON.stringify(data) + "\nStatus: " + status);
			//console.log(obj.dislikes);
			//alert("Data: " + JSON.stringify(data) + "\nStatus: " + status);

		});
	}
});