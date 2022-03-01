// This is the scss entry file
import "../styles/index.scss";
// This code taken from https://stimulus.hotwired.dev/handbook/installing
import { Application } from "@hotwired/stimulus";
import { definitionsFromContext } from "@hotwired/stimulus-webpack-helpers";

const application = Application.start();
const context = require.context("./controllers", true, /\.js$/);
application.load(definitionsFromContext(context));


var btns = document.querySelectorAll(".btn");
for (var i = 0; i < btns.length; i++) {
    btns[i].addEventListener('click', function () {
        console.log("SHOULD CHANGE COLOR...");
        var currentBtn = document.querySelector(".current-tab");
        currentBtn.className = currentBtn.className.replace(" current-tab");
        this.className += " current-tab";
    });
}

