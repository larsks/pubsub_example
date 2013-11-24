/* We need to use port 8000 when deployed on OpenShift to avoid
 * problems with their front-end proxy architecture.  You'll need
 * to set using_openshift somewhere before loading this script.
 */
if (using_openshift) {
	poll_url = location.protocol + "//" + location.hostname + ":8000/sub";
} else {
	poll_url = "/sub";
}

/* This is our long poll function.  It makes an ajax request
 * to /sub on our server, and then hangs around waiting for data.
 *
 * If we receive data from the server, we restart the poll immediately.  If
 * there's an error, we wait for one second before polling again (so avoid
 * runaway polling if the server is unavailable/broken/etc.
 */
function poll() {
	$.ajax({
		url: poll_url,
		type: 'GET',
		dataType: 'json',
		success: function(data) {
			$("#conversation").append("<p><span class='nick'>"
						  + (data['nick'] ? data['nick'] : "&lt;unknown&gt;")
						  + "</span>: " + data['message'] + "</p>");
						  $("#conversation").each(function () {
							  this.scrollTop = this.scrollHeight;
						  });
						  setTimeout(poll, 0);
		},
		error: function () {
			setTimeout(poll, 1000);
		},
	});
}

/* Called when the user clisk the "Send" button (or, in most browsers, if they
 * press return while in the message field).
 */
function send_message() {
	$.ajax({
		url: '/pub',
		type: 'POST',
		dataType: 'json',
		data: {
			nick: $("#nick").val(),
			message: $("#message").val(),
		},
		complete: function () {
			$("#message").val("");
		},
	});
}

/* This is the document.ready() function, called once the DOM for 
 * the document is ready.
 */
$(function() {
	$("#send").click(send_message);
	$("#chatform").submit(function (event) {
		send_message();
		event.preventDefault();
	});

	setTimeout(poll, 0);
})

