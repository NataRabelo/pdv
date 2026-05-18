(function () {
    const fiscalPage = {
        auxiliares: { empresas: [], ambientes: [], regimes_tributarios: [] },
        empresaId: "",
        configuracaoAtual: null,
        notas: []
    };

    document.addEventListener("DOMContentLoaded", async () => {
        bindFiscalEvents();
        await carregarAuxiliaresFiscal();
        if (fiscalPage.auxiliares.empresas.length === 1) {
            fiscalPage.empresaId = String(fiscalPage.auxiliares.empresas[0].id);
        }
        popularSelectsFiscal();
        if (fiscalPage.empresaId) {
            document.getElementById("fiscal-empresa").value = fiscalPage.empresaId;
            await carregarConfiguracaoFiscal(fiscalPage.empresaId);
        }
        await carregarNotasFiscais();
        if (window.lucide) {
            lucide.createIcons();
        }
    });

    function bindFiscalEvents() {
        const empresaSelect = document.getElementById("fiscal-empresa");
        const configForm = document.getElementById("fiscal-config-form");
        const prevalidacaoForm = document.getElementById("fiscal-prevalidacao-form");

        document.addEventListener("click", async (event) => {
            const emitirButton = event.target.closest("[data-fiscal-emitir-venda]");
            const xmlButton = event.target.closest("[data-fiscal-baixar-xml]");

            if (emitirButton) {
                event.preventDefault();
                await emitirNotaFiscal(emitirButton.dataset.fiscalEmitirVenda);
            }

            if (xmlButton) {
                event.preventDefault();
                baixarXmlNota(xmlButton.dataset.fiscalBaixarXml);
            }
        });

        if (empresaSelect) {
            empresaSelect.addEventListener("change", async () => {
                fiscalPage.empresaId = empresaSelect.value || "";
                if (!fiscalPage.empresaId) {
                    fiscalPage.configuracaoAtual = null;
                    atualizarStatusConfiguracao("Selecione uma empresa para carregar a configuracao fiscal.");
                    limparFormularioConfiguracao();
                    return;
                }
                await carregarConfiguracaoFiscal(fiscalPage.empresaId);
            });
        }

        if (configForm) {
            configForm.addEventListener("submit", async (event) => {
                event.preventDefault();
                if (!fiscalPage.empresaId) {
                    mostrarMensagemFiscal("Selecione uma empresa antes de salvar a configuracao.", "error");
                    return;
                }

                try {
                    const payload = montarPayloadConfiguracao();
                    const result = await requestFiscal(`/api/fiscal/configuracao/${fiscalPage.empresaId}`, {
                        method: "PUT",
                        headers: getFiscalHeaders(true),
                        body: JSON.stringify(payload)
                    });
                    fiscalPage.configuracaoAtual = result.data || null;
                    preencherFormularioConfiguracao(fiscalPage.configuracaoAtual);
                    renderizarStatusConfiguracao(fiscalPage.configuracaoAtual);
                    await carregarNotasFiscais();
                    mostrarMensagemFiscal(result.message || "Configuracao fiscal atualizada com sucesso.");
                } catch (error) {
                    mostrarMensagemFiscal(error.message || "Erro ao salvar configuracao fiscal.", "error");
                }
            });
        }

        if (prevalidacaoForm) {
            prevalidacaoForm.addEventListener("submit", async (event) => {
                event.preventDefault();
                const vendaId = document.getElementById("fiscal-venda-id")?.value || "";
                if (!vendaId) {
                    mostrarMensagemFiscal("Informe a venda que deseja prevalidar.", "error");
                    return;
                }

                try {
                    const result = await requestFiscal("/api/fiscal/notas/prevalidar", {
                        method: "POST",
                        headers: getFiscalHeaders(true),
                        body: JSON.stringify({ venda_id: vendaId })
                    });
                    renderizarResultadoPrevalidacao(result.data || null);
                    await carregarNotasFiscais();
                    mostrarMensagemFiscal(result.message || "Prevalidacao executada com sucesso.");
                } catch (error) {
                    mostrarMensagemFiscal(error.message || "Erro ao prevalidar a venda.", "error");
                }
            });
        }
    }

    async function carregarAuxiliaresFiscal() {
        const result = await requestFiscal("/api/fiscal/auxiliares", { method: "GET" });
        fiscalPage.auxiliares = result.data || fiscalPage.auxiliares;
    }

    async function carregarConfiguracaoFiscal(empresaId) {
        const url = new URL("/api/fiscal/configuracao", window.location.origin);
        url.searchParams.set("empresa_id", empresaId);
        const result = await requestFiscal(url.toString(), { method: "GET" });
        fiscalPage.configuracaoAtual = result.data || null;
        preencherFormularioConfiguracao(fiscalPage.configuracaoAtual);
        renderizarStatusConfiguracao(fiscalPage.configuracaoAtual);
    }

    async function carregarNotasFiscais() {
        const result = await requestFiscal("/api/fiscal/notas?limite=20", { method: "GET" });
        fiscalPage.notas = Array.isArray(result.data) ? result.data : [];
        renderizarNotasFiscais();
    }

    async function emitirNotaFiscal(vendaId) {
        if (!vendaId) {
            mostrarMensagemFiscal("Informe a venda que deseja emitir.", "error");
            return;
        }

        try {
            const result = await requestFiscal("/api/fiscal/notas/emitir", {
                method: "POST",
                headers: getFiscalHeaders(true),
                body: JSON.stringify({ venda_id: vendaId })
            });
            await carregarNotasFiscais();
            renderizarResultadoEmissao(result.data || null);
            mostrarMensagemFiscal(result.message || "Nota fiscal emitida com sucesso.");
        } catch (error) {
            mostrarMensagemFiscal(error.message || "Erro ao emitir a nota fiscal.", "error");
        }
    }

    function baixarXmlNota(notaId) {
        if (!notaId) return;
        const url = new URL(`/api/fiscal/notas/${notaId}/xml`, window.location.origin);
        window.open(url.toString(), "_blank", "noopener");
    }

    function popularSelectsFiscal() {
        popularSelect("fiscal-empresa", fiscalPage.auxiliares.empresas, "Selecione a empresa");
        popularSelect("fiscal-ambiente", (fiscalPage.auxiliares.ambientes || []).map((item) => ({ id: item, nome: item })), "Selecione");
        popularSelect("fiscal-regime", (fiscalPage.auxiliares.regimes_tributarios || []).map((item) => ({ id: item, nome: item })), "Selecione");
    }

    function popularSelect(selectId, items, placeholder) {
        const select = document.getElementById(selectId);
        if (!select) return;

        const currentValue = select.value;
        select.innerHTML = `<option value="">${escapeHtml(placeholder || "Selecione")}</option>`;
        (items || []).forEach((item) => {
            select.innerHTML += `<option value="${escapeHtml(item.id)}">${escapeHtml(item.nome)}</option>`;
        });
        if (currentValue) {
            select.value = currentValue;
        }
    }

    function preencherFormularioConfiguracao(configuracao) {
        if (!configuracao) {
            limparFormularioConfiguracao();
            return;
        }

        setValue("fiscal-ambiente", configuracao.ambiente || "HOMOLOGACAO");
        setValue("fiscal-regime", configuracao.regime_tributario || "SIMPLES_NACIONAL");
        setValue("fiscal-serie", configuracao.serie_nfce || 1);
        setValue("fiscal-proximo-numero", configuracao.proximo_numero_nfce || 1);
        setValue("fiscal-ie", configuracao.inscricao_estadual || "");
        setValue("fiscal-im", configuracao.inscricao_municipal || "");
        setValue("fiscal-cnae", configuracao.cnae || "");
        setValue("fiscal-uf", configuracao.uf || "");
        setValue("fiscal-municipio", configuracao.municipio_nome || "");
        setValue("fiscal-municipio-ibge", configuracao.municipio_codigo_ibge || "");
        setValue("fiscal-cep", configuracao.cep || "");
        setValue("fiscal-logradouro", configuracao.logradouro || "");
        setValue("fiscal-numero", configuracao.numero || "");
        setValue("fiscal-bairro", configuracao.bairro || "");
        setValue("fiscal-complemento", configuracao.complemento || "");
        setValue("fiscal-certificado-caminho", configuracao.certificado_caminho || "");
        setValue("fiscal-certificado-env", configuracao.certificado_senha_env || "");
        setValue("fiscal-csc-id", configuracao.csc_id || "");
        setValue("fiscal-csc-token", configuracao.csc_token || "");

        const contingencia = document.getElementById("fiscal-contingencia");
        if (contingencia) {
            contingencia.checked = Boolean(configuracao.contingencia_ativa);
        }
    }

    function limparFormularioConfiguracao() {
        [
            "fiscal-ambiente",
            "fiscal-regime",
            "fiscal-serie",
            "fiscal-proximo-numero",
            "fiscal-ie",
            "fiscal-im",
            "fiscal-cnae",
            "fiscal-uf",
            "fiscal-municipio",
            "fiscal-municipio-ibge",
            "fiscal-cep",
            "fiscal-logradouro",
            "fiscal-numero",
            "fiscal-bairro",
            "fiscal-complemento",
            "fiscal-certificado-caminho",
            "fiscal-certificado-env",
            "fiscal-csc-id",
            "fiscal-csc-token"
        ].forEach((fieldId) => setValue(fieldId, ""));

        const contingencia = document.getElementById("fiscal-contingencia");
        if (contingencia) {
            contingencia.checked = false;
        }
    }

    function montarPayloadConfiguracao() {
        return {
            ambiente: getValue("fiscal-ambiente"),
            regime_tributario: getValue("fiscal-regime"),
            serie_nfce: getValue("fiscal-serie"),
            proximo_numero_nfce: getValue("fiscal-proximo-numero"),
            inscricao_estadual: getValue("fiscal-ie"),
            inscricao_municipal: getValue("fiscal-im"),
            cnae: getValue("fiscal-cnae"),
            uf: getValue("fiscal-uf").toUpperCase(),
            municipio_nome: getValue("fiscal-municipio"),
            municipio_codigo_ibge: onlyDigits(getValue("fiscal-municipio-ibge")),
            cep: onlyDigits(getValue("fiscal-cep")),
            logradouro: getValue("fiscal-logradouro"),
            numero: getValue("fiscal-numero"),
            bairro: getValue("fiscal-bairro"),
            complemento: getValue("fiscal-complemento"),
            certificado_caminho: getValue("fiscal-certificado-caminho"),
            certificado_senha_env: getValue("fiscal-certificado-env").toUpperCase(),
            csc_id: getValue("fiscal-csc-id"),
            csc_token: getValue("fiscal-csc-token"),
            contingencia_ativa: Boolean(document.getElementById("fiscal-contingencia")?.checked)
        };
    }

    function renderizarStatusConfiguracao(configuracao) {
        if (!configuracao) {
            atualizarStatusConfiguracao("Configuracao fiscal ainda nao carregada.");
            return;
        }

        const pendencias = Array.isArray(configuracao.pendencias) ? configuracao.pendencias : [];
        const certificadoStatus = configuracao.certificado_ok
            ? `<span class="text-emerald-300">Certificado pronto</span>`
            : `<span class="text-amber-300">Certificado pendente</span>`;

        atualizarStatusConfiguracao(`
            <div class="space-y-2">
                <div class="flex items-center justify-between gap-3">
                    <span>Empresa</span>
                    <strong class="text-white">${escapeHtml(configuracao.empresa_nome || "-")}</strong>
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span>Ambiente</span>
                    <strong class="text-white">${escapeHtml(configuracao.ambiente || "-")}</strong>
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span>Status do certificado</span>
                    <strong>${certificadoStatus}</strong>
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span>Pronto para emissao</span>
                    <strong class="${configuracao.pronto_para_emissao ? "text-emerald-300" : "text-amber-300"}">
                        ${configuracao.pronto_para_emissao ? "Sim" : "Nao"}
                    </strong>
                </div>
                <div class="text-xs text-slate-400">
                    ${escapeHtml(configuracao.certificado_detalhe || "Sem validacao do certificado.")}
                </div>
                ${pendencias.length ? `
                    <div class="rounded-xl border border-amber-500/20 bg-amber-500/10 px-3 py-3">
                        <p class="text-xs uppercase tracking-[0.14em] text-amber-300 mb-2">Pendencias</p>
                        <ul class="space-y-1 text-sm text-amber-100">
                            ${pendencias.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
                        </ul>
                    </div>
                ` : `
                    <div class="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-3 text-sm text-emerald-100">
                        Base fiscal preenchida e pronta para a proxima etapa de emissao.
                    </div>
                `}
            </div>
        `);
    }

    function renderizarResultadoPrevalidacao(resultado) {
        const container = document.getElementById("fiscal-prevalidacao-resultado");
        if (!container) return;

        if (!resultado) {
            container.textContent = "Nenhuma venda prevalidada nesta sessao.";
            return;
        }

        const pendencias = Array.isArray(resultado.pendencias) ? resultado.pendencias : [];
        container.innerHTML = `
            <div class="space-y-3">
                <div>
                    <p class="text-xs uppercase tracking-[0.14em] text-slate-500">Venda</p>
                    <strong class="block text-white mt-2">${escapeHtml(resultado.venda_numero || `#${resultado.venda_id}`)}</strong>
                </div>
                <div>
                    <p class="text-xs uppercase tracking-[0.14em] text-slate-500">Status</p>
                    <strong class="block mt-2 ${resultado.status === "PRONTA_PARA_EMISSAO" ? "text-emerald-300" : "text-amber-300"}">
                        ${escapeHtml(resultado.status || "-")}
                    </strong>
                </div>
                ${pendencias.length ? `
                    <div class="rounded-xl border border-amber-500/20 bg-amber-500/10 px-3 py-3">
                        <p class="text-xs uppercase tracking-[0.14em] text-amber-300 mb-2">Pendencias</p>
                        <ul class="space-y-1 text-sm text-amber-100">
                            ${pendencias.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
                        </ul>
                    </div>
                ` : `
                    <div class="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-3 text-sm text-emerald-100">
                        Venda pronta para a etapa de emissao fiscal.
                    </div>
                    <button type="button" data-fiscal-emitir-venda="${escapeHtml(resultado.venda_id)}"
                        class="inline-flex items-center justify-center gap-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold px-4 py-3 transition w-full">
                        <i data-lucide="send" class="w-4 h-4"></i>
                        Emitir NFC-e
                    </button>
                `}
            </div>
        `;

        if (window.lucide) {
            lucide.createIcons();
        }
    }

    function renderizarResultadoEmissao(nota) {
        const container = document.getElementById("fiscal-prevalidacao-resultado");
        if (!container || !nota) return;

        container.innerHTML = `
            <div class="space-y-3">
                <div class="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-3 text-sm text-emerald-100">
                    NFC-e emitida internamente e XML gerado.
                </div>
                <div>
                    <p class="text-xs uppercase tracking-[0.14em] text-slate-500">Nota</p>
                    <strong class="block text-white mt-2">Serie ${escapeHtml(nota.serie || "-")} / Numero ${escapeHtml(nota.numero || "-")}</strong>
                </div>
                <div>
                    <p class="text-xs uppercase tracking-[0.14em] text-slate-500">Chave de acesso</p>
                    <p class="break-all text-slate-300 mt-2">${escapeHtml(nota.chave_acesso || "-")}</p>
                </div>
                <button type="button" data-fiscal-baixar-xml="${escapeHtml(nota.id)}"
                    class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-100 font-semibold px-4 py-3 transition w-full">
                    <i data-lucide="download" class="w-4 h-4"></i>
                    Baixar XML
                </button>
            </div>
        `;

        if (window.lucide) {
            lucide.createIcons();
        }
    }

    function renderizarNotasFiscais() {
        const container = document.getElementById("fiscal-notas-lista");
        if (!container) return;

        if (!fiscalPage.notas.length) {
            container.innerHTML = `<p class="text-slate-400">Nenhum registro fiscal encontrado.</p>`;
            return;
        }

        container.innerHTML = fiscalPage.notas.map((nota) => `
            <article class="rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-4">
                <div class="flex items-start justify-between gap-4">
                    <div>
                        <p class="font-semibold text-white">${escapeHtml(nota.venda_numero || `Venda #${nota.venda_id}`)}</p>
                        <p class="text-sm text-slate-400">${escapeHtml(nota.empresa_nome || "-")}</p>
                        ${nota.numero ? `<p class="text-xs text-slate-500 mt-1">Serie ${escapeHtml(nota.serie || "-")} / Numero ${escapeHtml(nota.numero)}</p>` : ""}
                    </div>
                    <span class="text-xs uppercase tracking-[0.14em] ${nota.status === "PRONTA_PARA_EMISSAO" ? "text-emerald-300" : "text-amber-300"}">
                        ${escapeHtml(nota.status || "-")}
                    </span>
                </div>
                ${nota.chave_acesso ? `<p class="text-xs text-slate-500 mt-3 break-all">${escapeHtml(nota.chave_acesso)}</p>` : ""}
                <p class="text-xs text-slate-500 mt-3">${escapeHtml(nota.mensagem_retorno || "Sem retorno de validacao.")}</p>
                <div class="flex flex-col sm:flex-row gap-2 mt-4">
                    ${nota.status !== "EMITIDA" ? `
                        <button type="button" data-fiscal-emitir-venda="${escapeHtml(nota.venda_id)}"
                            class="inline-flex items-center justify-center gap-2 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-200 hover:bg-sky-500/20 font-semibold px-3 py-2 transition">
                            <i data-lucide="send" class="w-4 h-4"></i>
                            Emitir
                        </button>
                    ` : ""}
                    ${nota.xml_disponivel ? `
                        <button type="button" data-fiscal-baixar-xml="${escapeHtml(nota.id)}"
                            class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 hover:border-sky-500/30 px-3 py-2 transition">
                            <i data-lucide="download" class="w-4 h-4"></i>
                            XML
                        </button>
                    ` : ""}
                </div>
            </article>
        `).join("");

        if (window.lucide) {
            lucide.createIcons();
        }
    }

    function atualizarStatusConfiguracao(html) {
        const status = document.getElementById("fiscal-config-status");
        if (!status) return;
        status.innerHTML = html;
    }

    function mostrarMensagemFiscal(message, type = "success") {
        const old = document.getElementById("fiscal-message");
        if (old) old.remove();

        const div = document.createElement("div");
        div.id = "fiscal-message";
        div.className = `
            fixed top-4 right-4 z-[9999] px-4 py-3 rounded-xl shadow-lg text-sm font-medium
            ${type === "success" ? "bg-emerald-500 text-white" : "bg-rose-500 text-white"}
        `;
        div.textContent = message;
        document.body.appendChild(div);

        setTimeout(() => div.remove(), 3500);
    }

    function requestFiscal(url, options = {}) {
        return fetch(url, {
            credentials: "same-origin",
            ...options,
            headers: {
                ...getFiscalHeaders(false),
                ...(options.headers || {})
            }
        }).then(async (response) => {
            let result;
            try {
                result = await response.json();
            } catch (_error) {
                result = { success: false, message: "Resposta invalida do servidor." };
            }

            if (!response.ok || result.success === false) {
                throw new Error(result.message || "Erro na requisicao.");
            }

            return result;
        });
    }

    function getFiscalHeaders(isJson = false) {
        const token = localStorage.getItem("token");
        const headers = {};
        if (isJson) {
            headers["Content-Type"] = "application/json";
        }
        if (token) {
            headers.Authorization = `Bearer ${token}`;
        }
        return headers;
    }

    function setValue(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.value = value ?? "";
        }
    }

    function getValue(id) {
        return (document.getElementById(id)?.value || "").trim();
    }

    function onlyDigits(value) {
        return String(value || "").replace(/\D/g, "");
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
})();
