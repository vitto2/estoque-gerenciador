(function () {
    "use strict";

    var overlay = document.getElementById("exclusao-overlay");
    if (!overlay) return;

    var modal = overlay.querySelector(".exclusao-modal");
    var form = document.getElementById("form-exclusao-modal");
    var campoSenha = document.getElementById("exclusao-senha");
    var erro = document.getElementById("exclusao-erro");
    var reduzido = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var temGsap = typeof window.gsap !== "undefined" && !reduzido;

    function abrir(botao) {
        form.action = botao.dataset.action;
        document.getElementById("exclusao-categoria").textContent = botao.dataset.categoria || "";
        document.getElementById("exclusao-titulo-equip").textContent =
            (botao.dataset.fabricante || "") + " " + (botao.dataset.modelo || "");

        var serialEl = document.getElementById("exclusao-serial");
        if (botao.dataset.serial) {
            serialEl.textContent = botao.dataset.serial;
            serialEl.style.display = "";
        } else {
            serialEl.textContent = "sem serial";
            serialEl.style.display = "";
        }

        var statusEl = document.getElementById("exclusao-status");
        statusEl.textContent = botao.dataset.status || "";
        statusEl.className = "status-badge status-" + (botao.dataset.statusSlug || "");

        var localEl = document.getElementById("exclusao-local");
        localEl.textContent = botao.dataset.local ? botao.dataset.local : "";
        localEl.style.display = botao.dataset.local ? "" : "none";

        campoSenha.value = "";
        erro.style.display = "none";

        overlay.classList.add("aberto");
        overlay.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
        if (temGsap) {
            gsap.fromTo(overlay, { opacity: 0 }, { opacity: 1, duration: 0.2 });
            gsap.fromTo(modal, { opacity: 0, y: 16, scale: 0.97 }, { opacity: 1, y: 0, scale: 1, duration: 0.3, ease: "power3.out" });
        }
        setTimeout(function () { campoSenha.focus(); }, 50);
    }

    function fechar() {
        overlay.classList.remove("aberto");
        overlay.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
    }

    document.addEventListener("click", function (e) {
        var botao = e.target.closest(".btn-abrir-exclusao");
        if (botao) abrir(botao);
    });

    document.getElementById("exclusao-cancelar").addEventListener("click", fechar);
    overlay.addEventListener("click", function (e) { if (e.target === overlay) fechar(); });
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && overlay.classList.contains("aberto")) fechar();
    });

    form.addEventListener("submit", function (e) {
        if (!campoSenha.value.trim()) {
            e.preventDefault();
            erro.style.display = "block";
            campoSenha.focus();
        }
    });
})();
