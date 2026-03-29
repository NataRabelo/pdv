lucide.createIcons();

const API_URL = "/api/categorias";

/* =========================
   MODAIS
========================= */
function openModal(id) {
  document.getElementById(id).style.display = "flex";
}

function closeModal(id) {
  document.getElementById(id).style.display = "none";
}

/* =========================
   LOAD INICIAL
========================= */
document.addEventListener("DOMContentLoaded", () => {
  carregarCategorias();
});

/* =========================
   LISTAR
========================= */
async function carregarCategorias() {
  try {
    const response = await fetch(API_URL);
    const data = await response.json();

    if (data.success) {
      renderTabela(data.data);
    }

  } catch (error) {
    console.error("Erro ao carregar categorias:", error);
  }
}

/* =========================
   RENDER TABELA
========================= */
function renderTabela(categorias) {
  const tbody = document.getElementById("categorias-body");
  tbody.innerHTML = "";

  if (!categorias.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="3" class="text-center text-slate-500 py-6">
          Nenhuma categoria cadastrada
        </td>
      </tr>
    `;
    return;
  }

  categorias.forEach((categoria) => {
    const tr = document.createElement("tr");
    tr.classList.add("table-row");
    tr.id = `categoria-${categoria.id}`;

    tr.innerHTML = `
      <td class="table-cell font-semibold text-white">
        ${categoria.nome}
      </td>
      <td class="table-cell text-slate-400">
        ${categoria.descricao || ""}
      </td>
      <td class="table-cell text-right">
        <div class="flex justify-end gap-2">

          <button class="btn-editar p-2 text-sky-400"
            data-id="${categoria.id}"
            data-nome="${categoria.nome}"
            data-descricao="${categoria.descricao || ""}">
            ✏️
          </button>

          <button class="btn-delete p-2 text-rose-400"
            data-id="${categoria.id}">
            🗑️
          </button>

        </div>
      </td>
    `;

    tbody.appendChild(tr);
  });
}

/* =========================
   CREATE (CADASTRAR)
========================= */
document.getElementById("form-cadastro")
?.addEventListener("submit", async function (e) {
  e.preventDefault();

  const nome = document.getElementById("nome").value;
  const descricao = document.getElementById("descricao").value;

  const btn = this.querySelector('button[type="submit"]');
  btn.disabled = true;
  btn.innerText = "Salvando...";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Se usar JWT:
        // "Authorization": "Bearer " + localStorage.getItem("token")
      },
      body: JSON.stringify({ nome, descricao })
    });

    const data = await response.json();

    if (response.ok && data.success) {
      adicionarNaTabela(data.data);
      closeModal("modal-cadastro");
      this.reset();
    } else {
      throw new Error(data.message);
    }

  } catch (error) {
    alert(error.message || "Erro ao cadastrar");
  } finally {
    btn.disabled = false;
    btn.innerText = "Salvar Categoria";
  }
});

/* =========================
   ADD LINHA (SEM RELOAD)
========================= */
function adicionarNaTabela(categoria) {
  const tbody = document.getElementById("categorias-body");

  const tr = document.createElement("tr");
  tr.classList.add("table-row");
  tr.id = `categoria-${categoria.id}`;

  tr.innerHTML = `
    <td class="table-cell font-semibold text-white">
      ${categoria.nome}
    </td>
    <td class="table-cell text-slate-400">
      ${categoria.descricao || ""}
    </td>
    <td class="table-cell text-right">
      <div class="flex justify-end gap-2">

        <button class="btn-editar p-2 text-sky-400"
          data-id="${categoria.id}"
          data-nome="${categoria.nome}"
          data-descricao="${categoria.descricao || ""}">
          ✏️
        </button>

        <button class="btn-delete p-2 text-rose-400"
          data-id="${categoria.id}">
          🗑️
        </button>

      </div>
    </td>
  `;

  tbody.appendChild(tr);
}

/* =========================
   DELETE
========================= */
let deleteId = null;

function confirmarDelete(id) {
  deleteId = id;
  openModal("modal-deletar");
}

document.getElementById("form-delete")
?.addEventListener("submit", async function (e) {
  e.preventDefault();

  const btn = this.querySelector('button[type="submit"]');
  btn.disabled = true;
  btn.innerText = "Deletando...";

  try {
    const response = await fetch(`${API_URL}/${deleteId}`, {
      method: "DELETE"
    });

    const data = await response.json();

    if (response.ok && data.success) {
      document.getElementById(`categoria-${deleteId}`)?.remove();
      closeModal("modal-deletar");
    } else {
      throw new Error(data.message);
    }

  } catch (error) {
    alert(error.message || "Erro ao deletar");
  } finally {
    btn.disabled = false;
    btn.innerText = "Deletar";
  }
});

/* =========================
   EVENT DELEGATION (EDIT/DELETE)
========================= */
document.addEventListener("click", function (e) {

  const btnDelete = e.target.closest(".btn-delete");
  if (btnDelete) {
    confirmarDelete(btnDelete.dataset.id);
  }

  const btnEdit = e.target.closest(".btn-editar");
  if (btnEdit) {
    abrirModalEdicao(
      btnEdit.dataset.id,
      btnEdit.dataset.nome,
      btnEdit.dataset.descricao
    );
  }
});

/* =========================
   MODAL EDITAR (PREPARADO)
========================= */
function abrirModalEdicao(id, nome, descricao) {
  document.getElementById("edit-id").value = id;
  document.getElementById("edit-nome").value = nome;
  document.getElementById("edit-descricao").value = descricao;

  openModal("modal-edicao");
}

/* =========================
   CLICK FORA MODAL
========================= */
window.onclick = function (event) {
  if (event.target.classList.contains("modal-overlay")) {
    event.target.style.display = "none";
  }
};