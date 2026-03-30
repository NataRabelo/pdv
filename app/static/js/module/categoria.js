lucide.createIcons();

const API_URL = "/api/categorias";
let categoriasCache = [];

/* =========================
   MODAIS
========================= */
function openModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;

  modal.classList.remove("hidden");
  modal.style.display = "flex";
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;

  modal.classList.add("hidden");
  modal.style.display = "none";
}

/* =========================
   INIT
========================= */
document.addEventListener("DOMContentLoaded", async () => {
  await carregarCategorias();
});

/* =========================
   LISTAR
========================= */
async function carregarCategorias() {
  try {
    const res = await fetch(API_URL);
    const data = await res.json();

    if (!data.success) {
      console.error("Erro ao listar categorias:", data.message);
      return;
    }

    categoriasCache = Array.isArray(data.data) ? data.data : [];
    renderTabela(categoriasCache);
  } catch (err) {
    console.error("Erro ao carregar categorias:", err);
  }
}

/* =========================
   RENDER
========================= */
function renderTabela(categorias) {
  const tbody = document.getElementById("categorias-body");
  if (!tbody) return;

  tbody.innerHTML = "";

  if (!categorias.length) {
    tbody.innerHTML = `
      <tr id="linha-vazia">
        <td colspan="3" class="text-center text-slate-500 py-6">
          Nenhuma categoria cadastrada
        </td>
      </tr>
    `;
    return;
  }

  categorias.forEach((categoria) => {
    tbody.appendChild(criarLinhaCategoria(categoria));
  });

  lucide.createIcons();
}

function criarLinhaCategoria(categoria) {
  const tr = document.createElement("tr");
  tr.setAttribute("data-id", categoria.id);

  tr.innerHTML = `
    <td class="table-cell font-semibold text-white">${escapeHtml(categoria.nome)}</td>
    <td class="table-cell text-slate-400">${escapeHtml(categoria.descricao || "")}</td>
    <td class="table-cell text-right">
      <div class="flex justify-end gap-2">
        <button
          type="button"
          class="btn-editar p-2 text-sky-400"
          data-id="${categoria.id}"
          data-nome="${escapeAttr(categoria.nome)}"
          data-descricao="${escapeAttr(categoria.descricao || "")}">
          <i data-lucide="pencil"></i>
        </button>

        <button
          type="button"
          class="btn-delete p-2 text-rose-400"
          data-id="${categoria.id}">
          <i data-lucide="trash"></i>
        </button>
      </div>
    </td>
  `;

  return tr;
}

function atualizarLinhaCategoria(categoria) {
  const tbody = document.getElementById("categorias-body");
  const linhaExistente = tbody.querySelector(`tr[data-id="${categoria.id}"]`);

  if (!linhaExistente) {
    removerLinhaVazia();
    tbody.prepend(criarLinhaCategoria(categoria));
    lucide.createIcons();
    return;
  }

  const novaLinha = criarLinhaCategoria(categoria);
  linhaExistente.replaceWith(novaLinha);
  lucide.createIcons();
}

function removerLinhaCategoria(id) {
  const tbody = document.getElementById("categorias-body");
  const linha = tbody.querySelector(`tr[data-id="${id}"]`);

  if (linha) {
    linha.remove();
  }

  if (!tbody.querySelector("tr[data-id]")) {
    tbody.innerHTML = `
      <tr id="linha-vazia">
        <td colspan="3" class="text-center text-slate-500 py-6">
          Nenhuma categoria cadastrada
        </td>
      </tr>
    `;
  }
}

function removerLinhaVazia() {
  const linhaVazia = document.getElementById("linha-vazia");
  if (linhaVazia) linhaVazia.remove();
}

/* =========================
   CREATE
========================= */
const formCadastro = document.getElementById("form-cadastro");
if (formCadastro) {
  formCadastro.addEventListener("submit", async function (e) {
    e.preventDefault();

    const nome = document.getElementById("nome")?.value.trim();
    const descricao = document.getElementById("descricao")?.value.trim() || "";

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome, descricao })
      });

      const data = await res.json();

      if (!data.success) {
        console.error("Erro ao cadastrar:", data.message);
        return;
      }

      const novaCategoria = data.data;

      categoriasCache.unshift(novaCategoria);
      removerLinhaVazia();

      const tbody = document.getElementById("categorias-body");
      tbody.prepend(criarLinhaCategoria(novaCategoria));

      lucide.createIcons();
      closeModal("modal-cadastro");
      this.reset();
    } catch (err) {
      console.error("Erro ao cadastrar categoria:", err);
    }
  });
}

/* =========================
   CLICK ACTIONS
========================= */
document.addEventListener("click", function (e) {
  const editBtn = e.target.closest(".btn-editar");
  if (editBtn) {
    const editId = document.getElementById("edit-id");
    const editNome = document.getElementById("edit-nome");
    const editDescricao = document.getElementById("edit-descricao");

    if (!editId || !editNome || !editDescricao) {
      console.error("Campos do modal de edição não encontrados.");
      return;
    }

    editId.value = editBtn.dataset.id || "";
    editNome.value = editBtn.dataset.nome || "";
    editDescricao.value = editBtn.dataset.descricao || "";

    openModal("modal-edicao");
    return;
  }

  const delBtn = e.target.closest(".btn-delete");
  if (delBtn) {
    const deleteId = document.getElementById("delete-id");

    if (!deleteId) {
      console.error("Campo delete-id não encontrado.");
      return;
    }

    deleteId.value = delBtn.dataset.id || "";
    openModal("modal-deletar");
  }
});

/* =========================
   UPDATE
========================= */
const formEdicao = document.getElementById("form-edicao");
if (formEdicao) {
  formEdicao.addEventListener("submit", async function (e) {
    e.preventDefault();

    const id = document.getElementById("edit-id")?.value;
    const nome = document.getElementById("edit-nome")?.value.trim();
    const descricao = document.getElementById("edit-descricao")?.value.trim() || "";

    if (!id) {
      console.error("ID da categoria não encontrado.");
      return;
    }

    try {
      const res = await fetch(`${API_URL}/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome, descricao })
      });

      const data = await res.json();

      if (!data.success) {
        console.error("Erro ao atualizar:", data.message);
        return;
      }

      const categoriaAtualizada = {
        id: Number(id),
        nome,
        descricao
      };

      categoriasCache = categoriasCache.map((categoria) =>
        Number(categoria.id) === Number(id) ? categoriaAtualizada : categoria
      );

      atualizarLinhaCategoria(categoriaAtualizada);
      closeModal("modal-edicao");
    } catch (err) {
      console.error("Erro ao editar categoria:", err);
    }
  });
}

/* =========================
   DELETE
========================= */
const formDelete = document.getElementById("form-delete");
if (formDelete) {
  formDelete.addEventListener("submit", async function (e) {
    e.preventDefault();

    const id = document.getElementById("delete-id")?.value;

    if (!id) {
      console.error("ID da categoria não encontrado para exclusão.");
      return;
    }

    try {
      const res = await fetch(`${API_URL}/${id}`, {
        method: "DELETE"
      });

      const data = await res.json();

      if (!data.success) {
        console.error("Erro ao deletar:", data.message);
        return;
      }

      categoriasCache = categoriasCache.filter(
        (categoria) => Number(categoria.id) !== Number(id)
      );

      removerLinhaCategoria(id);
      closeModal("modal-deletar");
    } catch (err) {
      console.error("Erro ao deletar categoria:", err);
    }
  });
}

/* =========================
   HELPERS
========================= */
function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}