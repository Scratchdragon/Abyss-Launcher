for(let elem of document.getElementsByClassName("shutdown_button")) {
    let img = elem.querySelector('.act_icon');
    img.style.height = "3vh";
    img.src = "images/shutdown.png";
    elem.onclick = function() {
        backend.shutdown();
    }
}