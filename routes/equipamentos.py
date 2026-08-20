from datetime import datetime

from flask import (
    Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_file, session, url_for,
)

from exportacao import gerar_planilha_equipamentos
from extracao_serial import ExtracaoFalhou, ExtracaoIndisponivel, extrair_serial_da_imagem
from models import (
    CATEGORIAS, CATEGORIAS_COM_SERIAL_OBRIGATORIO, LOCAIS_ARMAZENAMENTO, STATUS_ARTURITO_OPCOES,
    STATUS_OPCOES, Equipamento, db, status_slug,
)

equipamentos_bp = Blueprint("equipamentos", __name__, url_prefix="/equipamentos")

ITENS_POR_PAGINA = 30


def get_categorias_disponiveis():
    """CATEGORIAS fixas + qualquer categoria customizada ('Outro') já cadastrada."""
    existentes = [row[0] for row in db.session.query(Equipamento.categoria).distinct().all()]
    extras = sorted(c for c in existentes if c and c not in CATEGORIAS)
    return CATEGORIAS + extras


def get_tecnicos_existentes():
    """Técnicos já usados em algum cadastro — alimenta o filtro e o autocomplete do form."""
    linhas = (
        db.session.query(Equipamento.tecnico_responsavel)
        .distinct()
        .order_by(Equipamento.tecnico_responsavel)
        .all()
    )
    return [row[0] for row in linhas if row[0]]


def _valores_iniciais(equipamento=None, form_data=None):
    """Monta o dicionário usado para preencher o formulário: dá prioridade ao que
    veio do POST (em caso de erro de validação), depois ao registro existente
    (modo edição), e por último aos valores em branco (modo cadastro)."""
    if form_data is not None:
        return {
            "fabricante": form_data.get("fabricante", ""),
            "modelo": form_data.get("modelo", ""),
            "categoria": form_data.get("categoria", ""),
            "categoria_customizada": form_data.get("categoria_customizada", ""),
            "quantidade": form_data.get("quantidade", ""),
            "serial": form_data.get("serial", ""),
            "tecnico_responsavel": form_data.get("tecnico_responsavel", ""),
            "status": form_data.get("status", "Disponível"),
            "local_armazenamento": form_data.get("local_armazenamento", ""),
            "observacoes": form_data.get("observacoes", ""),
            "status_arturito": form_data.get("status_arturito", ""),
        }
    if equipamento is not None:
        return {
            "fabricante": equipamento.fabricante,
            "modelo": equipamento.modelo,
            "categoria": equipamento.categoria,
            "categoria_customizada": "",
            "quantidade": equipamento.quantidade,
            "serial": equipamento.serial or "",
            "tecnico_responsavel": equipamento.tecnico_responsavel,
            "status": equipamento.status,
            "local_armazenamento": equipamento.local_armazenamento or "",
            "observacoes": equipamento.observacoes or "",
            "status_arturito": equipamento.status_arturito or "",
        }
    return {
        "fabricante": "",
        "modelo": "",
        "categoria": "",
        "categoria_customizada": "",
        "quantidade": 1,
        "serial": "",
        "tecnico_responsavel": "",
        "status": "Disponível",
        "local_armazenamento": "",
        "observacoes": "",
        "status_arturito": "",
    }


