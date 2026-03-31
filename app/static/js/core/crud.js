window.CrudPage = class CrudPage {
    constructor(config) {
        this.config = {
            apiBaseUrl: "",
            tableBodyId: "",
            formCreateId: "",
            formEditId: "",
            formDeleteId: "",
            modalCreateId: "",
            modalEditId: "",
            modalDeleteId: "",
            searchInputId: "",
            fields: [],
            renderRow: null,
            mapItemToEditForm: null,
            messages: {
                loadError: "Erro ao carregar registros.",
                createSuccess: "Registro criado com sucesso.",
                createError: "Erro ao criar registro.",
                updateSuccess: "Registro atualizado com sucesso.",
                updateError: "Erro ao atualizar registro.",
                deleteSuccess: "Registro deletado com sucesso.",
                deleteError: "Erro ao deletar registro."
            },
            ...config
        };

        this.items = [];
        this.currentEditId = null;
        this.currentDeleteId = null;
    }

    init() {
        this.bindCreateForm();
        this.bindEditForm();
        this.bindDeleteForm();
        this.bindSearch();
        this.bindModalClose();
        this.load();
    }

    getToken() {
        return localStorage.getItem("token");
    }

    getHeaders(isJson = true) {
        const headers = {
            "Authorization": `Bearer ${this.getToken()}`
        };

        if (isJson) {
            headers["Content-Type"] = "application/json";
        }

        return headers;
    }

    async request(url, options = {}) {
        const response = await fetch(url, options);

        let result;
        try {
            result = await response.json();
        } catch {
            result = {
                success: false,
                message: "Resposta inválida do servidor."
            };
        }

        if (!response.ok || result.success === false) {
            throw new Error(result.message || "Erro na requisição.");
        }

        return result;
    }

    async load() {
        try {
            const result = await this.request(this.config.apiBaseUrl, {
                method: "GET",
                headers: this.getHeaders(false)
            });

            this.items = Array.isArray(result.data) ? result.data : [];
            this.renderTable(this.items);
        } catch (error) {
            this.showMessage(error.message || this.config.messages.loadError, "error");
        }
    }

    renderTable(data) {
        const tableBody = document.getElementById(this.config.tableBodyId);
        if (!tableBody) return;

        if (!data.length) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="99" class="text-center py-6 text-slate-400">
                        Nenhum registro encontrado.
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = data.map(item => this.config.renderRow(item, this)).join("");

        if (window.lucide) {
            lucide.createIcons();
        }
    }

    filter(term) {
        const value = (term || "").toLowerCase().trim();

        if (!value) {
            this.renderTable(this.items);
            return;
        }

        const filtered = this.items.filter(item => {
            return this.config.fields.some(field => {
                const fieldValue = item[field];
                return String(fieldValue || "").toLowerCase().includes(value);
            });
        });

        this.renderTable(filtered);
    }

    collectFormData(form) {
        const formData = new FormData(form);
        const data = {};

        for (const [key, value] of formData.entries()) {
            data[key] = typeof value === "string" ? value.trim() : value;
        }

        return data;
    }

    clearForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return;

        form.reset();
    }

    fillForm(formId, data) {
        const form = document.getElementById(formId);
        if (!form) return;

        Object.keys(data).forEach(key => {
            const field = form.querySelector(`[name="${key}"]`);
            if (field) {
                field.value = data[key] ?? "";
            }
        });
    }

    bindCreateForm() {
        if (!this.config.formCreateId) return;

        const form = document.getElementById(this.config.formCreateId);
        if (!form) return;

        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            try {
                const data = this.collectFormData(form);

                await this.request(this.config.apiBaseUrl, {
                    method: "POST",
                    headers: this.getHeaders(true),
                    body: JSON.stringify(data)
                });

                this.showMessage(this.config.messages.createSuccess, "success");
                this.closeModal(this.config.modalCreateId);
                this.clearForm(this.config.formCreateId);
                await this.load();
            } catch (error) {
                this.showMessage(error.message || this.config.messages.createError, "error");
            }
        });
    }

    bindEditForm() {
        if (!this.config.formEditId) return;

        const form = document.getElementById(this.config.formEditId);
        if (!form) return;

        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            if (!this.currentEditId) {
                this.showMessage("Registro de edição não definido.", "error");
                return;
            }

            try {
                const data = this.collectFormData(form);

                await this.request(`${this.config.apiBaseUrl}${this.currentEditId}`, {
                    method: "PUT",
                    headers: this.getHeaders(true),
                    body: JSON.stringify(data)
                });

                this.showMessage(this.config.messages.updateSuccess, "success");
                this.closeModal(this.config.modalEditId);
                this.currentEditId = null;
                await this.load();
            } catch (error) {
                this.showMessage(error.message || this.config.messages.updateError, "error");
            }
        });
    }

    bindDeleteForm() {
        if (!this.config.formDeleteId) return;

        const form = document.getElementById(this.config.formDeleteId);
        if (!form) return;

        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            if (!this.currentDeleteId) {
                this.showMessage("Registro de exclusão não definido.", "error");
                return;
            }

            try {
                await this.request(`${this.config.apiBaseUrl}${this.currentDeleteId}`, {
                    method: "DELETE",
                    headers: this.getHeaders(false)
                });

                this.showMessage(this.config.messages.deleteSuccess, "success");
                this.closeModal(this.config.modalDeleteId);
                this.currentDeleteId = null;
                await this.load();
            } catch (error) {
                this.showMessage(error.message || this.config.messages.deleteError, "error");
            }
        });
    }

    bindSearch() {
        if (!this.config.searchInputId) return;

        const input = document.getElementById(this.config.searchInputId);
        if (!input) return;

        input.addEventListener("input", () => {
            this.filter(input.value);
        });
    }

    bindModalClose() {
        document.addEventListener("click", (e) => {
            const closeTrigger = e.target.closest("[data-close-modal]");
            if (!closeTrigger) return;

            const modalId = closeTrigger.getAttribute("data-close-modal");
            if (modalId) {
                this.closeModal(modalId);
            }
        });

        window.addEventListener("click", (e) => {
            if (e.target.classList.contains("modal-overlay")) {
                e.target.classList.add("hidden");
            }
        });
    }

    openCreateModal() {
        this.clearForm(this.config.formCreateId);
        this.openModal(this.config.modalCreateId);
    }

    openEditModal(id) {
        const item = this.items.find(x => String(x.id) === String(id));

        if (!item) {
            this.showMessage("Registro não encontrado para edição.", "error");
            return;
        }

        this.currentEditId = id;

        const mappedData = this.config.mapItemToEditForm
            ? this.config.mapItemToEditForm(item)
            : item;

        this.fillForm(this.config.formEditId, mappedData);
        this.openModal(this.config.modalEditId);
    }

    openDeleteModal(id) {
        this.currentDeleteId = id;
        this.openModal(this.config.modalDeleteId);
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        modal.classList.remove("hidden");
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        modal.classList.add("hidden");
    }

    showMessage(message, type = "success") {
        const old = document.getElementById("crud-message");

        if (old) {
            old.remove();
        }

        const div = document.createElement("div");
        div.id = "crud-message";
        div.className = `
            fixed top-4 right-4 z-[9999] px-4 py-3 rounded-xl shadow-lg text-sm font-medium
            ${type === "success" ? "bg-emerald-500 text-white" : "bg-red-500 text-white"}
        `;
        div.textContent = message;

        document.body.appendChild(div);

        setTimeout(() => {
            div.remove();
        }, 3000);
    }
};