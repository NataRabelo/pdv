document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("userMenuBtn");
    const dropdown = document.getElementById("userDropdown");
    const backButton = document.querySelector("[data-back-button]");

    if (btn && dropdown) {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            dropdown.classList.toggle("hidden");
        });

        document.addEventListener("click", (e) => {
            if (!dropdown.contains(e.target) && !btn.contains(e.target)) {
                dropdown.classList.add("hidden");
            }
        });
    }

    if (backButton) {
        backButton.addEventListener("click", () => {
            const sameOriginReferrer = document.referrer && document.referrer.startsWith(window.location.origin);

            if (window.history.length > 1 && sameOriginReferrer) {
                window.history.back();
                return;
            }

            window.location.href = "/home";
        });
    }
});
