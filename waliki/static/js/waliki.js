$(document).ready(function() {

    $('div.conflict').each(function(idx, elem){
        var $elem = $(elem);
        $elem.find(".flask-flash").hide();
        $elem.find(".footer").hide();
        $elem.find(".actions").hide();
        $elem.find("h1").addClass("conflictH1");
        $elem.parent("div.conflict-container").find("div.loading").hide();
        $elem.show();
    });

});
