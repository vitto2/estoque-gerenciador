(function () {
    "use strict";
    if (typeof window.gsap === "undefined") return;

    if (typeof window.ScrollTrigger !== "undefined") {
        gsap.registerPlugin(ScrollTrigger);
    }

    document.addEventListener("DOMContentLoaded", function () {
        var hero = document.querySelector(".painel-hero");
        if (hero) gsap.from(hero, { opacity: 0, y: -16, duration: 0.6, ease: "power3.out" });

        var cards = gsap.utils.toArray(".card-resumo");
        if (cards.length) {
            gsap.from(cards, { opacity: 0, y: 22, duration: 0.55, stagger: 0.09, delay: 0.15, ease: "power3.out" });
        }

        // Contador: sobe de 0 até o valor real já renderizado no HTML
        // (progressive enhancement — sem JS, o número correto continua visível).
        document.querySelectorAll(".card-resumo-valor").forEach(function (el) {
            var destino = parseInt(el.textContent.replace(/\D/g, ""), 10);
            if (isNaN(destino)) return;
            var contador = { valor: 0 };
            el.textContent = "0";
            gsap.to(contador, {
                valor: destino,
                duration: 1.1,
                delay: 0.3,
                ease: "power2.out",
                onUpdate: function () { el.textContent = Math.round(contador.valor); },
            });
        });

        var graficos = gsap.utils.toArray(".card-grafico");
        if (graficos.length && typeof window.ScrollTrigger !== "undefined") {
            graficos.forEach(function (card, i) {
                gsap.from(card, {
                    opacity: 0,
                    y: 30,
                    duration: 0.6,
                    ease: "power3.out",
                    delay: (i % 2) * 0.08,
                    scrollTrigger: { trigger: card, start: "top 88%" },
                });
            });
        }
    });
})();
