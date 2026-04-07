window.categoriaPage = null;

document.addEventListener("DOMContentLoaded", () => {
    window.categoriaPage = new CrudPage({
        apiBaseUrl: "/api/categorias/",
        tableBodyId: "categoria-table-body",
        formCreateId: "form-cadastro",
        formEditId: "form-edicao",
        formDeleteId: "form-delete",
        modalCreateId: "modal-cadastro",
        modalEditId: "modal-edicao",
        modalDeleteId: "modal-delete",
        searchInputId: "input-busca",
        paginationContainerId: "categoria-pagination",
        pageSize: 10,
        fields: ["nome", "descricao"],

        messages: {
            loadError: "Erro ao carregar categorias.",
            createSuccess: "Categoria cadastrada com sucesso.",
            createError: "Erro ao cadastrar categoria.",
            updateSuccess: "Categoria atualizada com sucesso.",
            updateError: "Erro ao atualizar categoria.",
            deleteSuccess: "Categoria excluída com sucesso.",
            deleteError: "Erro ao excluir categoria."
        },

        mapItemToEditForm: (item) => ({
            nome: item.nome || "",
            descricao: item.descricao || ""
        }),

        renderRow: (item) => {
            return `
                <tr class="hover:bg-slate-800/40 transition">
                    <td class="px-5 py-4 align-middle">
                        <div class="flex items-center gap-3">
                            <div class="flex items-center justify-center w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
                                <i data-lucide="folder-tree" class="w-4 h-4"></i>
                            </div>
                            <div>
                                <p class="font-semibold text-white">${escapeHtml(item.nome || "-")}</p>
                                <p class="text-xs text-slate-500">ID #${item.id}</p>
                            </div>
                        </div>
                    </td>

                    <td class="px-5 py-4 align-middle">
                        <p class="text-slate-300 leading-relaxed">
                            ${escapeHtml(item.descricao || "Sem descrição cadastrada.")}
                        </p>
                    </td>

                    <td class="px-5 py-4 align-middle">
                        <div class="flex items-center justify-center gap-2">
                            <button
                                type="button"
                                onclick="categoriaPage.openEditModal(${item.id})"
                                class="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-amber-400/10 border border-amber-400/20 text-amber-300 hover:bg-amber-400/20 transition"
                                title="Editar categoria"
                            >
                                <i data-lucide="square-pen" class="w-4 h-4"></i>
                            </button>

                            <button
                                type="button"
                                onclick="categoriaPage.openDeleteModal(${item.id})"
                                class="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 transition"
                                title="Excluir categoria"
                            >
                                <i data-lucide="trash-2" class="w-4 h-4"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }
    });

    window.categoriaPage.init();

    if (window.lucide) {
        lucide.createIcons();
    }
});

function escapeHtml(value) {
    if (value === null || value === undefined) return "";

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
