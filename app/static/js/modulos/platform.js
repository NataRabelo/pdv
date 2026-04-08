const platformState = {
  tenants: [],
};

const platformElements = {
  tenantGrid: document.getElementById("platformTenantGrid"),
  feedback: document.getElementById("platformFeedback"),
  totalTenants: document.getElementById("platformTotalTenants"),
  totalEmpresas: document.getElementById("platformTotalEmpresas"),
  totalAdmins: document.getElementById("platformTotalAdmins"),
  refreshButton: document.getElementById("refreshPlatformBtn"),
  overlay: document.getElementById("platformModalOverlay"),
  tenantModal: document.getElementById("tenantModal"),
  companyModal: document.getElementById("companyModal"),
  adminModal: document.getElementById("adminModal"),
  companyTenantName: document.getElementById("companyTenantName"),
  companyTenantId: document.getElementById("companyTenantId"),
  adminTenantName: document.getElementById("adminTenantName"),
  adminTenantId: document.getElementById("adminTenantId"),
  adminEmpresaId: document.getElementById("adminEmpresaId"),
  tenantForm: document.getElementById("tenantForm"),
  companyForm: document.getElementById("companyForm"),
  adminForm: document.getElementById("adminForm"),
  openTenantModalBtn: document.getElementById("openTenantModalBtn"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function showFeedback(message, type = "info") {
  if (!platformElements.feedback) {
    return;
  }

  platformElements.feedback.textContent = message;
  platformElements.feedback.className = `platform-feedback platform-feedback-${type}`;
  platformElements.feedback.classList.remove("hidden");
}

function clearFeedback() {
  if (!platformElements.feedback) {
    return;
  }

  platformElements.feedback.textContent = "";
  platformElements.feedback.className = "platform-feedback hidden";
}

async function requestJson(url, options = {}) {
  const config = {
    method: options.method || "GET",
    credentials: "same-origin",
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
    ...(options.body ? { body: JSON.stringify(options.body) } : {}),
  };

  const response = await fetch(url, config);
  const payload = await response.json().catch(() => ({}));

  if (!response.ok || payload.success === false) {
    throw new Error(payload.message || "Nao foi possivel concluir a operacao.");
  }

  return payload;
}

function formatDate(value) {
  if (!value) {
    return "Sem data";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Sem data";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function countTotals() {
  const totals = platformState.tenants.reduce((accumulator, tenant) => {
    accumulator.empresas += tenant.empresas.length;
    accumulator.admins += tenant.admins.length;
    return accumulator;
  }, { empresas: 0, admins: 0 });

  if (platformElements.totalTenants) {
    platformElements.totalTenants.textContent = String(platformState.tenants.length);
  }
  if (platformElements.totalEmpresas) {
    platformElements.totalEmpresas.textContent = String(totals.empresas);
  }
  if (platformElements.totalAdmins) {
    platformElements.totalAdmins.textContent = String(totals.admins);
  }
}

function renderTenantGrid() {
  if (!platformElements.tenantGrid) {
    return;
  }

  if (!platformState.tenants.length) {
    platformElements.tenantGrid.innerHTML = `
      <article class="platform-empty-state">
        <h4 class="text-xl font-semibold text-white mb-3">Nenhum tenant provisionado ainda</h4>
        <p>Use o botao "Novo tenant" para iniciar a estrutura multi-tenant da plataforma.</p>
      </article>
    `;
    lucide.createIcons();
    return;
  }

  platformElements.tenantGrid.innerHTML = platformState.tenants.map((tenant) => {
    const empresasHtml = tenant.empresas.length
      ? tenant.empresas.map((empresa) => `
          <li class="platform-list-item">
            <div>
              <strong class="platform-list-title">${escapeHtml(empresa.nome_fantasia)}</strong>
              <span class="platform-list-subtitle">${escapeHtml(empresa.razao_social)}</span>
            </div>
            <div class="text-right">
              <strong class="platform-list-title">${escapeHtml(empresa.tipo_empresa)}</strong>
              <span class="platform-list-subtitle">${escapeHtml(empresa.cnpj)}</span>
            </div>
          </li>
        `).join("")
      : `
          <li class="platform-list-item">
            <div>
              <strong class="platform-list-title">Sem empresas</strong>
              <span class="platform-list-subtitle">Cadastre a primeira empresa deste tenant.</span>
            </div>
          </li>
        `;

    const adminsHtml = tenant.admins.length
      ? tenant.admins.map((admin) => `
          <li class="platform-list-item">
            <div>
              <strong class="platform-list-title">${escapeHtml(admin.nome)}</strong>
              <span class="platform-list-subtitle">@${escapeHtml(admin.usuario)}</span>
            </div>
            <div class="text-right">
              <strong class="platform-list-title">${admin.ativo ? "Ativo" : "Inativo"}</strong>
              <span class="platform-list-subtitle">${escapeHtml(admin.cpf)}</span>
            </div>
          </li>
        `).join("")
      : `
          <li class="platform-list-item">
            <div>
              <strong class="platform-list-title">Sem admins adicionais</strong>
              <span class="platform-list-subtitle">Crie novos acessos administrativos quando precisar.</span>
            </div>
          </li>
        `;

    return `
      <article class="platform-tenant-card">
        <div class="platform-tenant-card-header">
          <div>
            <span class="platform-chip">Tenant #${tenant.id}</span>
            <h4 class="platform-tenant-name">${escapeHtml(tenant.nome)}</h4>
            <p class="platform-tenant-meta">Provisionado em ${formatDate(tenant.criado_em)}</p>
          </div>
          <button type="button" class="platform-inline-btn" data-action="open-company-modal" data-tenant-id="${tenant.id}">
            <i data-lucide="building"></i>
            Nova empresa
          </button>
        </div>

        <div class="platform-tenant-badges">
          <span class="platform-badge"><i data-lucide="briefcase-business"></i>${tenant.quantidade_empresas} empresas</span>
          <span class="platform-badge"><i data-lucide="shield-check"></i>${tenant.quantidade_admins} admins</span>
        </div>

        <div class="platform-list-block">
          <div class="platform-list-head">
            <strong>Empresas</strong>
          </div>
          <ul class="platform-list">${empresasHtml}</ul>
        </div>

        <div class="platform-list-block">
          <div class="platform-list-head">
            <strong>Admins</strong>
          </div>
          <ul class="platform-list">${adminsHtml}</ul>
        </div>

        <div class="platform-tenant-card-footer">
          <span class="platform-inline-meta">Tenant pronto para estoque, PDV e financeiro.</span>
          <div class="platform-inline-actions">
            <button type="button" class="platform-inline-btn" data-action="open-admin-modal" data-tenant-id="${tenant.id}">
              <i data-lucide="user-plus"></i>
              Novo admin
            </button>
          </div>
        </div>
      </article>
    `;
  }).join("");

  lucide.createIcons();
}

function getTenantById(tenantId) {
  return platformState.tenants.find((tenant) => tenant.id === Number(tenantId)) || null;
}

function openModal(modalElement) {
  if (!modalElement || !platformElements.overlay) {
    return;
  }

  clearFeedback();
  platformElements.overlay.classList.remove("hidden");
  modalElement.classList.remove("hidden");
  modalElement.setAttribute("aria-hidden", "false");
  lucide.createIcons();
}

function closeModals() {
  [platformElements.tenantModal, platformElements.companyModal, platformElements.adminModal].forEach((modal) => {
    if (!modal) {
      return;
    }

    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");
  });

  if (platformElements.overlay) {
    platformElements.overlay.classList.add("hidden");
  }

  if (platformElements.tenantForm) {
    platformElements.tenantForm.reset();
  }
  if (platformElements.companyForm) {
    platformElements.companyForm.reset();
  }
  if (platformElements.adminForm) {
    platformElements.adminForm.reset();
  }
}

function prepareCompanyModal(tenantId) {
  const tenant = getTenantById(tenantId);
  if (!tenant) {
    showFeedback("Tenant nao encontrado para cadastrar a empresa.", "error");
    return;
  }

  if (platformElements.companyTenantName) {
    platformElements.companyTenantName.textContent = tenant.nome;
  }
  if (platformElements.companyTenantId) {
    platformElements.companyTenantId.value = String(tenant.id);
  }

  openModal(platformElements.companyModal);
}

function prepareAdminModal(tenantId) {
  const tenant = getTenantById(tenantId);
  if (!tenant) {
    showFeedback("Tenant nao encontrado para cadastrar o admin.", "error");
    return;
  }

  if (!tenant.empresas.length) {
    showFeedback("Cadastre uma empresa antes de criar admins para esse tenant.", "error");
    return;
  }

  if (platformElements.adminTenantName) {
    platformElements.adminTenantName.textContent = tenant.nome;
  }
  if (platformElements.adminTenantId) {
    platformElements.adminTenantId.value = String(tenant.id);
  }
  if (platformElements.adminEmpresaId) {
      platformElements.adminEmpresaId.innerHTML = tenant.empresas.map((empresa) => `
      <option value="${empresa.id}">${escapeHtml(empresa.nome_fantasia)} - ${escapeHtml(empresa.cnpj)}</option>
    `).join("");
  }

  openModal(platformElements.adminModal);
}

async function loadTenants({ silent = false } = {}) {
  try {
    if (!silent) {
      showFeedback("Atualizando mapa da plataforma...", "info");
    }

    const response = await requestJson("/api/platform/tenants");
    platformState.tenants = response.data || [];
    countTotals();
    renderTenantGrid();

    if (!silent) {
      showFeedback("Painel atualizado com sucesso.", "success");
      window.setTimeout(() => clearFeedback(), 1800);
    }
  } catch (error) {
    showFeedback(error.message, "error");
  }
}

async function handleTenantSubmit(event) {
  event.preventDefault();

  const payload = {
    tenant_nome: document.getElementById("tenantNome").value.trim(),
    empresa: {
      razao_social: document.getElementById("tenantEmpresaRazaoSocial").value.trim(),
      nome_fantasia: document.getElementById("tenantEmpresaNomeFantasia").value.trim(),
      cnpj: document.getElementById("tenantEmpresaCnpj").value.trim(),
      tipo_empresa: document.getElementById("tenantEmpresaTipo").value,
    },
    admin: {
      nome: document.getElementById("tenantAdminNome").value.trim(),
      usuario: document.getElementById("tenantAdminUsuario").value.trim(),
      cpf: document.getElementById("tenantAdminCpf").value.trim(),
      senha: document.getElementById("tenantAdminSenha").value,
    },
  };

  try {
    await requestJson("/api/platform/tenants", { method: "POST", body: payload });
    closeModals();
    await loadTenants({ silent: true });
    showFeedback("Tenant provisionado com sucesso.", "success");
  } catch (error) {
    showFeedback(error.message, "error");
  }
}

async function handleCompanySubmit(event) {
  event.preventDefault();

  const tenantId = platformElements.companyTenantId?.value;
  const payload = {
    razao_social: document.getElementById("companyRazaoSocial").value.trim(),
    nome_fantasia: document.getElementById("companyNomeFantasia").value.trim(),
    cnpj: document.getElementById("companyCnpj").value.trim(),
    tipo_empresa: document.getElementById("companyTipoEmpresa").value,
  };

  try {
    await requestJson(`/api/platform/tenants/${tenantId}/empresas`, { method: "POST", body: payload });
    closeModals();
    await loadTenants({ silent: true });
    showFeedback("Empresa cadastrada com sucesso.", "success");
  } catch (error) {
    showFeedback(error.message, "error");
  }
}

async function handleAdminSubmit(event) {
  event.preventDefault();

  const tenantId = platformElements.adminTenantId?.value;
  const payload = {
    empresa_id: platformElements.adminEmpresaId?.value,
    nome: document.getElementById("adminNome").value.trim(),
    usuario: document.getElementById("adminUsuario").value.trim(),
    cpf: document.getElementById("adminCpf").value.trim(),
    senha: document.getElementById("adminSenha").value,
  };

  try {
    await requestJson(`/api/platform/tenants/${tenantId}/admins`, { method: "POST", body: payload });
    closeModals();
    await loadTenants({ silent: true });
    showFeedback("Admin cadastrado com sucesso.", "success");
  } catch (error) {
    showFeedback(error.message, "error");
  }
}

function bindEvents() {
  platformElements.openTenantModalBtn?.addEventListener("click", () => openModal(platformElements.tenantModal));
  platformElements.refreshButton?.addEventListener("click", () => loadTenants());
  platformElements.tenantForm?.addEventListener("submit", handleTenantSubmit);
  platformElements.companyForm?.addEventListener("submit", handleCompanySubmit);
  platformElements.adminForm?.addEventListener("submit", handleAdminSubmit);
  platformElements.overlay?.addEventListener("click", closeModals);

  document.querySelectorAll("[data-close-modal]").forEach((button) => {
    button.addEventListener("click", closeModals);
  });

  document.addEventListener("click", (event) => {
    const actionElement = event.target.closest("[data-action]");
    if (!actionElement) {
      return;
    }

    const tenantId = Number(actionElement.dataset.tenantId);
    const action = actionElement.dataset.action;

    if (action === "open-company-modal") {
      prepareCompanyModal(tenantId);
    }

    if (action === "open-admin-modal") {
      prepareAdminModal(tenantId);
    }
  });
}

bindEvents();
loadTenants();
