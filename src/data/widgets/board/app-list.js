var apps = [];

function launchDesktopApp(entry) {
    var element = document.getElementById("app." + selected);
	document.body.style.top = "-100vh";
	backend.launchDesktopApp(entry);

	function await_app_exit() {
		backend.in_app(function(inapp){
		    if(!inapp) {
                document.body.style.top = "0";
            }
	        else {
	            const timeout = setTimeout(function() {
                    await_app_exit();
                }, 1000);
            }
		});
    }
    await_app_exit();
}

for(let elem of document.getElementsByClassName("app-list")) {
    try {
	    var settings = JSON.parse(elem.getAttribute("settings"));
    }
    catch (error) {
        alert("JSON.parse error while loading app-list widget.\n" + elem.getAttribute("settings") + "\n" + error);
    }

	elem.innerHTML = '<h1 class="applist-cat">' + settings.title + '</h1>';

	// Get desktop items
	try {
	    backend.getDesktopEntriesByCategory(settings.category, function(entries){
	        for(let entry of entries) {
	            if(!apps.includes(entry)) {
	                apps.push(entry);
	                backend.getDesktopIconPath(entry, function(icon) {
	                    if(entry.length > 10) {
	                        name = entry.split(" ")[0];
	                    }
	                    else {
	                        name = entry;
	                    }
	                    elem.innerHTML += "<div class='app-cont'><div onclick='launchDesktopApp(\"" + entry + "\")' class='applist-app'><img src='" + icon + "' /><p>" + name + "</p></div></div>";
	                });
	            }
	        }
	    });

	}
	catch (error) {
	    alert("Error while loading app-list widget.\n" + error)
	}
}

var style = document.createElement("style");
	style.innerHTML = `h1 {
	font-weight: bold;
	color: white;
	font-family: Roboto, Roboto, sans-serif;
}

.app-list:before,
.app-list:after {
  content: " "; /* 1 */
  display: table; /* 2 */
}

.app-list:after {
  clear: both;
}

.app-cont {
    height: 120px;
    float: left;
}

.applist-app {
	margin: 10px;
	margin-bottom: 50px;
	border-radius: 50%;
	box-shadow: 3px 4px 8px rgba(0,0,0, 0.8);
	overflow: hidden;
	background-color: rgba(255, 255, 255, 0.05);
	transition: all 0.2s ease;
	display: flex;
	justify-content: center;
	width: 60px;
}

.applist-app:hover img {
	width: 65px;
}

.applist-app:hover {
	margin: 7.5px;
	margin-bottom: 47.5px;
	width: 65px;
}

.applist-app img {
	width: 60px;
	transition: width 0.2s ease
}

.applist-app p {
	font-size: 90%;
	font-weight: bold;
	color: white;
	font-family: Roboto, Roboto, sans-serif;
	margin-top: 70px;
	position: absolute;
	transition: margin-top 0.2s ease;
}

.applist-app:hover p {
	margin-top: 72.5px;
}`;
document.body.appendChild(style);