for(let elem of document.getElementsByClassName("restart_button")) {
    let img = elem.querySelector('.act_icon');
    img.style.height = "3vh";
    img.src = "images/restart.png";
    elem.onclick = function() {
        backend.restart();
    }
}