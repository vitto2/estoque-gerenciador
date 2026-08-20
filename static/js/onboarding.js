(function () {
    "use strict";

    var STORAGE_KEY = "estoqueTiOnboardingVistoV1";

    var overlay = document.getElementById("onboarding-overlay");
    if (!overlay) return;

    var modal = overlay.querySelector(".onboarding-modal");
    var slides = Array.prototype.slice.call(overlay.querySelectorAll(".onboarding-slide"));
    var dots = Array.prototype.slice.call(overlay.querySelectorAll(".onboarding-dot"));
    var btnProximo = document.getElementById("onboarding-proximo");
    var btnPular = document.getElementById("onboarding-pular");
    var btnFechar = document.getElementById("onboarding-fechar");
    var btnReabrir = document.getElementById("btn-reabrir-onboarding");

    var indiceAtual = 0;
    var temGsap = typeof window.gsap !== "undefined";

    function animarSlideAtual() {
        var ativo = slides[indiceAtual];
        if (temGsap) {
            gsap.fromTo(ativo, { opacity: 0, x: 24 }, { opacity: 1, x: 0, duration: 0.45, ease: "power2.out" });
        }
    }

    function irParaSlide(indice) {
        indiceAtual = indice;
        slides.forEach(function (el, i) {
            el.classList.toggle("onboarding-slide-ativo", i === indice);
        });
        dots.forEach(function (el, i) {
            el.classList.toggle("onboarding-dot-ativo", i === indice);
        });
        btnProximo.textContent = indice === slides.length - 1 ? "Começar a usar" : "Próximo";
        animarSlideAtual();
    }

    function abrirModal() {
        irParaSlide(0);
        overlay.classList.add("aberto");
        overlay.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
        if (temGsap) {
            gsap.fromTo(overlay, { opacity: 0 }, { opacity: 1, duration: 0.35 });
            gsap.fromTo(modal, { opacity: 0, y: 24, scale: 0.96 }, { opacity: 1, y: 0, scale: 1, duration: 0.5, ease: "back.out(1.6)" });
        }
    }

    function fecharModal(marcarComoVisto) {
        function limpar() {
            overlay.classList.remove("aberto");
            overlay.setAttribute("aria-hidden", "true");
            document.body.style.overflow = "";
        }
        if (temGsap) {
            gsap.to(overlay, { opacity: 0, duration: 0.25, onComplete: limpar });
        } else {
            limpar();
        }
        if (marcarComoVisto) {
            try { localStorage.setItem(STORAGE_KEY, "1"); } catch (e) { /* localStorage indisponível — não bloqueia o fechamento */ }
        }
    }

    btnProximo.addEventListener("click", function () {
        if (indiceAtual < slides.length - 1) irParaSlide(indiceAtual + 1);
        else fecharModal(true);
    });
    btnPular.addEventListener("click", function () { fecharModal(true); });
    btnFechar.addEventListener("click", function () { fecharModal(true); });
    overlay.addEventListener("click", function (e) { if (e.target === overlay) fecharModal(true); });
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && overlay.classList.contains("aberto")) fecharModal(true);
    });
    dots.forEach(function (dot, i) {
        dot.addEventListener("click", function () { irParaSlide(i); });
    });
    if (btnReabrir) {
        btnReabrir.addEventListener("click", function () { abrirModal(); });
    }

    var jaViu = false;
    try { jaViu = !!localStorage.getItem(STORAGE_KEY); } catch (e) { /* trata como não visto */ }
    if (!jaViu) {
        setTimeout(abrirModal, 500);
    }
})();
