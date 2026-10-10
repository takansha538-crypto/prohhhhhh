(function () {
  const form = document.getElementById("filterForm");
  if (!form) return;
  form.querySelectorAll("select").forEach((el) => {
    el.addEventListener("change", () => form.submit());
  });
  const drawerBtn = document.getElementById("openFilters");
  const filters = document.querySelector(".filters");
  if (drawerBtn && filters) {
    drawerBtn.addEventListener("click", () => {
      filters.classList.toggle("open");
      filters.style.display = filters.style.display === "none" ? "block" : filters.classList.contains("open") ? "block" : "";
      if (window.innerWidth < 980) {
        filters.style.display = filters.style.display === "block" ? "none" : "block";
      }
    });
  }
})();
