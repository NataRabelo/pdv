(function initInputMaskToolkit(global) {
    function onlyDigits(value) {
        return String(value ?? "").replace(/\D/g, "");
    }

    function formatCpf(value) {
        const digits = onlyDigits(value).slice(0, 11);
        if (!digits) return "";
        if (digits.length <= 3) return digits;
        if (digits.length <= 6) return digits.replace(/^(\d{3})(\d{0,3})$/, "$1.$2");
        if (digits.length <= 9) return digits.replace(/^(\d{3})(\d{3})(\d{0,3})$/, "$1.$2.$3");
        return digits.replace(/^(\d{3})(\d{3})(\d{3})(\d{0,2})$/, "$1.$2.$3-$4");
    }

    function formatCnpj(value) {
        const digits = onlyDigits(value).slice(0, 14);
        if (!digits) return "";
        if (digits.length <= 2) return digits;
        if (digits.length <= 5) return digits.replace(/^(\d{2})(\d{0,3})$/, "$1.$2");
        if (digits.length <= 8) return digits.replace(/^(\d{2})(\d{3})(\d{0,3})$/, "$1.$2.$3");
        if (digits.length <= 12) return digits.replace(/^(\d{2})(\d{3})(\d{3})(\d{0,4})$/, "$1.$2.$3/$4");
        return digits.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{0,2})$/, "$1.$2.$3/$4-$5");
    }

    function formatDocument(value) {
        const digits = onlyDigits(value);
        if (!digits) return "";
        return digits.length > 11 ? formatCnpj(digits) : formatCpf(digits);
    }

    function formatPhone(value) {
        const raw = String(value ?? "").trim();
        if (!raw) return "";

        const digits = onlyDigits(raw);
        if (!digits) return "";

        const hasCountryCode = digits.length > 11;
        const localDigits = hasCountryCode ? digits.slice(-11) : digits;
        const countryCode = hasCountryCode ? digits.slice(0, digits.length - localDigits.length) : "";
        const areaCode = localDigits.slice(0, 2);
        const number = localDigits.slice(2);

        let formattedNumber = number;
        if (number.length > 5) {
            formattedNumber = `${number.slice(0, number.length === 8 ? 4 : 5)}-${number.slice(number.length === 8 ? 4 : 5)}`;
        }

        let formatted = areaCode ? `(${areaCode}) ${formattedNumber}` : formattedNumber;
        if (countryCode) {
            formatted = `+${countryCode} ${formatted}`;
        }
        return formatted.trim();
    }

    function formatByType(type, value) {
        switch (type) {
            case "cpf":
                return formatCpf(value);
            case "cnpj":
                return formatCnpj(value);
            case "document":
                return formatDocument(value);
            case "phone":
                return formatPhone(value);
            default:
                return String(value ?? "");
        }
    }

    function bind(input, explicitType) {
        if (!input) return;

        const maskType = explicitType || input.dataset.mask || "";
        if (!maskType) return;

        input.dataset.mask = maskType;
        if (input.dataset.inputMaskBound === "true") {
            refresh(input);
            return;
        }

        input.dataset.inputMaskBound = "true";
        input.setAttribute("inputmode", maskType === "phone" ? "tel" : "numeric");

        const applyMask = () => {
            input.value = formatByType(maskType, input.value);
        };

        applyMask();
        input.addEventListener("input", applyMask);
        input.addEventListener("blur", applyMask);
    }

    function bindAll(root = document) {
        if (!root?.querySelectorAll) return;
        root.querySelectorAll("[data-mask]").forEach((input) => bind(input));
    }

    function refresh(input) {
        if (!input) return;
        const maskType = input.dataset.mask || "";
        if (!maskType) return;
        input.value = formatByType(maskType, input.value);
    }

    global.InputMask = {
        bind,
        bindAll,
        refresh,
        digits: onlyDigits,
        formatCpf,
        formatCnpj,
        formatDocument,
        formatPhone,
    };

    document.addEventListener("DOMContentLoaded", () => bindAll(document));
})(window);
