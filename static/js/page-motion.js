(function () {
    "use strict";
    if (typeof window.gsap === "undefined") return;
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    document.addEventListener("DOMContentLoaded", function () {
        // Entrada única e rápida do cabeçalho — sem cascata item a item,
        // que atrasaria a leitura de listagens e formulários longos.
        var header = document.querySelector(".page-header");
        if (header) gsap.from(header, { opacity: 0, y: -10, duration: 0.3, ease: "power2.out" });

        var alertaBanco = document.querySelector(".alerta-banco");
        if (alertaBanco) gsap.from(alertaBanco, { opacity: 0, y: -8, duration: 0.3 });
    });
})();
