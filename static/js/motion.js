(function () {
    "use strict";
    if (typeof window.gsap === "undefined") return;

    document.addEventListener("DOMContentLoaded", function () {
        var tl = gsap.timeline({ defaults: { ease: "power3.out" } });

        tl.from(".brand-mark", { opacity: 0, scale: 0.5, rotate: -20, duration: 0.45, ease: "back.out(1.8)" })
          .from(".brand-copy", { opacity: 0, x: -10, duration: 0.3 }, "-=0.3")
          .from(".btn-ajuda", { opacity: 0, y: -6, duration: 0.25 }, "-=0.2")
          .from(".nav-desktop a", { opacity: 0, y: -8, stagger: 0.04, duration: 0.25 }, "-=0.15");

        var alerta = document.querySelector(".alerta-banco");
        if (alerta) gsap.from(alerta, { opacity: 0, y: -12, duration: 0.4, delay: 0.1 });
    });
})();
