// Start interface with python
var backend;
new QWebChannel(qt.webChannelTransport, function (channel) {
    backend = channel.objects.backend;
    function await_app_exit() {
		backend.icons_ready(function(icons_ready){
		    if(icons_ready) {
                document.body.style.top = "0";
                loadElements();
            }
	        else {
	            const timeout = setTimeout(function() {
                    await_app_exit();
                }, 1000);
            }
		});
    }
    await_app_exit();
});

// Functions for fake popups:
function open_popup(obj) {
	obj.style.visibility = "visible";
	obj.style.transition = "opacity 0.3s";
	obj.style.opacity = "1";
}
function close_popup(obj) {
	obj.style.transition = "opacity 0.3s";
	obj.style.opacity = "0";
	var listener = function() {
		obj.style.visibility = "hidden";
		obj.removeEventListener(transition(), listener);
	}
	obj.addEventListener(transition(), listener, false);
}

function transition(){
    var t;
    var el = document.createElement('fakeelement');
    var transitions = {
      'transition':'transitionend',
      'OTransition':'oTransitionEnd',
      'MozTransition':'transitionend',
      'WebkitTransition':'webkitTransitionEnd'
    }

    for(t in transitions){
        if( el.style[t] !== undefined ){
            return transitions[t];
        }
    }
}

var getJSON = function(url, callback) {
    backend.getFile(url, function(data) {
        if(data=="") {
            callback(1, "No file");
        }
        else {
            callback(null, JSON.parse(data));
        }
    });
};

// Panel methods
function loadPanel(widgets) {
	var i = 0;

	var load = function(err, data) {}

	load = function(err, data) {
		var src = widgets[i]; 
  		if (err !== null) {
    		alert('Widget "' + src + '" failed to load: ' + err);
  		} else {
  			var panel = document.getElementById("top-panel");

			var widget = document.createElement("div");

			if(data.name == null) {
				alert('Widget "' + src + '" failed to load: No name was declared');
				return;
			}
			widget.classList.add("widget", data.name);

			// Widget content is option as it may be added later by the widget script
			if(data.content != null) {
				widget.innerHTML = data.content;
			}

			// Add the script to the widget
			if(data.script != null) {
				var script = document.createElement("script");
				script.src = (src.substring(0, src.lastIndexOf("/")+1) + data.script);
				widget.appendChild(script);
			}

			// Add the style to the widget
			if(data.style != null) {
				var style = document.createElement("link");
				style.href = (src.substring(0, src.lastIndexOf("/")+1) + data.style);
				style.rel = "stylesheet";
				style.type="text/css";
				widget.appendChild(script);
			}

			panel.appendChild(widget);

			if(widgets[i+1]!=null) {
				// Get the next widget
				i++;
				getJSON(
					widgets[i],
					load
				);
			}
			
		}
	}
	
	getJSON(
		widgets[i],
		load
	);
}

// Dashboard methods
function loadApplets(widgets) {
	if(widgets[0]==null) {
		return;
	}
	var i = 0;

	var load = function(err, data) {}

	load = function(err, data) {
		var src = widgets[i].name;
  		if (err !== null) {
    		alert('Widget "' + src + '" failed to load: ' + err);
  		} else {
  			var board = document.getElementById("board");

			var widget = document.createElement("div");

			if(data.name == null) {
				alert('Widget "' + src + '" failed to load: No name was declared');
				return;
			}

			widget.classList.add("widget", data.name);

			// Widget customization options
			if(widgets[i].settings != null) {
			    let attribute = "{\n";
				let index = 0;
                for(let setting of Object.keys(widgets[i].settings)) {
					++index;
                    if(setting == null) {
                        alert('Widget "' + src + '" failed to load: Settings item #' + index + ' has no name (setting.key = null)');
                        return;
                    }
                    if(Object.values(widgets[i].settings)[index-1] == null) {
                        alert('Widget "' + src + '" failed to load: Settings item #' + index + ' has no default value (setting.value = null)');
                        return;
                    }

                    let def = Object.values(widgets[i].settings)[index-1];
                    if(typeof def === "string") {
                        def = '"' + def + '"';
                    }
                    attribute += '  "' + setting + '":' + def;
					if(index<Object.keys(widgets[i].settings).length) {
						attribute += ",";
					}
					// Newlines just make the attribute more human readable
					attribute += "\n";
                }
                attribute += "}";
                widget.setAttribute("settings", attribute);
			}

			// Widget content is option as it may be added later by the widget script
			if(data.content != null) {
				widget.innerHTML = data.content;
			}
			if(data.html != null) {
				widget.innerHTML = "<iframe src='" + data.html + "' title='" + widget.id + "'></iframe>";
			}

			// Add the script to the widget
			if(data.script != null) {
				var script = document.createElement("script");
				script.src = (src.substring(0, src.lastIndexOf("/")+1) + data.script);
				widget.appendChild(script);
			}

			// Add the style to the widget
			if(data.style != null) {
				var style = document.createElement("link");
				style.href = (src.substring(0, src.lastIndexOf("/")+1) + data.style);
				style.rel = "stylesheet";
				style.type="text/css";
				widget.appendChild(script);
			}

			board.appendChild(widget);

			if(widgets[i+1]!=null) {
				// Get the next widget
				i++;
				getJSON(
					widgets[i].name,
					load
				);
			}

		}
	}

	getJSON(
		widgets[i].name,
		load
	);
}