def _validar_dados(form, item_id=None):
    """Valida os campos do formulário. Retorna (dados_prontos_pra_salvar, lista_de_erros).
    `item_id` é o id do equipamento em edição (None em cadastros novos), usado para
    não comparar o serial contra o próprio registro na checagem de duplicidade."""
    erros = []
    duplicado_id = None

    fabricante = (form.get("fabricante") or "").strip()
    if not fabricante:
        erros.append("Informe o fabricante do equipamento.")

    modelo = (form.get("modelo") or "").strip()
    if not modelo:
        erros.append("Informe o modelo do equipamento.")

    categoria = (form.get("categoria") or "").strip()
    if categoria == "Outro":
        categoria = (form.get("categoria_customizada") or "").strip()
    if not categoria:
        erros.append("Informe a categoria do equipamento.")

    quantidade = None
    quantidade_raw = (form.get("quantidade") or "").strip()
    try:
        quantidade = int(quantidade_raw)
        if quantidade < 1:
            raise ValueError
    except (TypeError, ValueError):
        erros.append("Quantidade deve ser um número inteiro maior que zero.")

    serial = (form.get("serial") or "").strip() or None
    if not serial and categoria in CATEGORIAS_COM_SERIAL_OBRIGATORIO:
        erros.append(f'Informe o número de série — obrigatório para a categoria "{categoria}".')
    if serial:
        duplicado = Equipamento.query.filter(db.func.lower(Equipamento.serial) == serial.lower())
        if item_id is not None:
            duplicado = duplicado.filter(Equipamento.id != item_id)
        existente = duplicado.first()
        if existente:
            duplicado_id = existente.id
            erros.append(f'Já existe um equipamento cadastrado com o serial "{serial}".')

    tecnico = (form.get("tecnico_responsavel") or "").strip()
    if not tecnico:
        erros.append("Informe o técnico responsável.")

    status = (form.get("status") or "").strip()
    if status not in STATUS_OPCOES:
        erros.append("Selecione um status válido.")

    local = (form.get("local_armazenamento") or "").strip() or None
    if local and local not in LOCAIS_ARMAZENAMENTO:
        erros.append("Selecione um local de armazenamento válido.")

    observacoes = (form.get("observacoes") or "").strip() or None

    status_arturito = (form.get("status_arturito") or "").strip() or None
    if status_arturito and status_arturito not in STATUS_ARTURITO_OPCOES:
        erros.append("Selecione um status do Arturito válido.")

    dados = {
        "fabricante": fabricante,
        "modelo": modelo,
        "categoria": categoria,
        "quantidade": quantidade,
        "serial": serial,
        "tecnico_responsavel": tecnico,
        "status": status,
        "local_armazenamento": local,
        "observacoes": observacoes,
        "status_arturito": status_arturito,
    }
    return dados, erros, duplicado_id


def _contexto_form(equipamento=None, form_data=None, serial_duplicado_id=None):
    return {
        "equipamento": equipamento,
        "valores": _valores_iniciais(equipamento=equipamento, form_data=form_data),
        "categorias": get_categorias_disponiveis() + ["Outro"],
        "status_opcoes": STATUS_OPCOES,
        "locais_armazenamento": LOCAIS_ARMAZENAMENTO,
        "status_arturito_opcoes": STATUS_ARTURITO_OPCOES,
        "categorias_serial_obrigatorio": CATEGORIAS_COM_SERIAL_OBRIGATORIO,
        "tecnicos_existentes": get_tecnicos_existentes(),
        "serial_duplicado_id": serial_duplicado_id,
    }


def _filtros_atuais():
    return {
        "categoria": request.args.get("categoria", "").strip(),
        "status": request.args.get("status", "").strip(),
        "tecnico": request.args.get("tecnico", "").strip(),
        "fabricante": request.args.get("fabricante", "").strip(),
        "modelo": request.args.get("modelo", "").strip(),
        "busca": request.args.get("busca", "").strip(),
    }


def _aplicar_filtros(query, filtros):
    if filtros["categoria"]:
        query = query.filter(Equipamento.categoria == filtros["categoria"])
    if filtros["status"]:
        query = query.filter(Equipamento.status == filtros["status"])
    if filtros["tecnico"]:
        query = query.filter(Equipamento.tecnico_responsavel == filtros["tecnico"])
    if filtros.get("fabricante"):
        query = query.filter(Equipamento.fabricante == filtros["fabricante"])
    if filtros.get("modelo"):
        query = query.filter(Equipamento.modelo == filtros["modelo"])
    if filtros.get("busca"):
        query = query.filter(Equipamento.serial.ilike(f"%{filtros['busca']}%"))
    return query


