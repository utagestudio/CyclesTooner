// Before/after slider in the hero: the range input sets where the second image starts.
document.querySelectorAll(".ba").forEach(function (box) {
  var range = box.querySelector(".ba-range");
  if (!range) return;
  range.addEventListener("input", function () {
    box.style.setProperty("--pos", range.value + "%");
    box.classList.add("ba-touched");
  });
});
