function notifyGhost(eventName) {
  window.parent.postMessage({
    source: "plotly-visualization",
    event: eventName
  }, "*");
}

// assets/plot_loaded_tracker.js

document.addEventListener("DOMContentLoaded", function () {
  setTimeout(function () {
    const buttons = Array.from(document.querySelectorAll("button")).filter(btn => btn.innerText === "Download CSV");
    buttons.forEach(btn => {
      btn.addEventListener("click", function () {
        if (typeof notifyGhost === "function") {
            console.log('download triggered')
            notifyGhost("csv-download");
            console.log('download sent')
          
        }
      });
    });
  }, 1000);
});