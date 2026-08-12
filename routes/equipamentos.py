from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for

from exportacao import gerar_planilha_equipamentos
from models import CATEGORIAS, STATUS_OPCOES, Equipamento, db

equipamentos_bp = Blueprint("equipamentos", __name__, url_prefix="/equipamentos")


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
            "nome": form_data.get("nome", ""),
            "categoria": form_data.get("categoria", ""),
            "categoria_customizada": form_data.get("categoria_customizada", ""),
            "quantidade": form_data.get("quantidade", ""),
            "tecnico_responsavel": form_data.get("tecnico_responsavel", ""),
            "status": form_data.get("status", "Disponível"),
        }
    if equipamento is not None:
        return {
            "nome": equipamento.nome,
            "categoria": equipamento.categoria,
            "categoria_customizada": "",
            "quantidade": equipamento.quantidade,
            "tecnico_responsavel": equipamento.tecnico_responsavel,
            "status": equipamento.status,
        }
    return {
        "nome": "",
        "categoria": "",
        "categoria_customizada": "",
        "quantidade": 1,
        "tecnico_responsavel": "",
        "status": "Disponível",
    }


def _validar_dados(form):
    """Valida os campos do formulário. Retorna (dados_prontos_pra_salvar, lista_de_erros)."""
    erros = []

    nome = (form.get("nome") or "").strip()
    if not nome:
        erros.append("Informe o nome/tipo do equipamento.")

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

    tecnico = (form.get("tecnico_responsavel") or "").strip()
    if not tecnico:
        erros.append("Informe o técnico responsável.")

    status = (form.get("status") or "").strip()
    if status not in STATUS_OPCOES:
        erros.append("Selecione um status válido.")

    dados = {
        "nome": nome,
        "categoria": categoria,
        "quantidade": quantidade,
        "tecnico_responsavel": tecnico,
        "status": status,
    }
    return dados, erros


def _contexto_form(equipamento=None, form_data=None):
    return {
        "equipamento": equipamento,
        "valores": _valores_iniciais(equipamento=equipamento, form_data=form_data),
        "categorias": get_categorias_disponiveis() + ["Outro"],
        "status_opcoes": STATUS_OPCOES,
        "tecnicos_existentes": get_tecnicos_existentes(),
    }


def _filtros_atuais():
    return {
        "categoria": request.args.get("categoria", "").strip(),
        "status": request.args.get("status", "").strip(),
        "tecnico": request.args.get("tecnico", "").strip(),
    }


def _aplicar_filtros(query, filtros):
    if filtros["categoria"]:
        query = query.filter(Equipamento.categoria == filtros["categoria"])
    if filtros["status"]:
        query = query.filter(Equipamento.status == filtros["status"])
    if filtros["tecnico"]:
        query = query.filter(Equipamento.tecnico_responsavel == filtros["tecnico"])
    return query


def _contexto_lote(form_data=None, seriais=None):
    fd = form_data or {}
    return {
        "valores": {
            "nome": fd.get("nome", ""),
            "categoria": fd.get("categoria", ""),
            "categoria_customizada": fd.get("categoria_customizada", ""),
            "tecnico_responsavel": fd.get("tecnico_responsavel", ""),
            "status": fd.get("status", "Disponível"),
        },
        "seriais": seriais if seriais is not None else [""],
        "categorias": get_categorias_disponiveis() + ["Outro"],
        "status_opcoes": STATUS_OPCOES,
        "tecnicos_existentes": get_tecnicos_existentes(),
    }


@equipamentos_bp.route("/lote", methods=["GET", "POST"])
def lote():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        categoria = (request.form.get("categoria") or "").strip()
        if categoria == "Outro":
            categoria = (request.form.get("categoria_customizada") or "").strip()
        tecnico = (request.form.get("tecnico_responsavel") or "").strip()
        status = (request.form.get("status") or "").strip()
        seriais_raw = request.form.getlist("serial")

        erros = []
        if not nome:
            erros.append("Informe o nome/tipo do equipamento.")
        if not categoria:
            erros.append("Informe a categoria.")
        if not tecnico:
            erros.append("Informe o técnico responsável.")
        if status not in STATUS_OPCOES:
            erros.append("Selecione um status válido.")

        seriais = [s.strip() for s in seriais_raw if s.strip()]
        if not seriais:
            erros.append("Adicione pelo menos um número de série.")

        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("lote.html", **_contexto_lote(form_data=request.form, seriais=seriais_raw))

        for serial in seriais:
            db.session.add(Equipamento(
                nome=nome,
                categoria=categoria,
                quantidade=1,
                serial=serial,
                tecnico_responsavel=tecnico,
                status=status,
            ))
        db.session.commit()
        n = len(seriais)
        flash(f'{n} equipamento{"s" if n > 1 else ""} cadastrado{"s" if n > 1 else ""} com sucesso.', "sucesso")
        return redirect(url_for("equipamentos.listagem"))

    return render_template("lote.html", **_contexto_lote())


@equipamentos_bp.route("/")
def listagem():
    filtros = _filtros_atuais()
    query = _aplicar_filtros(Equipamento.query, filtros)
    itens = query.order_by(Equipamento.data_registro.desc()).all()

    return render_template(
        "listagem.html",
        itens=itens,
        categorias=get_categorias_disponiveis(),
        status_opcoes=STATUS_OPCOES,
        tecnicos_existentes=get_tecnicos_existentes(),
        filtro_categoria=filtros["categoria"],
        filtro_status=filtros["status"],
        filtro_tecnico=filtros["tecnico"],
    )


@equipamentos_bp.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        dados, erros = _validar_dados(request.form)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("form_equipamento.html", **_contexto_form(form_data=request.form))

        item = Equipamento(**dados)
        db.session.add(item)
        db.session.commit()
        flash(f'Equipamento "{item.nome}" cadastrado com sucesso.', "sucesso")
        return redirect(url_for("equipamentos.listagem"))

    return render_template("form_equipamento.html", **_contexto_form())


@equipamentos_bp.route("/<int:item_id>/editar", methods=["GET", "POST"])
def editar(item_id):
    item = Equipamento.query.get_or_404(item_id)

    if request.method == "POST":
        dados, erros = _validar_dados(request.form)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template(
                "form_equipamento.html",
                **_contexto_form(equipamento=item, form_data=request.form),
            )

        for campo, valor in dados.items():
            setattr(item, campo, valor)
        db.session.commit()
        flash(f'Equipamento "{item.nome}" atualizado com sucesso.', "sucesso")
        return redirect(url_for("equipamentos.listagem"))

    return render_template("form_equipamento.html", **_contexto_form(equipamento=item))


@equipamentos_bp.route("/<int:item_id>/excluir", methods=["POST"])
def excluir(item_id):
    item = Equipamento.query.get_or_404(item_id)
    nome = item.nome
    db.session.delete(item)
    db.session.commit()
    flash(f'Equipamento "{nome}" excluído.', "sucesso")
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
