window.permissionPage = null;
const permissionCanEdit = () => window.userHasPermission?.("editar_permission");
const permissionCanDelete = () => window.userHasPermission?.("excluir_permission");

document.addEventListener("DOMContentLoaded", () => {
    window.permissionPage = new CrudPage({
        apiBaseUrl: "/api/permissions/",
        tableBodyId: "permission-table-body",
        formCreateId: "form-cadastro",
        formEditId: "form-edicao",
        formDeleteId: "form-delete",
        modalCreateId: "modal-cadastro",
        modalEditId: "modal-edicao",
        modalDeleteId: "modal-delete",
        searchInputId: "input-busca",
        paginationContainerId: "permission-pagination",
        pageSize: 10,
        fields: ["nome", "codigo", "descricao"],
        messages: {
            loadError: "Erro ao carregar permissions.",
            createSuccess: "Permission cadastrada com sucesso.",
            createError: "Erro ao cadastrar permission.",
            updateSuccess: "Permission atualizada com sucesso.",
            updateError: "Erro ao atualizar permission.",
            deleteSuccess: "Permission excluida com sucesso.",
            deleteError: "Erro ao excluir permission."
        },
        mapItemToEditForm: (item) => ({
            nome: item.nome || "",
            codigo: item.codigo || "",
            descricao: item.descricao || "",
            ativo: Boolean(item.ativo)
        }),
        beforeOpenCreateModal: async () => {
            preencherCheckboxAtivo("cadastro-ativo", true);
        },
        beforeOpenEditModal: async (item) => {
            preencherCheckboxAtivo("edicao-ativo", item.ativo);
        },
        beforeSubmitCreate: (payload) => normalizarPayload(payload, false),
        beforeSubmitEdit: (payload) => normalizarPayload(payload, true),
        renderRow: (item) => `
            <tr class="hover:bg-slate-800/40 transition">
                <td class="px-5 py-4 align-middle">
                    <div class="flex items-center gap-3">
                        <div class="flex items-center justify-center w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
                            <i data-lucide="key-round" class="w-4 h-4"></i>
                        </div>
                        <div>
                            <p class="font-semibold text-white">${escapeHtml(item.nome || "-")}</p>
                            <p class="text-xs text-slate-500">${escapeHtml(item.codigo || "-")}</p>
                        </div>
                    </div>
                </td>

                <td class="px-5 py-4 align-middle">
                    <p class="text-slate-300 leading-relaxed">${escapeHtml(item.descricao || "Sem descricao cadastrada.")}</p>
                </td>

                <td class="px-5 py-4 align-middle">
                    <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${item.ativo ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20" : "bg-slate-700/30 text-slate-400 border border-slate-700"}">
                        ${item.ativo ? "Ativa" : "Inativa"}
                    </span>
                </td>

                <td class="px-5 py-4 align-middle">
                    <div class="flex items-center justify-center gap-2">
                        ${renderPermissionActions(item)}
                    </div>
                </td>
            </tr>
        `
    });

    window.permissionPage.init();

    if (window.lucide) {
        lucide.createIcons();
    }
});

function normalizarPayload(payload, isEdit) {
    return {
        ...payload,
        nome: (payload.nome || "").trim(),
        codigo: (payload.codigo || "").trim(),
        descricao: (payload.descricao || "").trim(),
        ativo: obterCheckboxAtivo(isEdit ? "edicao-ativo" : "cadastro-ativo")
    };
}

function obterCheckboxAtivo(id) {
    const checkbox = document.getElementById(id);
    return checkbox ? checkbox.checked : true;
}

function preencherCheckboxAtivo(id, value) {
    const checkbox = document.getElementById(id);
    if (checkbox) {
        checkbox.checked = Boolean(value);
    }
}

function escapeHtml(value) {
    if (value === null || value === undefined) return "";

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function renderPermissionActions(item) {
    const actions = [];

    if (permissionCanEdit()) {
        actions.push(`
            <button
                type="button"
                onclick="permissionPage.openEditModal(${item.id})"
                class="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-amber-400/10 border border-amber-400/20 text-amber-300 hover:bg-amber-400/20 transition"
                title="Editar permission"
            >
                <i data-lucide="square-pen" class="w-4 h-4"></i>
            </button>
        `);
    }

    if (permissionCanDelete()) {
        actions.push(`
            <button
                type="button"
                onclick="permissionPage.openDeleteModal(${item.id})"
                class="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 transition"
                title="Excluir permission"
            >
                <i data-lucide="trash-2" class="w-4 h-4"></i>
            </button>
        `);
    }

    return actions.length
        ? actions.join("")
        : '<span class="text-xs font-medium text-slate-500">Somente leitura</span>';
}