// Apps section variables
var max = 0;
var last_selected = 0;
var selected = 1;

// App information
var appdata;
var appnames;

function loadElements() {
// Load the panel
getJSON("./data/panel.json",
function(err, data) {
  	if (err !== null) {
    	alert('Error loading panel json file: ' + err);
  	} else {
		loadPanel(data);
	}
});

// Load the dashboard
getJSON("./data/board.json",
function(err, data) {
  	if (err !== null) {
    	alert('Error loading panel json file: ' + err);
  	} else {
		loadApplets(data);
	}
});

// Load apps
getJSON("./data/appdata.json",
function(err, data) {
  if (err !== null) {
    alert('Something went wrong: ' + err);
  }
  else {
        // Save app data for later
		appnames = Object.keys(data);
		appdata = Object.values(data);
		max = appnames.length;
	  
		// Set up elements
		var apps = document.getElementById("app-scroll");

		for (var i = 0; i<max;++i) {
			var element = document.createElement("div");
			element.className = "app";
			element.addEventListener('click', function handleClick(event) {
  				select(this.id.split(".")[1]);
			});

	
			var img = document.createElement("img");
			img.src = appdata[i].image;

			var details = document.createElement("div");
			details.className = "details";

			var icon = '▶';
			
			details.innerHTML = "<h1>" + appnames[i] + "</h1>"
			details.innerHTML += "<p><span style='color: rgb(57, 200, 244); margin-top: 0;'>" + icon + "</span>&nbsp&nbsp&nbsp" + appdata[i].description.toUpperCase() + "</p>";
	
			element.appendChild(img);
			element.appendChild(details);
	
			apps.appendChild(element);
			element.style.left = (30*i) + "vh";
			element.id = "app." + i;
		}

		++max;
	  
		var element = document.createElement("div");
		element.className = "app";
		element.addEventListener('click', function handleClick(event) {
  			select(this.id.split(".")[1]);
		});

		element.innerHTML = "<img src='images/add.png'><div class='details'><h1>Add a game</h1></div>";
	  
		apps.appendChild(element);
		element.style.left = (30*(max-1)) + "vh";
		element.id = "app." + (max - 1);

		update_selected();
  }
});
}

function open_app() {
	if(selected==max-1) {
		open_popup(document.getElementById("add-menu"));
	}
	else {
		var element = document.getElementById("app." + selected);
		document.body.style.top = "-100vh";
		backend.launch(appnames[selected], appdata[selected].launch);

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
}

function select(i) {
	if(selected == i) {
		open_app();
		return;
	}
	
	last_selected = selected;
	selected = i;
	update_selected();
}

function update_selected() {
	var element = document.getElementById("app." + selected);
	element.style.outlineColor = "white";
	element.style.outlineOffset = "2px";

	for (let detail of element.getElementsByClassName("details")) {
		detail.style.opacity = 1;
	}
	
	var element = document.getElementById("app." + last_selected);
	element.style.outlineColor = "transparent";
	element.style.outlineOffset = "10px";

	for (let detail of element.getElementsByClassName("details")) {
		detail.style.opacity = 0;
	}
	
	document.getElementById("app-scroll").style.left = 
		"calc(" + (-selected*30)+ "vh + 50vw - 18.35vh)";
}

document.onkeyup = handle_input;
function handle_input(e) {
    e = e || window.event;
	last_selected = selected;
    if (e.keyCode == '37' && selected > 0) {
       --selected;
		update_selected();
    }
    else if (e.keyCode == '39' && selected+1 < max) {
       ++selected;
		update_selected();
    }
	// Check for confirm key(s) pressed ([space] or [enter])
	else if (e.keyCode == '13' || e.keyCode == '32') {
		open_app();
	}
}

var loadFile = function(event, id) {
	var image = document.getElementById(id);
	image.src = URL.createObjectURL(event.target.files[0]);
}

function create_app(image, description, launch) {
	var app = Object();
	app.image = image;
	app.description = description;
	app.launch = launch;
	return app;
}