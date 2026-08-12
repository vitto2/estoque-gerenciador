"""
Modelo de dados do Sistema de Estoque de TI.

Existe uma única entidade (Equipamento), pois o controle aqui é feito
por "lote" (tipo + quantidade + status) e não por número de série
individual. Ex.: um registro pode representar "5 notebooks Dell,
status Disponível" e outro "2 notebooks Dell, status Manutenção".
Dá pra evoluir para rastreio unitário depois, se precisar.
"""
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Opções usadas nos formulários e filtros. Concentradas aqui pra
# facilitar manutenção (adicionar/remover categoria = editar 1 lista).
CATEGORIAS = [
    "Notebook",
    "Monitor",
    "Periférico",
    "Cabo",
    "Impressora",
    "Coletor de Dados",
    "Leitor/Scanner",
]
# "Outro" não entra nessa lista: é só uma opção de formulário que libera um
# campo de texto livre (routes/equipamentos.py). Nunca é um valor salvo no banco.

STATUS_OPCOES = [
    "Disponível",
    "Em uso",
    "Manutenção",
    "Baixado",
]

LOCAIS_ARMAZENAMENTO = [
    "Operação",
    "Meli-help Is",
    "Estoque TI G200",
]

_STATUS_SLUGS = {
    "Disponível": "disponivel",
    "Em uso": "em-uso",
    "Manutenção": "manutencao",
    "Baixado": "baixado",
}


def status_slug(status):
    """Versão sem acento/espaço do status, pra usar como classe CSS."""
    return _STATUS_SLUGS.get(status, "outro")


class Equipamento(db.Model):
    __tablename__ = "equipamentos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    serial = db.Column(db.String(100), nullable=True)
    local_armazenamento = db.Column(db.String(50), nullable=True)
    ticket_jira = db.Column(db.String(50), nullable=True)
    data_registro = db.Column(db.DateTime, nullable=False, default=datetime.now)
    tecnico_responsavel = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="Disponível")

    def __repr__(self):
        return f"<Equipamento {self.id} {self.nome} ({self.categoria}) - {self.status}>"

    @property
    def status_slug(self):
        """Versão sem acento/espaço do status, pra usar como classe CSS."""
        return status_slug(self.status)

    def to_dict(self):
        """Serialização usada pelas rotas do dashboard."""
        return {
            "id": self.id,
            "nome": self.nome,
            "categoria": self.categoria,
            "quantidade": self.quantidade,
            "data_registro": self.data_registro.strftime("%d/%m/%Y %H:%M"),
            "tecnico_responsavel": self.tecnico_responsavel,
            "status": self.status,
        }
