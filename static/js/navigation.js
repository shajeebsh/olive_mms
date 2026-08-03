// Olive MMS navigation helpers.
(function () {
  "use strict";

  // Keep the module ribbon in sync with Bootstrap's collapse on md+ screens.
  var moduleNav = document.getElementById("moduleNav");
  if (moduleNav && window.matchMedia("(min-width: 992px)").matches) {
    moduleNav.classList.add("show");
  }

  // Close the mobile ribbon after a link is tapped.
  document.querySelectorAll("#moduleNav .nav-link").forEach(function (link) {
    link.addEventListener("click", function () {
      if (window.matchMedia("(max-width: 991.98px)").matches && moduleNav) {
        var collapse = bootstrap.Collapse.getOrCreateInstance(moduleNav, { toggle: false });
        collapse.hide();
      }
    });
  });

  // Close the generic modal when an htmx form response triggers "closeModal".
  document.body.addEventListener("closeModal", function () {
    var el = document.getElementById("genericModal");
    if (el) {
      var modal = bootstrap.Modal.getOrCreateInstance(el);
      modal.hide();
    }
  });
})();
