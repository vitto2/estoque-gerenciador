from flask import Blueprint, render_template
from sqlalchemy import func

from models import Equipamento, db

dashboard_bp = Blueprint("dashboard", __name__)

NAO_INFORMADO = "Não informado"


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
def dashboard():
    total_registros = Equipamento.query.count()
    total_itens = db.session.query(func.sum(Equipamento.quantidade)).scalar() or 0

    fabricantes_distintos = (
        db.session.query(func.count(func.distinct(Equipamento.fabricante))).scalar() or 0
    )
    sem_serial = Equipamento.query.filter(Equipamento.serial.is_(None)).count()
    pendentes_arturito = Equipamento.query.filter(
        Equipamento.status_arturito == "Pendente de verificação"
    ).count()

    # Quantidade total por categoria
    por_categoria = (
        db.session.query(Equipamento.categoria, func.sum(Equipamento.quantidade))
        .group_by(Equipamento.categoria)
        .order_by(Equipamento.categoria)
        .all()
    )

    # Quantidade total por fabricante, do maior para o menor
    por_fabricante = (
        db.session.query(Equipamento.fabricante, func.sum(Equipamento.quantidade))
        .group_by(Equipamento.fabricante)
        .order_by(func.sum(Equipamento.quantidade).desc())
        .all()
    )

    # Onde os equipamentos estão guardados
    por_localizacao = (
        db.session.query(Equipamento.local_armazenamento, func.sum(Equipamento.quantidade))
        .group_by(Equipamento.local_armazenamento)
        .all()
    )

    # Quantos já foram conferidos no Arturito
    por_status_arturito = (
        db.session.query(Equipamento.status_arturito, func.sum(Equipamento.quantidade))
        .group_by(Equipamento.status_arturito)
        .all()
    )

    # Evolução de cadastros: nº de registros criados por dia.
    # func.date() é suportada tanto por SQLite quanto por Postgres, ao
    # contrário de func.strftime() (exclusiva do SQLite, quebra em produção).
    evolucao = (
        db.session.query(
            func.date(Equipamento.data_registro).label("dia"),
            func.count(Equipamento.id),
        )
        .group_by("dia")
        .order_by("dia")
        .all()
    )

    return render_template(
        "dashboard.html",
        total_registros=total_registros,
        total_itens=int(total_itens),
        fabricantes_distintos=fabricantes_distintos,
        sem_serial=sem_serial,
        pendentes_arturito=pendentes_arturito,
        categorias_labels=[c for c, _ in por_categoria],
        categorias_valores=[int(v) for _, v in por_categoria],
        fabricantes_labels=[f for f, _ in por_fabricante],
        fabricantes_valores=[int(v) for _, v in por_fabricante],
        localizacao_labels=[l or NAO_INFORMADO for l, _ in por_localizacao],
        localizacao_valores=[int(v) for _, v in por_localizacao],
        arturito_labels=[s or NAO_INFORMADO for s, _ in por_status_arturito],
        arturito_valores=[int(v) for _, v in por_status_arturito],
        evolucao_labels=[str(d) for d, _ in evolucao],
        evolucao_valores=[int(v) for _, v in evolucao],
    )
