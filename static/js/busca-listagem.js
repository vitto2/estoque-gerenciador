(function () {
    "use strict";

    var form = document.getElementById("filtros-form");
    var campoBusca = document.getElementById("busca");
    var conteudo = document.getElementById("conteudo-listagem");
    if (!form || !campoBusca || !conteudo) return;

    var urlFragmento = form.dataset.fragmentoUrl;
    var urlListagem = form.dataset.listagemUrl;
    var controladorAtual = null;
    var debounceId = null;

    function parametrosAtuais() {
        var params = new URLSearchParams();
        var busca = campoBusca.value.trim();
        var categoria = document.getElementById("categoria").value;
        var status = document.getElementById("status").value;
        var tecnico = document.getElementById("tecnico").value;
        if (busca) params.set("busca", busca);
        if (categoria) params.set("categoria", categoria);
        if (status) params.set("status", status);
        if (tecnico) params.set("tecnico", tecnico);
        return params;
    }

    function atualizar(params, modoHistorico) {
        if (controladorAtual) controladorAtual.abort();
        controladorAtual = new AbortController();

        var queryString = params.toString();
        conteudo.classList.add("carregando");

        fetch(urlFragmento + (queryString ? "?" + queryString : ""), { signal: controladorAtual.signal })
            .then(function (resposta) { return resposta.text(); })
            .then(function (html) {
                conteudo.innerHTML = html;
                conteudo.classList.remove("carregando");
                var novaUrl = urlListagem + (queryString ? "?" + queryString : "");
                if (modoHistorico === "push") {
                    history.pushState(null, "", novaUrl);
                } else {
                    history.replaceState(null, "", novaUrl);
                }
            })
            .catch(function (erro) {
                if (erro.name === "AbortError") return;
                conteudo.classList.remove("carregando");
                throw erro;
            });
    }

    campoBusca.addEventListener("input", function () {
        clearTimeout(debounceId);
        debounceId = setTimeout(function () {
            atualizar(parametrosAtuais(), "replace");
        }, 300);
    });

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        clearTimeout(debounceId);
        atualizar(parametrosAtuais(), "push");
        // No mobile o formulário é um bottom sheet — fechar depois de
        // "Filtrar" pra revelar o resultado que acabou de chegar.
        var backdrop = document.getElementById("filtros-backdrop");
        form.classList.remove("aberta");
        if (backdrop) backdrop.classList.remove("aberta");
        document.body.style.overflow = "";
    });

    window.addEventListener("popstate", function () {
        var params = new URLSearchParams(window.location.search);
        campoBusca.value = params.get("busca") || "";
        document.getElementById("categoria").value = params.get("categoria") || "";
        document.getElementById("status").value = params.get("status") || "";
        document.getElementById("tecnico").value = params.get("tecnico") || "";
        atualizar(params, "replace");
    });
})();
