$(document).ready(function() {
    $('.rdf_obj .show_more').click(function() {
	var link = $(this);
	table = $(this).siblings('.full_info');
	table.slideToggle(400, function() {
	    if (table.is(':visible')) {
		link.html('Show less');
	    } else {
		link.html('Show more');
	    }
	})

    });
    // Expand div when user goes to another RDF object
    $(window).bind('hashchange', function(e) {
	var hash = location.hash;
	var rdf_obj = $(hash);
	if (!rdf_obj.children('.full_info').is(':visible')) {
	    rdf_obj.children('.show_more').click();
	}
    });
});