def _contexto_lote(form_data=None, seriais=None, serial_problemas=None):
    fd = form_data or {}
    return {
        "serial_problemas": serial_problemas or [],
        "valores": {
            "fabricante": fd.get("fabricante", ""),
            "modelo": fd.get("modelo", ""),
            "categoria": fd.get("categoria", ""),
            "categoria_customizada": fd.get("categoria_customizada", ""),
            "tecnico_responsavel": fd.get("tecnico_responsavel", ""),
            "status": fd.get("status", "Disponível"),
            "local_armazenamento": fd.get("local_armazenamento", ""),
            "observacoes": fd.get("observacoes", ""),
            "status_arturito": fd.get("status_arturito", ""),
        },
        "seriais": seriais if seriais is not None else [""],
        "categorias": get_categorias_disponiveis() + ["Outro"],
        "status_opcoes": STATUS_OPCOES,
        "locais_armazenamento": LOCAIS_ARMAZENAMENTO,
        "status_arturito_opcoes": STATUS_ARTURITO_OPCOES,
        "tecnicos_existentes": get_tecnicos_existentes(),
    }


@equipamentos_bp.route("/extrair-serial", methods=["POST"])
def extrair_serial():
    foto = request.files.get("foto")
    if not foto or not foto.mimetype or not foto.mimetype.startswith("image/"):
        return jsonify({"erro": "Envie uma imagem válida."}), 400

    conteudo = foto.read()

    try:
        serial = extrair_serial_da_imagem(
            conteudo,
            foto.mimetype,
            current_app.config.get("GEMINI_API_KEY"),
            current_app.config.get("GEMINI_VISION_MODEL"),
        )
    except ExtracaoIndisponivel as erro:
        return jsonify({"erro": str(erro)}), 503
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except ExtracaoFalhou as erro:
        return jsonify({"erro": str(erro)}), 502

    if not serial:
        return jsonify({"serial": None, "mensagem": "Não encontrei um número de série legível nessa foto."})

    return jsonify({"serial": serial})


@equipamentos_bp.route("/lote", methods=["GET", "POST"])
def lote():
    if request.method == "POST":
        fabricante = (request.form.get("fabricante") or "").strip()
        modelo = (request.form.get("modelo") or "").strip()
        categoria = (request.form.get("categoria") or "").strip()
        if categoria == "Outro":
            categoria = (request.form.get("categoria_customizada") or "").strip()
        tecnico = (request.form.get("tecnico_responsavel") or "").strip()
        status = (request.form.get("status") or "").strip()
        seriais_raw = request.form.getlist("serial")

        local = (request.form.get("local_armazenamento") or "").strip() or None
        observacoes = (request.form.get("observacoes") or "").strip() or None
        status_arturito = (request.form.get("status_arturito") or "").strip() or None

        erros = []
        if not fabricante:
            erros.append("Informe o fabricante do equipamento.")
        if not modelo:
            erros.append("Informe o modelo do equipamento.")
        if not categoria:
            erros.append("Informe a categoria.")
        if not tecnico:
            erros.append("Informe o técnico responsável.")
        if status not in STATUS_OPCOES:
            erros.append("Selecione um status válido.")
        if local and local not in LOCAIS_ARMAZENAMENTO:
            erros.append("Selecione um local de armazenamento válido.")
        if status_arturito and status_arturito not in STATUS_ARTURITO_OPCOES:
            erros.append("Selecione um status do Arturito válido.")

        seriais = [s.strip() for s in seriais_raw if s.strip()]
        if not seriais:
            erros.append("Adicione pelo menos um número de série.")

        # Linhas problemáticas (chave em minúsculo) — usado só para destacar
        # visualmente a linha certa na tabela, não muda a regra de validação.
        linhas_com_erro = set()

        contagem = {}
        for s in seriais:
            chave = s.lower()
            contagem[chave] = contagem.get(chave, 0) + 1
        duplicados_no_lote = {chave for chave, n in contagem.items() if n > 1}
        if duplicados_no_lote:
            linhas_com_erro |= duplicados_no_lote
            nomes = sorted({s for s in seriais if s.lower() in duplicados_no_lote})
            erros.append(f"Seriais repetidos nesta lista: {', '.join(nomes)}.")

        if seriais and not duplicados_no_lote:
            ja_cadastrados = (
                Equipamento.query
                .filter(db.func.lower(Equipamento.serial).in_([s.lower() for s in seriais]))
                .all()
            )
            if ja_cadastrados:
                chaves_existentes = {e.serial.lower() for e in ja_cadastrados}
                linhas_com_erro |= chaves_existentes
                nomes = sorted({e.serial for e in ja_cadastrados})
                erros.append(f"Seriais já cadastrados no estoque: {', '.join(nomes)}.")

        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("lote.html", **_contexto_lote(
                form_data=request.form, seriais=seriais_raw, serial_problemas=list(linhas_com_erro),
            ))

        itens_criados = []
        for serial in seriais:
            item = Equipamento(
                fabricante=fabricante,
                modelo=modelo,
                categoria=categoria,
                quantidade=1,
                serial=serial,
                local_armazenamento=local,
                observacoes=observacoes,
                status_arturito=status_arturito,
                tecnico_responsavel=tecnico,
                status=status,
            )
            db.session.add(item)
            itens_criados.append(item)
        db.session.commit()
        session["ultimo_cadastro_id"] = itens_criados[-1].id
        n = len(seriais)
        flash(f'{n} equipamento{"s" if n > 1 else ""} cadastrado{"s" if n > 1 else ""} com sucesso.', "sucesso")
        return redirect(url_for("equipamentos.listagem"))

    return render_template("lote.html", **_contexto_lote())


