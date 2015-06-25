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
});
