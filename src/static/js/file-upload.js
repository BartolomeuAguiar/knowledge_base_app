// -------------------------------------------------------------
// file-upload.js
// Preview de arquivo antes do upload no modal de “Fazer Upload”
// -------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {
  const fileInput = document.getElementById("file-input");
  const filePreview = document.getElementById("file-preview");
  const fileForm = document.getElementById("file-upload-form");

  if (!fileInput || !filePreview) return;

  fileInput.addEventListener("change", function () {
    filePreview.innerHTML = "";

    if (this.files && this.files.length > 0) {
      const file = this.files[0];
      const fileSize = (file.size / 1024 / 1024).toFixed(2); // em MB

      let icon = "fa-file";
      if (file.type.includes("pdf")) {
        icon = "fa-file-pdf";
      } else if (file.type.includes("zip") || file.type.includes("archive")) {
        icon = "fa-file-archive";
      } else if (file.type.includes("image")) {
        icon = "fa-file-image";
      }

      const preview = document.createElement("div");
      preview.className = "file-item";
      preview.innerHTML = `
        <div class="file-icon">
          <i class="fas ${icon}"></i>
        </div>
        <div class="file-info">
          <div class="file-name">${file.name}</div>
          <div class="file-meta">${fileSize} MB - ${file.type || "Tipo desconhecido"}</div>
        </div>
      `;

      filePreview.appendChild(preview);
    }
  });

  if (fileForm) {
    fileForm.addEventListener("submit", function (e) {
      const fileInputElement = document.getElementById("file-input");
      if (!fileInputElement.files || fileInputElement.files.length === 0) {
        e.preventDefault();
        alert("Por favor, selecione um arquivo para upload.");
      }
    });
  }
});
