document.addEventListener("DOMContentLoaded", function () {
  const sidebarElement = document.getElementById("sidebar");
  window.sidebarInstance =
    bootstrap.Offcanvas.getInstance(sidebarElement) ||
    new bootstrap.Offcanvas(sidebarElement, {
      backdrop: false,
      keyboard: false,
      scroll: true,
    });

  const sidebarToggle = document.getElementById("sidebar-toggle");
  const closeButton = document.getElementById("close-sidebar");

  function updateTogglePosition() {
    requestAnimationFrame(() => {
      const isOpen = sidebarElement.classList.contains("show");
      const isExpanded = sidebarElement.classList.contains("expanded");

      if (isOpen) {
        const sidebarRect = sidebarElement.getBoundingClientRect();
        const offset = 10;

        let rightEdge = sidebarRect.right;
        if (isExpanded) {
          rightEdge = sidebarRect.right;
        }

        sidebarToggle.style.left = `${rightEdge - offset}px`;
        sidebarToggle.innerHTML = '<i class="fa-solid fa-caret-left"></i>';
      } else {
        const offsetFromScreen = -10;
        sidebarToggle.style.left = `${offsetFromScreen}px`;
        sidebarToggle.innerHTML = '<i class="fa-solid fa-caret-right"></i>';
      }
    });
  }

  function temporarilyHideToggle() {
    sidebarToggle.style.opacity = "0";
  }

  function showToggle() {
    sidebarToggle.style.opacity = "1";
    updateTogglePosition();
  }

  function observeExpandedClass() {
    const observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        if (
          mutation.type === "attributes" &&
          mutation.attributeName === "class"
        ) {
          setTimeout(updateTogglePosition, 50);
        }
      });
    });

    observer.observe(sidebarElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
  }

  updateTogglePosition();
  observeExpandedClass();

  sidebarElement.addEventListener("shown.bs.offcanvas", showToggle);
  sidebarElement.addEventListener("hidden.bs.offcanvas", showToggle);

  sidebarElement.addEventListener("show.bs.offcanvas", temporarilyHideToggle);
  sidebarElement.addEventListener("hide.bs.offcanvas", temporarilyHideToggle);

  sidebarToggle.addEventListener("click", function () {
    window.sidebarInstance.toggle();
  });

  closeButton.addEventListener("click", function () {
    window.sidebarInstance.hide();
  });

  sidebarElement.addEventListener("hidden.bs.offcanvas", function () {
    sidebarElement.classList.remove("expanded");
  });
});
