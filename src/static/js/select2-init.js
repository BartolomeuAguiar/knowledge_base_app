// -------------------------------------------------------------
// select2-init.js
// Inicializa o Select2 em campos de tag, com criação de novas
// tags apenas se data-allow-new="true" estiver presente
// -------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {
  const selectTag = document.querySelector(".select2-tags");
  if (!selectTag) return;

  // O jQuery transformará data-allow-new em data("allowNew")
  const allowNew = $(selectTag).data("allowNew") === true;

  $(selectTag).select2({
    tags: allowNew,
    tokenSeparators: [","],
    placeholder: "Selecione ou digite tags...",
    createTag: function (params) {
      if (!allowNew) return null;
      const term = params.term.trim();
      if (term === "") return null;
      return {
        id: term,
        text: "Criar nova TAG: " + term,
        newTag: true
      };
    },
    templateSelection: function (data) {
      if (data.newTag) {
        return data.id;
      }
      return data.text;
    },
    templateResult: function (data) {
      return data.text;
    }
  });
});