@equipamentos_bp.route("/saida/validar", methods=["POST"])
def saida_validar():
    """Etapa de conferência: só consulta o estoque, não altera nada.
    Mostra o que será afetado antes do usuário confirmar a movimentação."""
    observacao = (request.form.get("observacoes") or "").strip() or None
    status_novo = (request.form.get("status") or "Em uso").strip()
    texto = request.form.get("seriais_texto") or ""
    seriais = [s.strip() for s in texto.splitlines() if s.strip()]

    if not seriais:
        flash("Cole ou digite pelo menos um número de série.", "erro")
        return render_template("saida.html", status_opcoes=STATUS_OPCOES,
                               form_observacoes=observacao or "", form_status=status_novo,
                               form_texto=texto)
    if status_novo not in STATUS_OPCOES:
        flash("Status inválido.", "erro")
        return render_template("saida.html", status_opcoes=STATUS_OPCOES,
                               form_observacoes=observacao or "", form_status=status_novo,
                               form_texto=texto)

    vistos, duplicados, encontrados, nao_encontrados = set(), [], [], []
    for serial in seriais:
        chave = serial.lower()
        if chave in vistos:
            duplicados.append(serial)
            continue
        vistos.add(chave)
        item = Equipamento.query.filter(db.func.lower(Equipamento.serial) == chave).first()
        if item:
            encontrados.append(item)
        else:
            nao_encontrados.append(serial)

    return render_template(
        "saida_confirmar.html",
        encontrados=encontrados,
        nao_encontrados=nao_encontrados,
        duplicados=duplicados,
        status_novo=status_novo,
        status_novo_slug=status_slug(status_novo),
        observacoes=observacao,
        seriais_confirmados="\n".join(item.serial for item in encontrados),
    )


@equipamentos_bp.route("/saida", methods=["GET", "POST"])
def saida():
    if request.method == "POST":
        observacao = (request.form.get("observacoes") or "").strip() or None
        status_novo = (request.form.get("status") or "Em uso").strip()
        texto = request.form.get("seriais_texto") or ""

        seriais = [s.strip() for s in texto.splitlines() if s.strip()]

        if not seriais:
            flash("Cole ou digite pelo menos um número de série.", "erro")
            return render_template("saida.html", status_opcoes=STATUS_OPCOES,
                                   form_observacoes=observacao or "", form_status=status_novo,
                                   form_texto=texto)

        if status_novo not in STATUS_OPCOES:
            flash("Status inválido.", "erro")
            return render_template("saida.html", status_opcoes=STATUS_OPCOES,
                                   form_observacoes=observacao or "", form_status=status_novo,
                                   form_texto=texto)

        encontrados, nao_encontrados = [], []
        for serial in seriais:
            item = Equipamento.query.filter(
                db.func.lower(Equipamento.serial) == serial.lower()
            ).first()
            if item:
                item.status = status_novo
                if observacao:
                    item.observacoes = observacao
                encontrados.append(serial)
            else:
                nao_encontrados.append(serial)

        if encontrados:
            db.session.commit()

        return render_template(
            "saida_resultado.html",
            observacao=observacao,
            status_novo=status_novo,
            status_novo_slug=status_slug(status_novo),
            encontrados=encontrados,
            nao_encontrados=nao_encontrados,
        )

    return render_template("saida.html", status_opcoes=STATUS_OPCOES,
                           form_observacoes="", form_status="Em uso", form_texto="")


