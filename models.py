"""
Modelo de dados do Sistema de Estoque de TI.

Existe uma única entidade (Equipamento), pois o controle aqui é feito
por "lote" (tipo + quantidade + status) e não por número de série
individual. Ex.: um registro pode representar "5 notebooks Dell,
status Disponível" e outro "2 notebooks Dell, status Manutenção".
Dá pra evoluir para rastreio unitário depois, se precisar.
"""
import re
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates

db = SQLAlchemy()

# Quando um serial puramente numérico é copiado de uma planilha (Excel/
# Sheets guardam números como float, e o texto colado vem com essa
# terminação), sobra um ".0" no final que nunca faz parte do serial real.
_SERIAL_COM_SUFIXO_FLOAT = re.compile(r"^(\d+)\.0+$")


def normalizar_serial(serial):
    """Remove o ".0" residual de um serial numérico colado de planilha.
    Usado tanto na entrada (formulário, lote, extração por foto) quanto
    como validador do modelo, pra nenhum caminho de escrita deixar passar."""
    if not serial:
        return serial
    serial = serial.strip()
    match = _SERIAL_COM_SUFIXO_FLOAT.match(serial)
    return match.group(1) if match else serial

# Opções usadas nos formulários e filtros. Concentradas aqui pra
# facilitar manutenção (adicionar/remover categoria = editar 1 lista).
CATEGORIAS = [
    "Notebook",
    "Desktop",
    "Monitor",
    "Handheld",
    "Impressora",
    "Acessório",
]
# "Outro" não entra nessa lista: é só uma opção de formulário que libera um
# campo de texto livre (routes/equipamentos.py). Nunca é um valor salvo no banco.

# Categorias em que o equipamento normalmente vem com serial de fábrica —
# nessas, o campo "Número de série" passa a ser obrigatório no cadastro.
# Acessório e categorias customizadas ("Outro") continuam opcionais,
# pois nem sempre têm um serial de fato.
CATEGORIAS_COM_SERIAL_OBRIGATORIO = [
    "Notebook",
    "Desktop",
    "Monitor",
    "Handheld",
    "Impressora",
]

STATUS_OPCOES = [
    "Disponível",
    "Reservado",
    "Em uso",
    "Em manutenção",
    "Baixado",
]

LOCAIS_ARMAZENAMENTO = [
    "Estoque principal",
    "Melihelp",
    "Bancada",
    "Operação",
]

# Reflete se o cadastro deste equipamento no Arturito (sistema interno usado
# pelo time) já foi conferido/atualizado ou ainda está pendente.
STATUS_ARTURITO_OPCOES = [
    "Atualizado",
    "Pendente de verificação",
]

_STATUS_SLUGS = {
    "Disponível": "disponivel",
    "Reservado": "reservado",
    "Em uso": "em-uso",
    "Em manutenção": "em-manutencao",
    "Baixado": "baixado",
}


def status_slug(status):
    """Versão sem acento/espaço do status, pra usar como classe CSS."""
    return _STATUS_SLUGS.get(status, "outro")


_STATUS_DESCRICOES = {
    "Disponível": "Pronto para uso, ninguém está com ele agora",
    "Reservado": "Separado para alguém ou algum uso específico, mas ainda não entregue",
    "Em uso": "Alocado a alguém neste momento",
    "Em manutenção": "Em conserto ou revisão",
    "Baixado": "Fora de uso, descartado ou removido do estoque",
}


def status_descricao(status):
    """Explicação curta do status, usada em tooltips e legendas nos formulários."""
    return _STATUS_DESCRICOES.get(status, "")


class Equipamento(db.Model):
    __tablename__ = "equipamentos"

    id = db.Column(db.Integer, primary_key=True)
    fabricante = db.Column(db.String(100), nullable=False)
    modelo = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    serial = db.Column(db.String(100), nullable=True)
    local_armazenamento = db.Column(db.String(50), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    status_arturito = db.Column(db.String(30), nullable=True)
    data_registro = db.Column(db.DateTime, nullable=False, default=datetime.now)
    tecnico_responsavel = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="Disponível")

    def __repr__(self):
        return f"<Equipamento {self.id} {self.fabricante} {self.modelo} ({self.categoria}) - {self.status}>"

    @validates("serial")
    def _validar_serial(self, key, value):
        return normalizar_serial(value)

    @property
    def status_slug(self):
        """Versão sem acento/espaço do status, pra usar como classe CSS."""
        return status_slug(self.status)

    def to_dict(self):
        """Serialização usada pelas rotas do dashboard."""
        return {
            "id": self.id,
            "fabricante": self.fabricante,
            "modelo": self.modelo,
            "categoria": self.categoria,
            "quantidade": self.quantidade,
            "data_registro": self.data_registro.strftime("%d/%m/%Y %H:%M"),
            "tecnico_responsavel": self.tecnico_responsavel,
            "status": self.status,
        }


def normalizar_seriais_existentes(sessao=None):
    """Corrige, em lote, os seriais já salvos que ficaram com um ".0" no
    final (ver normalizar_serial) — usado pelo comando `flask normalizar-seriais`
    para arrumar dados que entraram assim antes dessa validação existir.

    Não aplica a correção quando ela colidiria com outro serial já
    existente (ou com outro equipamento que precisaria da mesma correção)
    — esses casos ficam fora da lista de "corrigidos" e voltam em
    "colisoes" para revisão manual, já que decidir qual dos dois é o
    registro certo exige contexto que o código não tem.
    """
    sessao = sessao or db.session
    equipamentos = Equipamento.query.filter(Equipamento.serial.isnot(None)).all()

    propostas = {e.id: normalizar_serial(e.serial) for e in equipamentos}
    por_chave = {}
    for equip_id, novo_serial in propostas.items():
        por_chave.setdefault(novo_serial.lower(), []).append(equip_id)

    corrigidos = []
    colisoes = []

    for equip in equipamentos:
        original = equip.serial
        novo = propostas[equip.id]
        if novo == original:
            continue

        ids_na_mesma_chave = por_chave[novo.lower()]
        if len(ids_na_mesma_chave) > 1:
            colisoes.append({
                "id": equip.id,
                "original": original,
                "proposto": novo,
                "colide_com": [i for i in ids_na_mesma_chave if i != equip.id],
            })
            continue

        equip.serial = novo
        corrigidos.append({"id": equip.id, "original": original, "novo": novo})

    sessao.commit()
    return {"corrigidos": corrigidos, "colisoes": colisoes}
