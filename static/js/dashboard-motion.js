(function () {
    "use strict";
    if (typeof window.gsap === "undefined") return;
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    // Números aparecem no valor final direto — nada de contar do zero
    // toda vez que o usuário volta à tela. Só uma entrada rápida e única
    // do painel, sem atraso em cascata sobre cada gráfico.
    document.addEventListener("DOMContentLoaded", function () {
        var situacao = document.querySelector(".situacao-estoque");
        if (situacao) gsap.from(situacao, { opacity: 0, y: -10, duration: 0.35, ease: "power2.out" });
    });
})();
