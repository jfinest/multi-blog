$("body").on("click",".like_button", function(e){
    e.preventDefault();
    var id = $(this).data("id");
    if(id){
        var url = "/blog/like/" + id;

        $.post(url, {}, function(data, status){
            console.log("Data: " + JSON.stringify(data) + "\nStatus: " + status);

            alert("Data :" + JSON.stringify(data) + "\nStatus: " + status);

        });
    }
});