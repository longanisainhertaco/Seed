document.addEventListener("DOMContentLoaded", () => {
  const seedCategoryChart = document.getElementById("seedCategoryChart");
  if (!seedCategoryChart) {
    return;
  }

  const rawData = seedCategoryChart.dataset.category || "{}";
  const categoryData = JSON.parse(rawData);
  const categoryLabels = Object.keys(categoryData);
  const categoryValues = Object.values(categoryData);
  if (!categoryLabels.length) {
    return;
  }

  const chartPalette = [
    "#3498db",
    "#9b59b6",
    "#e67e22",
    "#2ecc71",
    "#e74c3c",
    "#1abc9c",
    "#f39c12",
    "#7f8c8d",
    "#16a085",
    "#8e44ad",
  ];

  const ctx = seedCategoryChart.getContext("2d");
  const canvasSize = seedCategoryChart.clientWidth || 320;
  seedCategoryChart.width = canvasSize;
  seedCategoryChart.height = canvasSize;
  const size = Math.min(seedCategoryChart.width, 320);
  const radius = Math.min(size / 2 - 10, 150);
  const centerX = seedCategoryChart.width / 2;
  const centerY = seedCategoryChart.height / 2;
  const total = categoryValues.reduce((sum, value) => sum + value, 0) || 1;
  let startAngle = -Math.PI / 2;

  categoryValues.forEach((value, index) => {
    const sliceAngle = (value / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
    ctx.closePath();
    ctx.fillStyle = chartPalette[index % chartPalette.length];
    ctx.fill();
    startAngle += sliceAngle;
  });

  const legend = document.createElement("ul");
  legend.setAttribute("aria-label", "Seed category distribution");
  legend.style.listStyle = "none";
  legend.style.display = "grid";
  legend.style.gridTemplateColumns = "repeat(auto-fit, minmax(160px, 1fr))";
  legend.style.gap = "0.35rem";
  categoryLabels.forEach((label, index) => {
    const item = document.createElement("li");
    const swatch = document.createElement("span");
    swatch.style.display = "inline-block";
    swatch.style.width = "12px";
    swatch.style.height = "12px";
    swatch.style.marginRight = "8px";
    swatch.style.borderRadius = "3px";
    swatch.style.backgroundColor = chartPalette[index % chartPalette.length];
    const percent = ((categoryValues[index] / total) * 100).toFixed(1);
    item.appendChild(swatch);
    item.appendChild(
      document.createTextNode(`${label}: ${categoryValues[index]} (${percent}%)`)
    );
    legend.appendChild(item);
  });
  seedCategoryChart.parentElement.appendChild(legend);
});
