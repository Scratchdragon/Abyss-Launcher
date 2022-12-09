function time() {
	var datetime = new Date();

	var h = datetime.getHours();
	var m = datetime.getMinutes();
	
	var type = (h < 12) ? 'AM':'PM';
	h = h % 12;
  	
	if(h == 0) {
		h = 12;
	}
	
  	if(m<10) {
        m = "0" + m;
    }
  	return h + ":" + m + " <span style='font-size: 2vh;color: lightgray;'>" + type + "</span>";
}

function update_time() {
    for(let item of document.getElementsByClassName("time")) {
        item.innerHTML = time();
    }
	
	const timeout = setTimeout(function() {
        update_time();
    }, 10000);
}

update_time();