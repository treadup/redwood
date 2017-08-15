// Toggle the navigation menu between displayed and hidden.
// This only has effect on the menu on the mobile version of
// the site.
function toggleNavMenu() {
    var menuEl = document.getElementById('navigation-menu');

    if(menuEl.className == "nav-menu") {
        menuEl.className = "nav-menu--collapsed";
    } else {
        menuEl.className = "nav-menu";
    }
}

document.addEventListener("DOMContentLoaded", function(event) {
    var menuButtonEl = document.querySelector('.hamburger-button');
    menuButtonEl.addEventListener("click", toggleNavMenu);
});
