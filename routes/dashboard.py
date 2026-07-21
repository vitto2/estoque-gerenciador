from flask import Blueprint, render_template
from sqlalchemy import func

from models import STATUS_OPCOES, Equipamento, db

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    total_registros = Equipamento.query.count()
    total_itens = db.session.query(func.sum(Equipamento.quantidade)).scalar() or 0

    # Quantidade total por categoria
    por_categoria = (
        db.session.query(Equipamento.categoria, func.sum(Equipamento.quantidade))
        .group_by(Equipamento.categoria)
        .order_by(Equipamento.categoria)
        .all()
    )

    # Distribuição por status (soma de quantidade, não contagem de registros),
    # respeitando a ordem operacional fixa em vez da ordem alfabética
    mapa_status = dict(
        db.session.query(Equipamento.status, func.sum(Equipamento.quantidade))
        .group_by(Equipamento.status)
        .all()
    )
    status_labels = [s for s in STATUS_OPCOES if s in mapa_status]
    status_labels += sorted(s for s in mapa_status if s not in STATUS_OPCOES)
    status_valores = [int(mapa_status[s]) for s in status_labels]

    # Evolução de cadastros: nº de registros criados por dia
    evolucao = (
        db.session.query(
            func.strftime("%Y-%m-%d", Equipamento.data_registro).label("dia"),
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
        categorias_labels=[c for c, _ in por_categoria],
        categorias_valores=[int(v) for _, v in por_categoria],
        status_labels=status_labels,
        status_valores=status_valores,
        evolucao_labels=[d for d, _ in evolucao],
        evolucao_valores=[int(v) for _, v in evolucao],
    )
