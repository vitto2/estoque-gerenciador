(function () {
    "use strict";
    if (typeof window.gsap === "undefined") return;

    document.addEventListener("DOMContentLoaded", function () {
        var tl = gsap.timeline({ defaults: { ease: "power3.out" } });
        var ultimaPosicao = 0;

        function encadeia(alvo, vars, sobreposicao) {
            var elementos = typeof alvo === "string" ? gsap.utils.toArray(alvo) : alvo;
            if (!elementos || !elementos.length) return;
            tl.from(elementos, vars, ultimaPosicao !== 0 ? "-=" + sobreposicao : 0);
            ultimaPosicao = 1;
        }

        encadeia(".page-header", { opacity: 0, y: -14, duration: 0.4 }, 0);
        encadeia(".alerta-banco", { opacity: 0, y: -10, duration: 0.35 }, 0.2);
        encadeia(".modo-cadastro-tabs", { opacity: 0, y: -10, duration: 0.3 }, 0.2);
        encadeia(".filtros", { opacity: 0, y: 14, duration: 0.4 }, 0.15);
        encadeia(".form-card .campo", { opacity: 0, y: 12, duration: 0.35, stagger: { amount: 0.35 } }, 0.15);
        encadeia(".lote-card", { opacity: 0, y: 16, duration: 0.4, stagger: 0.08 }, 0.15);
        encadeia(".resultado-resumo .resultado-card", { opacity: 0, y: 16, duration: 0.4, stagger: 0.08 }, 0.15);
        encadeia(".tabela-estoque tbody tr", { opacity: 0, y: 8, duration: 0.35, stagger: { amount: 0.35 } }, 0.15);
        encadeia(".estado-vazio", { opacity: 0, y: 12, scale: 0.98, duration: 0.4 }, 0.1);
        encadeia(".form-acoes, .paginacao", { opacity: 0, y: 10, duration: 0.3 }, 0.15);

        // Contador nos números de resultado da saída em lote — mesma lógica do painel.
        document.querySelectorAll(".resultado-numero").forEach(function (el) {
            var destino = parseInt(el.textContent.replace(/\D/g, ""), 10);
            if (isNaN(destino)) return;
            var contador = { valor: 0 };
            el.textContent = "0";
            gsap.to(contador, {
                valor: destino,
                duration: 0.8,
                delay: 0.35,
                ease: "power2.out",
                onUpdate: function () { el.textContent = Math.round(contador.valor); },
            });
        });
    });
})();
