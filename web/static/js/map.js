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

function formatSummary(mapData) {
  if (!(mapData instanceof Map)) {
    return "<p>Ошибка данных</p>";
  }

  return `
    <div class="summary-container">
      ${Array.from(mapData.entries())
        .map(
          ([key, value]) => `
          <div class="summary-item">
            <span class="summary-key"><b>${key}:</b></span>
            <span class="summary-value">${value || "—"}</span>
          </div>
        `,
        )
        .join("")}
    </div>
  `;
}

window.addEventListener("load", function () {
  const map = L.map("map").setView([55.1465, 61.3406], 12);

  const mapElement = document.getElementById("map");

  const resizeObserver = new ResizeObserver(() => {
    map.invalidateSize();
  });

  resizeObserver.observe(mapElement);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
  }).addTo(map);

  let markers = [];

  function loadClusters() {
    const bounds = map.getBounds();
    const zoom = map.getZoom();

    const url = `/api/clusters?zoom=${zoom}&ne_lat=${bounds.getNorthEast().lat}&ne_lng=${bounds.getNorthEast().lng}&sw_lat=${bounds.getSouthWest().lat}&sw_lng=${bounds.getSouthWest().lng}`;

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
              <a href="${prop.link}" target="_blank">Перейти к объявлению</a>
            `;

            if (prop.about_data && typeof prop.about_data === "object") {
              popupHtml += `<b>Характеристики:</b><br>`;
              for (const [key, value] of Object.entries(prop.about_data)) {
                popupHtml += `• ${key}: ${value}<br>`;
              }
            }

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

          // Обработчики событий
          marker.on("mouseover", function (e) {
            this.openPopup();
          });

          marker.on("mouseout", function (e) {
            this.closePopup();
          });

          marker.on("click", function () {
            const sidebarElement = document.getElementById("sidebar");
            const sidebar =
              bootstrap.Offcanvas.getInstance(sidebarElement) ||
              new bootstrap.Offcanvas(sidebarElement);

            sidebar.show();

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
    const sidebarBody = document.querySelector(".offcanvas-body");
    if (!sidebarBody) return;

    console.log(property.summary[0] + property.summary[1]);
    const unpackedSum = unpackObj(property.summary);

    let content = `
      <h3>${property.title}</h3>
      <h4><strong>Цена:</strong> ${formatNumber(String(property.price))} ₽</h4>
      <p><strong>Адрес:</strong> ${property.address || "не указан"}</p>
      <p><strong>Описание:</strong> ${property.description || "нету"}</p>
      <p><strong>Характеристики:</strong> ${formatSummary(unpackedSum)}</p><br>
      <p>${property.factoids}</p>
      <a href="${property.link}" target="_blank" class="btn btn-primary mt-2">Перейти к объявлению</a>
    `;

    if (property.about_data && typeof property.about_data === "object") {
      content += `<div class="mt-3"><strong>Характеристики:</strong><ul>`;
      for (const [key, value] of Object.entries(property.about_data)) {
        content += `<li><strong>${key}:</strong> ${value}</li>`;
      }
      content += `</ul></div>`;
    }

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
    const sidebarBody = document.querySelector(".offcanvas-body");
    if (!sidebarBody) return;

    let content = `<h4>${cluster.count} объектов в этом районе</h4>`;

    cluster.properties.forEach((prop) => {
      const title = prop.title || "Без названия";
      const price = prop.price
        ? `${formatNumber(String(prop.price))} ₽`
        : "Цена не указана";

      content += `
        <div class="card mb-2">
          <div class="card-body">
            <h5 class="card-title">${title}</h5>
            <p class="card-text">${price}</p>
            <p class="card-text"><small>Адрес: ${prop.address || "не указан"}</small></p>
            <a href="${prop.link}" target="_blank" class="btn btn-sm btn-primary">Подробнее</a>
          </div>
        </div>
      `;
    });

    sidebarBody.innerHTML = content;
  }

  map.on("moveend", loadClusters);
  loadClusters();

  map.on("moveend", () => {
    const rect = document.getElementById("map").getBoundingClientRect();
    console.trace("Сработал moveend");
    console.log(
      `Камера перемещена. Центр: lat: ${map.getCenter().lat}, lng: ${map.getCenter().lng}, Зум: ${map.getZoom()}`,
    );
    console.log("Размер карты (px):", rect.width, rect.height);
  });
});
