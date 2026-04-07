window.rolePage = null;

document.addEventListener("DOMContentLoaded", async () => {
    window.rolePage = new CrudPage({
        apiBaseUrl: "/api/roles/",
        tableBodyId: "role-table-body",
        formCreateId: "form-cadastro",
        formEditId: "form-edicao",
        formDeleteId: "form-delete",
        modalCreateId: "modal-cadastro",
        modalEditId: "modal-edicao",
        modalDeleteId: "modal-delete",
        searchInputId: "input-busca",
        paginationContainerId: "role-pagination",
        pageSize: 10,
        fields: ["nome", "codigo", "descricao", "permissions_text"],
        messages: {
            loadError: "Erro ao carregar roles.",
            createSuccess: "Role cadastrada com sucesso.",
            createError: "Erro ao cadastrar role.",
            updateSuccess: "Role atualizada com sucesso.",
            updateError: "Erro ao atualizar role.",
            deleteSuccess: "Role excluida com sucesso.",
            deleteError: "Erro ao excluir role."
        },
        mapItemToEditForm: (item) => ({
            nome: item.nome || "",
            codigo: item.codigo || "",
            descricao: item.descricao || "",
            ativo: Boolean(item.ativo)
        }),
        beforeOpenCreateModal: async () => {
            await carregarPermissions("cadastro-permissions");
            preencherCheckboxAtivo("cadastro-ativo", true);
        },
        beforeOpenEditModal: async (item) => {
            await carregarPermissions("edicao-permissions", item.permission_ids || []);
            preencherCheckboxAtivo("edicao-ativo", item.ativo);
        },
        beforeSubmitCreate: () => normalizarPayload(false),
        beforeSubmitEdit: () => normalizarPayload(true),
        renderRow: (item) => `
            <tr class="hover:bg-slate-800/40 transition">
                <td class="px-5 py-4 align-middle">
                    <div class="flex items-center gap-3">
                        <div class="flex items-center justify-center w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
                            <i data-lucide="shield-check" class="w-4 h-4"></i>
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
                    <div class="flex flex-wrap gap-2">
                        ${(item.permissions || []).length
                            ? item.permissions.map((permission) => `
                                <span class="inline-flex items-center rounded-full border border-sky-500/20 bg-sky-500/10 px-2.5 py-1 text-xs text-sky-300">
                                    ${escapeHtml(permission.codigo)}
                                </span>
                            `).join("")
                            : '<span class="text-slate-500 text-sm">Sem permissions vinculadas.</span>'}
                    </div>
                </td>

                <td class="px-5 py-4 align-middle">
                    <div class="flex items-center justify-center gap-2">
                        <button
                            type="button"
                            onclick="rolePage.openEditModal(${item.id})"
                            class="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-amber-400/10 border border-amber-400/20 text-amber-300 hover:bg-amber-400/20 transition"
                            title="Editar role"
                        >
                            <i data-lucide="square-pen" class="w-4 h-4"></i>
                        </button>

                        <button
                            type="button"
                            onclick="rolePage.openDeleteModal(${item.id})"
                            class="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 transition"
                            title="Excluir role"
                        >
                            <i data-lucide="trash-2" class="w-4 h-4"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `
    });

    window.rolePage.init();

    if (window.lucide) {
        lucide.createIcons();
    }
});

async function carregarPermissions(containerId, selectedIds = []) {
    const container = document.getElementById(containerId);
    if (!container) return;

    try {
        const response = await fetch("/api/roles/permissions-disponiveis", {
            credentials: "same-origin",
            headers: getAuthHeaders()
        });
        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.message || "Erro ao carregar permissions.");
        }

        const selected = new Set((selectedIds || []).map((id) => String(id)));

        container.innerHTML = result.data.map((permission) => `
            <label class="flex items-start gap-3 rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 hover:border-sky-500/40 transition">
                <input
                    type="checkbox"
                    name="permission_ids"
                    value="${permission.id}"
                    class="mt-1 rounded border-slate-700 bg-slate-900 text-sky-500 focus:ring-sky-500"
                    ${selected.has(String(permission.id)) ? "checked" : ""}
                >
                <span class="min-w-0">
                    <span class="block text-sm font-medium text-white">${escapeHtml(permission.nome || permission.codigo)}</span>
                    <span class="block text-xs text-slate-500">${escapeHtml(permission.codigo || "")}</span>
                </span>
            </label>
        `).join("");
    } catch (error) {
        container.innerHTML = `<p class="text-sm text-red-400">${escapeHtml(error.message)}</p>`;
    }
}

function normalizarPayload(isEdit) {
    const prefix = isEdit ? "edicao" : "cadastro";

    return {
        nome: (document.getElementById(`${prefix}-nome`)?.value || "").trim(),
        codigo: (document.getElementById(`${prefix}-codigo`)?.value || "").trim(),
        descricao: (document.getElementById(`${prefix}-descricao`)?.value || "").trim(),
        ativo: obterCheckboxAtivo(`${prefix}-ativo`),
        permission_ids: coletarPermissionIds(`${prefix}-permissions`)
    };
}

function coletarPermissionIds(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return [];

    return Array.from(container.querySelectorAll('input[name="permission_ids"]:checked'))
        .map((input) => input.value);
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

function getAuthHeaders() {
    const token = localStorage.getItem("token");
    return {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {})
    };
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
