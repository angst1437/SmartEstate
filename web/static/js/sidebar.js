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

  // Функция для обновления позиции кнопки переключения
  function updateTogglePosition() {
    requestAnimationFrame(() => {
      const isOpen = sidebarElement.classList.contains("show");
      const isExpanded = sidebarElement.classList.contains("expanded");

      if (isOpen) {
        const sidebarRect = sidebarElement.getBoundingClientRect();
        const offset = 10; // выглядывает на 10px из правого края сайдбара

        // Учитываем расширенное состояние
        let rightEdge = sidebarRect.right;
        if (isExpanded) {
          // Если сайдбар расширен, используем его фактическую ширину
          rightEdge = sidebarRect.right;
        }

        sidebarToggle.style.left = `${rightEdge - offset}px`;
        sidebarToggle.innerHTML = '<i class="fa-solid fa-caret-left"></i>';
      } else {
        const offsetFromScreen = -10; // выглядывает из левого края экрана на 10px
        sidebarToggle.style.left = `${offsetFromScreen}px`;
        sidebarToggle.innerHTML = '<i class="fa-solid fa-caret-right"></i>';
      }
    });
  }

  // Показ/скрытие кнопки на время анимации (опционально)
  function temporarilyHideToggle() {
    sidebarToggle.style.opacity = "0";
  }

  function showToggle() {
    sidebarToggle.style.opacity = "1";
    updateTogglePosition();
  }

  // Функция для отслеживания изменений класса expanded
  function observeExpandedClass() {
    const observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        if (
          mutation.type === "attributes" &&
          mutation.attributeName === "class"
        ) {
          // Обновляем позицию при изменении класса expanded
          setTimeout(updateTogglePosition, 50); // небольшая задержка для CSS анимации
        }
      });
    });

    observer.observe(sidebarElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
  }

  // Инициализация
  updateTogglePosition();
  observeExpandedClass();

  // Обновление позиции только после завершения анимации
  sidebarElement.addEventListener("shown.bs.offcanvas", showToggle);
  sidebarElement.addEventListener("hidden.bs.offcanvas", showToggle);

  // Прячем кнопку на время анимации
  sidebarElement.addEventListener("show.bs.offcanvas", temporarilyHideToggle);
  sidebarElement.addEventListener("hide.bs.offcanvas", temporarilyHideToggle);

  // Обработчик клика по кнопке переключения
  sidebarToggle.addEventListener("click", function () {
    window.sidebarInstance.toggle();
  });

  // Обработчик клика по кнопке закрытия
  closeButton.addEventListener("click", function () {
    window.sidebarInstance.hide();
  });

  // Добавить в конец файла
  sidebarElement.addEventListener("hidden.bs.offcanvas", function () {
    sidebarElement.classList.remove("expanded");
  });
});
