document.addEventListener("DOMContentLoaded", function () {
  const sidebarElement = document.getElementById("sidebar");
  const sidebar =
    bootstrap.Offcanvas.getInstance(sidebarElement) ||
    new bootstrap.Offcanvas(sidebarElement);

  const sidebarToggle = document.getElementById("sidebar-toggle");
  const closeButton = document.getElementById("close-sidebar");

  // Функция для обновления позиции кнопки переключения
  function updateTogglePosition() {
    if (sidebarElement.classList.contains("show")) {
      const sidebarWidth = sidebarElement.offsetWidth;
      sidebarToggle.style.left = `${sidebarWidth + 50}px`;
      sidebarToggle.innerHTML = '<i class="fa-solid fa-caret-left"></i>';
    } else {
      sidebarToggle.style.left = "15px";
      sidebarToggle.innerHTML = '<i class="fa-solid fa-caret-right"></i>';
    }
  }

  // Обработчик открытия сайдбара
  sidebarElement.addEventListener("show.bs.offcanvas", function () {
    updateTogglePosition();

    // Закрываем все открытые popup при открытии sidebar
    document.querySelectorAll(".leaflet-popup").forEach((popup) => {
      popup.style.display = "none";
    });
  });

  // Обработчик закрытия сайдбара
  sidebarElement.addEventListener("hide.bs.offcanvas", function () {
    updateTogglePosition();
  });

  // Обработчик изменения размера (для адаптации под расширенный режим)
  new ResizeObserver(updateTogglePosition).observe(sidebarElement);

  // Обработчик клика по основной кнопке
  sidebarToggle.addEventListener("click", function () {
    sidebar.toggle();
  });

  // Обработчик клика по кнопке закрытия
  closeButton.addEventListener("click", function () {
    sidebar.hide();
  });
});
