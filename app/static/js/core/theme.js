(function () {
    const config = window.__tenantThemeConfig || {};
    const defaultMode = config.defaultMode === "classic" ? "classic" : "modern";
    const companyModes = config.companyModes || {};
    const storageKey = config.storageKey || "oceanblue:empresa-visual-selecionada";

    function normalizeMode(mode) {
        return mode === "classic" ? "classic" : "modern";
    }

    function applyMode(mode) {
        if (!document.body) {
            return;
        }

        document.body.setAttribute("data-theme-mode", normalizeMode(mode));
    }

    function getModeForCompany(companyId) {
        return companyModes[String(companyId)] || null;
    }

    function applyCompany(companyId, persist = true) {
        const normalizedCompanyId = String(companyId || "").trim();

        if (!normalizedCompanyId) {
            if (persist) {
                window.localStorage.removeItem(storageKey);
            }
            applyMode(defaultMode);
            return defaultMode;
        }

        const mode = getModeForCompany(normalizedCompanyId) || defaultMode;
        if (persist) {
            window.localStorage.setItem(storageKey, normalizedCompanyId);
        }
        applyMode(mode);
        return mode;
    }

    function bindCompanySelect(select) {
        if (!select || select.dataset.themeBound === "true") {
            return;
        }

        select.dataset.themeBound = "true";

        const syncSelectTheme = (persist) => {
            const companyId = select.value || "";
            if (companyId) {
                applyCompany(companyId, persist);
                return;
            }

            if (persist) {
                applyCompany("", true);
                return;
            }

            applyMode(defaultMode);
        };

        select.addEventListener("change", () => {
            syncSelectTheme(true);
        });

        if (select.value) {
            syncSelectTheme(false);
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        const storedCompanyId = window.localStorage.getItem(storageKey);
        if (storedCompanyId && getModeForCompany(storedCompanyId)) {
            applyCompany(storedCompanyId, false);
        } else {
            applyMode(defaultMode);
        }

        document.querySelectorAll("[data-theme-company-select]").forEach(bindCompanySelect);
    });

    window.OceanBlueTheme = {
        applyMode,
        applyCompany,
        bindCompanySelect
    };
})();
