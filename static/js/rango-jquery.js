$(document).ready(function(){
    //JQuery code to be added in here
    $("#about-btn").click(function(event) {
        mgstr = $('#msg').html()
        msgstr = mgstr + "O"
        $("#msg").html(msgstr)
    });
    $("p").hover( function() {
            $("p").css('color', 'red');
    },
    function() {
            $("p").css('color', 'blue');
    });
});