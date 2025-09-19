document.addEventListener("DOMContentLoaded", () => {
    const items = document.querySelectorAll("#file-list li, #file-list code");
    items.forEach(el => {
      el.style.color = randomColor();
    });
  
    function randomColor() {
      return `hsl(${Math.floor(Math.random() * 360)}, 100%, 40%)`;
    }
  });
  