def _montar_contexto_listagem(filtros):
    """Monta o contexto da área de resultados da listagem — agrupada por
    modelo, ou os equipamentos batendo com uma busca por serial. Usado
    tanto pela página completa quanto pelo fragmento buscado via AJAX
    conforme o usuário digita no campo de busca (busca instantânea)."""
    pagina = request.args.get("pagina", 1, type=int)
    if pagina < 1:
        pagina = 1

    if filtros["busca"]:
        # Busca por serial: ignora o agrupamento por modelo e mostra os
        # equipamentos correspondentes diretamente, já que o objetivo aqui
        # é achar um item específico, não navegar por modelo.
        query = _aplicar_filtros(Equipamento.query, filtros)
        query = query.order_by(Equipamento.data_registro.desc())

        paginacao = query.paginate(page=pagina, per_page=ITENS_POR_PAGINA, error_out=False)
        if paginacao.pages and pagina > paginacao.pages:
            paginacao = query.paginate(page=paginacao.pages, per_page=ITENS_POR_PAGINA, error_out=False)

        return {
            "modo": "busca",
            "itens": paginacao.items,
            "total_itens": paginacao.total,
            "paginacao": paginacao,
            "filtro_categoria": filtros["categoria"],
            "filtro_status": filtros["status"],
            "filtro_tecnico": filtros["tecnico"],
            "filtro_busca": filtros["busca"],
        }

    # Visão padrão: um card por modelo, agrupando os equipamentos —
    # evita listar centenas de linhas individuais quando há muitas
    # unidades do mesmo modelo cadastradas.
    query = _aplicar_filtros(Equipamento.query, filtros)
    grupos_query = (
        query.with_entities(
            Equipamento.fabricante,
            Equipamento.modelo,
            Equipamento.categoria,
            db.func.count(Equipamento.id).label("registros"),
            db.func.sum(Equipamento.quantidade).label("unidades"),
        )
        .group_by(Equipamento.fabricante, Equipamento.modelo, Equipamento.categoria)
        .order_by(Equipamento.fabricante, Equipamento.modelo)
    )

    paginacao = grupos_query.paginate(page=pagina, per_page=ITENS_POR_PAGINA, error_out=False)
    if paginacao.pages and pagina > paginacao.pages:
        paginacao = grupos_query.paginate(page=paginacao.pages, per_page=ITENS_POR_PAGINA, error_out=False)

    total_registros = query.count()
    total_itens = query.with_entities(db.func.sum(Equipamento.quantidade)).scalar() or 0

    return {
        "modo": "grupos",
        "grupos": paginacao.items,
        "paginacao": paginacao,
        "total_grupos": paginacao.total,
        "total_registros": total_registros,
        "total_itens": int(total_itens),
        "filtro_categoria": filtros["categoria"],
        "filtro_status": filtros["status"],
        "filtro_tecnico": filtros["tecnico"],
        "filtro_busca": filtros["busca"],
    }


