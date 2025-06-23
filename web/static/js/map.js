function formatNumber(number) {
  return number.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

function unpackObj(obj) {
  const array = Object.values(obj);

  const dict = new Map();
  for (let i = 0; i < array.length; i += 2) {
    dict.set(array[i], array[i + 1]);
  }
  return dict;
}

function formatJSON(jsonData, isNested = false) {
  if (typeof jsonData !== "object" || jsonData === null) {
    return jsonData !== undefined && jsonData !== null ? jsonData : "—";
  }

  const containerClass = isNested ? "summary-nested" : "summary-container";

  return `
    <div class="${containerClass}">
      <dl class="summary-dl">
        ${Object.entries(jsonData)
          .map(
            ([key, value]) => `
            <div class="summary-item">
              <dt class="summary-key"><b>${key}:</b></dt>
              <dd class="summary-value">${formatJSON(value, true)}</dd>
            </div>
          `,
          )
          .join("")}
      </dl>
    </div>
  `;
}

window.addEventListener("load", function () {
  const map = L.map("map").setView([55.1465, 61.3406], 12);

  const mapElement = document.getElementById("map");

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
  }).addTo(map);

  let markers = [];

  function loadClusters() {
    const bounds = map.getBounds();
    const zoom = map.getZoom();

    const filters = {
      min_price: document.getElementById("filter_min_price").value,
      max_price: document.getElementById("filter_max_price").value,
      min_area: document.getElementById("filter_min_area").value,
      max_area: document.getElementById("filter_max_area").value,
      rooms: document.getElementById("filter_rooms").value,
      renovation_type: document.getElementById("filter_renovation").value,
      floor: document.getElementById("filter_floor").value,
      min_year: document.getElementById("filter_min_year").value,
      min_kitchen_area: document.getElementById("filter_min_kitchen_area")
        .value,
      min_bathrooms_num: document.getElementById("filter_min_bathrooms_num")
        .value,
      bathroom_type: document.getElementById("filter_bathroom_type").value,
      balcony_type: document.getElementById("filter_balcony_type").value,
      sell_type: document.getElementById("sell_type").value,
    };

    Object.keys(filters).forEach((key) => {
      if (!filters[key]) {
        delete filters[key];
      }
    });

    const queryParams = new URLSearchParams({
      zoom,
      ne_lat: bounds.getNorthEast().lat,
      ne_lng: bounds.getNorthEast().lng,
      sw_lat: bounds.getSouthWest().lat,
      sw_lng: bounds.getSouthWest().lng,
      ...filters,
    });

    const url = `/api/clusters?${queryParams.toString()}`;

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        markers.forEach((m) => map.removeLayer(m));
        markers = [];

        data.forEach((cluster) => {
          const size = 10 + Math.min(cluster.count, 13);

          const marker = L.marker([cluster.lat, cluster.lon], {
            icon: L.divIcon({
              html: `<div style="
                width:${size}px;
                height:${size}px;
                background: blue;
                border-radius: 50%;
                opacity: 1;
                border: 1px solid white;
              "></div>`,
              className: "",
              iconSize: [size, size],
            }),
          }).addTo(map);

          let popupHtml = "";

          if (cluster.count === 1) {
            const prop = cluster.properties[0];
            const formatted_price = formatNumber(String(prop.price));
            popupHtml = `    
              <b>${prop.title}</b><br>
              <b>Цена:</b> ${formatted_price} ₽<br>
              <b>Адрес:</b> ${prop.address || "не указан"}<br>
            `;

            if (prop.photos && Array.isArray(prop.photos)) {
              popupHtml += `
                <div style="margin-top: 10px;"><b>Фотографии:</b></div>
                <div style="display: flex; flex-wrap: wrap; gap: 5px; margin-top: 5px;">
              `;
              for (const photo of prop.photos.slice(0, 3)) {
                popupHtml += `<img src="${photo}" style="width: 90px; height: 90px; object-fit: cover; border: 1px solid #ddd;">`;
              }
              popupHtml += `</div>`;
            }
          } else {
            popupHtml =
              `<b>${cluster.count} объектов:</b><br>` +
              cluster.properties
                .map((p) => {
                  const title = p.title || "Без названия";
                  const price = p.price
                    ? `${formatNumber(String(p.price))} ₽`
                    : "Цена не указана";
                  return `• ${title} — ${price}`;
                })
                .join("<br>");
          }

          marker.bindPopup(popupHtml, { autoPan: false });

          marker.on("mouseover", function (e) {
            this.openPopup();
          });

          marker.on("mouseout", function (e) {
            this.closePopup();
          });

          marker.on("click", function () {
            const sidebarElement = document.getElementById("sidebar");
            sidebarElement.classList.remove("expanded");
            const sidebar =
              bootstrap.Offcanvas.getInstance(sidebarElement) ||
              new bootstrap.Offcanvas(sidebarElement);

            window.sidebarInstance.show();

            if (cluster.count === 1) {
              updateSidebarContent(cluster.properties[0]);
            } else {
              updateSidebarForCluster(cluster);
            }
          });

          markers.push(marker);
        });
      });
  }

  function updateSidebarContent(property) {
    const sidebarElement = document.getElementById("sidebar");
    const sidebarBody = document.querySelector(".offcanvas-body");
    if (!sidebarBody) return;

    sidebarElement.classList.remove("expanded");

    let content = `
      <h3>${property.title}</h3>
      <h4><strong>Цена:</strong> ${formatNumber(String(property.price))} ₽</h4>
      <p><strong>Адрес:</strong> ${property.address || "не указан"}</p>
      <p><strong>Описание:</strong> ${property.description || "нету"}</p>
      <p><strong>Характеристики:</strong> ${formatJSON(property.summary)}</p><br>
      <a href="${property.link}" target="_blank" class="btn btn-primary mt-2">Перейти к объявлению</a>
    `;

    if (
      property.photos &&
      Array.isArray(property.photos) &&
      property.photos.length > 0
    ) {
      const carouselId = `carousel-${property.id || Math.random().toString(36).substring(7)}`;
      content += `
    <div class="mt-3">
      <strong>Фотографии:</strong>
      <div id="${carouselId}" class="carousel slide mt-2" data-bs-ride="carousel">
        <div class="carousel-inner">
  `;

      property.photos.forEach((photo, index) => {
        content += `
      <div class="carousel-item${index === 0 ? " active" : ""}">
        <img src="${photo}" class="d-block w-100" style="object-fit: cover; max-height: 300px;" alt="Фото ${index + 1}">
      </div>
    `;
      });

      content += `
        </div>
        <button class="carousel-control-prev" type="button" data-bs-target="#${carouselId}" data-bs-slide="prev">
          <span class="carousel-control-prev-icon" aria-hidden="true"></span>
          <span class="visually-hidden">Предыдущее</span>
        </button>
        <button class="carousel-control-next" type="button" data-bs-target="#${carouselId}" data-bs-slide="next">
          <span class="carousel-control-next-icon" aria-hidden="true"></span>
          <span class="visually-hidden">Следующее</span>
        </button>
      </div>
    </div>
  `;
    }

    sidebarBody.innerHTML = content;
  }

  function updateSidebarForCluster(cluster) {
    const sidebarElement = document.getElementById("sidebar");
    const sidebarBody = document.querySelector(".offcanvas-body");
    if (!sidebarBody) return;

    sidebarElement.classList.add("expanded");

    let content = `<h4>${cluster.count} объектов в этом районе</h4>
                <div class="cluster-grid">`;

    cluster.properties.forEach((prop, index) => {
      const title = prop.title || "Без названия";
      const price = prop.price
        ? `${formatNumber(String(prop.price))} ₽`
        : "Цена не указана";

      let cardContent = `<div class="cluster-card">`;

      if (prop.photos && Array.isArray(prop.photos) && prop.photos.length > 0) {
        const carouselId = `carousel-cluster-${prop.id || Math.random().toString(36).substring(7)}`;
        cardContent += `
        <div class="mb-3">
          <div id="${carouselId}" class="carousel slide" data-bs-ride="carousel">
            <div class="carousel-inner">
        `;

        prop.photos.forEach((photo, photoIndex) => {
          cardContent += `
            <div class="carousel-item${photoIndex === 0 ? " active" : ""}">
              <img src="${photo}" class="d-block w-100" style="object-fit: cover; height: 180px; border-radius: 5px;" alt="Фото ${photoIndex + 1}">
            </div>
          `;
        });

        cardContent += `
            </div>
            <button class="carousel-control-prev" type="button" data-bs-target="#${carouselId}" data-bs-slide="prev">
              <span class="carousel-control-prev-icon" aria-hidden="true"></span>
              <span class="visually-hidden">Предыдущее</span>
            </button>
            <button class="carousel-control-next" type="button" data-bs-target="#${carouselId}" data-bs-slide="next">
              <span class="carousel-control-next-icon" aria-hidden="true"></span>
              <span class="visually-hidden">Следующее</span>
            </button>
          </div>
        </div>
        `;
      }

      cardContent += `
        <h5>${title}</h5>
        <h6><strong>Цена:</strong> ${price}</h6>
        <p><strong>Адрес:</strong> ${prop.address || "не указан"}</p>
        <p><strong>Характеристики:</strong> ${formatJSON(prop.factoids)}</p>
      `;

      cardContent += `
        <div class="mt-3 d-flex gap-2">
          <button class="btn btn-sm btn-outline-primary" onclick="showPropertyDetails(${index}, ${JSON.stringify(cluster).replace(/"/g, "&quot;")})">
            Подробнее
          </button>
          <a href="${prop.link}" target="_blank" class="btn btn-sm btn-primary">
            Перейти к объявлению
          </a>
        </div>
      </div>
      `;

      content += cardContent;
    });

    content += `</div>`;
    sidebarBody.innerHTML = content;
  }

  // Функция для показа детальной информации об объявлении
  window.showPropertyDetails = function (propertyIndex, cluster) {
    const property = cluster.properties[propertyIndex];
    const sidebarElement = document.getElementById("sidebar");
    const sidebarBody = document.querySelector(".offcanvas-body");
    if (!sidebarBody) return;

    sidebarElement.classList.remove("expanded");

    let content = `
      <div class="mb-3">
        <button class="btn btn-sm btn-outline-secondary" onclick="updateSidebarForCluster(${JSON.stringify(cluster).replace(/"/g, "&quot;")})">
          ← Назад
        </button>
      </div>
      <h3>${property.title}</h3>
      <h4><strong>Цена:</strong> ${formatNumber(String(property.price))} ₽</h4>
      <p><strong>Адрес:</strong> ${property.address || "не указан"}</p>
      <p><strong>Описание:</strong> ${property.description || "нету"}</p>
      <p><strong>Характеристики:</strong> ${formatJSON(property.summary)}</p><br>
      <a href="${property.link}" target="_blank" class="btn btn-primary mt-2">Перейти к объявлению</a>
    `;

    if (
      property.photos &&
      Array.isArray(property.photos) &&
      property.photos.length > 0
    ) {
      const carouselId = `carousel-detail-${property.id || Math.random().toString(36).substring(7)}`;
      content += `
    <div class="mt-3">
      <strong>Фотографии:</strong>
      <div id="${carouselId}" class="carousel slide mt-2" data-bs-ride="carousel">
        <div class="carousel-inner">
  `;

      property.photos.forEach((photo, index) => {
        content += `
      <div class="carousel-item${index === 0 ? " active" : ""}">
        <img src="${photo}" class="d-block w-100" style="object-fit: cover; max-height: 300px;" alt="Фото ${index + 1}">
      </div>
    `;
      });

      content += `
        </div>
        <button class="carousel-control-prev" type="button" data-bs-target="#${carouselId}" data-bs-slide="prev">
          <span class="carousel-control-prev-icon" aria-hidden="true"></span>
          <span class="visually-hidden">Предыдущее</span>
        </button>
        <button class="carousel-control-next" type="button" data-bs-target="#${carouselId}" data-bs-slide="next">
          <span class="carousel-control-next-icon" aria-hidden="true"></span>
          <span class="visually-hidden">Следующее</span>
        </button>
      </div>
    </div>
  `;
    }

    sidebarBody.innerHTML = content;
  };

  window.updateSidebarForCluster = updateSidebarForCluster;

  map.on("moveend", loadClusters);

  const filterPanel = document.getElementById("filter-panel");
  const toggleBtn = document.getElementById("filter-toggle");

  toggleBtn.addEventListener("click", () => {
    const isVisible = filterPanel.style.display === "block";

    if (isVisible) {
      filterPanel.classList.remove("show");
      toggleBtn.classList.remove("active");
      setTimeout(() => (filterPanel.style.display = "none"), 300);
    } else {
      filterPanel.style.display = "block";
      setTimeout(() => {
        filterPanel.classList.add("show");
        toggleBtn.classList.add("active");
      }, 10);
    }
  });

  document
    .getElementById("filters-form")
    .addEventListener("submit", function (e) {
      e.preventDefault();
      loadClusters();

      if (filterPanel.classList.contains("show")) {
        filterPanel.classList.remove("show");
        filterPanel.addEventListener(
          "transitionend",
          () => {
            filterPanel.style.display = "none";
          },
          { once: true },
        );
      }
    });

  document.getElementById("filter-reset").addEventListener("click", () => {
    document.getElementById("filters-form").reset();
    loadClusters();
  });

  loadClusters();
});