@equipamentos_bp.route("/")
def listagem():
    filtros = _filtros_atuais()

    # Mostra a Etiqueta do que acabou de ser cadastrado (aparece uma única
    # vez, logo após o redirect do cadastro/lote — não é persistido).
    ultimo_cadastro = None
    ultimo_cadastro_id = session.pop("ultimo_cadastro_id", None)
    if ultimo_cadastro_id:
        ultimo_cadastro = Equipamento.query.get(ultimo_cadastro_id)

    # Com fabricante+modelo selecionados: lista os seriais daquele modelo.
    if filtros["fabricante"] and filtros["modelo"]:
        query = _aplicar_filtros(Equipamento.query, filtros)
        query = query.order_by(Equipamento.data_registro.desc())

        pagina = request.args.get("pagina", 1, type=int)
        if pagina < 1:
            pagina = 1
        paginacao = query.paginate(page=pagina, per_page=ITENS_POR_PAGINA, error_out=False)
        if paginacao.pages and pagina > paginacao.pages:
            paginacao = query.paginate(page=paginacao.pages, per_page=ITENS_POR_PAGINA, error_out=False)

        return render_template(
            "listagem_modelo.html",
            itens=paginacao.items,
            total_itens=paginacao.total,
            paginacao=paginacao,
            status_opcoes=STATUS_OPCOES,
            tecnicos_existentes=get_tecnicos_existentes(),
            filtro_status=filtros["status"],
            filtro_tecnico=filtros["tecnico"],
            filtro_fabricante=filtros["fabricante"],
            filtro_modelo=filtros["modelo"],
            ultimo_cadastro=ultimo_cadastro,
        )

    contexto = _montar_contexto_listagem(filtros)
    return render_template(
        "listagem.html",
        categorias=get_categorias_disponiveis(),
        status_opcoes=STATUS_OPCOES,
        tecnicos_existentes=get_tecnicos_existentes(),
        ultimo_cadastro=ultimo_cadastro,
        **contexto,
    )


@equipamentos_bp.route("/fragmento")
def listagem_fragmento():
    """Devolve só a área de resultados (cabeçalho + grade/tabela +
    paginação) da listagem, em HTML, para a busca instantânea — o
    JavaScript troca o conteúdo da página sem recarregar enquanto o
    usuário digita no campo de busca por serial."""
    filtros = _filtros_atuais()
    contexto = _montar_contexto_listagem(filtros)
    return render_template("_fragmento_listagem.html", **contexto)


@equipamentos_bp.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        dados, erros, duplicado_id = _validar_dados(request.form)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("form_equipamento.html",
                                   **_contexto_form(form_data=request.form, serial_duplicado_id=duplicado_id))

        item = Equipamento(**dados)
        db.session.add(item)
        db.session.commit()
        session["ultimo_cadastro_id"] = item.id
        flash(f'Equipamento "{item.fabricante} {item.modelo}" cadastrado com sucesso.', "sucesso")
        return redirect(url_for("equipamentos.listagem"))

    return render_template("form_equipamento.html", **_contexto_form())


@equipamentos_bp.route("/<int:item_id>/editar", methods=["GET", "POST"])
def editar(item_id):
    item = Equipamento.query.get_or_404(item_id)

    if request.method == "POST":
        dados, erros, duplicado_id = _validar_dados(request.form, item_id=item.id)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template(
                "form_equipamento.html",
                **_contexto_form(equipamento=item, form_data=request.form, serial_duplicado_id=duplicado_id),
            )

        for campo, valor in dados.items():
            setattr(item, campo, valor)
        db.session.commit()
        flash(f'Equipamento "{item.fabricante} {item.modelo}" atualizado com sucesso.', "sucesso")
        return redirect(url_for("equipamentos.listagem"))

    return render_template("form_equipamento.html", **_contexto_form(equipamento=item))


@equipamentos_bp.route("/<int:item_id>/excluir", methods=["POST"])
def excluir(item_id):
    item = Equipamento.query.get_or_404(item_id)

    senha = (request.form.get("senha") or "").strip()
    if senha != current_app.config.get("SENHA_EXCLUSAO"):
        flash("Senha incorreta. Exclusão cancelada.", "erro")
        return redirect(url_for("equipamentos.listagem"))

    identificacao = f"{item.fabricante} {item.modelo}"
    db.session.delete(item)
    db.session.commit()
    flash(f'Equipamento "{identificacao}" excluído.', "sucesso")
    return redirect(url_for("equipamentos.listagem"))


@equipamentos_bp.route("/exportar")
def exportar():
    filtros = _filtros_atuais()
    query = _aplicar_filtros(Equipamento.query, filtros)
    itens = query.order_by(Equipamento.data_registro.desc()).all()

    buffer = gerar_planilha_equipamentos(itens)
    nome_arquivo = f"estoque_ti_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
