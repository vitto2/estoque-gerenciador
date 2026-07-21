# Sistema de Estoque de TI

Aplicação web para cadastro e controle de estoque de equipamentos de TI
(notebooks, monitores, periféricos, cabos, impressoras, coletores de
dados, leitores/scanners etc).

**Status:** completo — cadastro, listagem com filtros, dashboard e exportação para Excel.

## Requisitos
- Python 3.10+ (testado com 3.12)

## Instalação
```bash
cd estoque-ti

# Recomendado: ambiente virtual
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Como rodar
```bash
python app.py
```
Acesse http://127.0.0.1:5000 no navegador. O banco SQLite
(`instance/estoque.db`) é criado automaticamente na primeira execução, vazio.

> `debug=True` em `app.py` é ótimo para desenvolvimento local. Se um dia
> este app for exposto além do localhost/rede interna, desative o debug
> e veja a seção "Limitações conhecidas" abaixo.

## Estrutura do projeto
```
estoque-ti/
├── app.py              # application factory: cria a app e registra os blueprints
├── config.py           # configuração (caminho do banco SQLite)
├── models.py            # modelo Equipamento + listas de categorias/status
├── exportacao.py         # geração da planilha .xlsx
├── requirements.txt
├── routes/
│   ├── equipamentos.py   # listagem, filtros, cadastro, edição, exclusão, exportação
│   └── dashboard.py       # agregações e dados dos gráficos
├── templates/
│   ├── base.html          # layout, navegação, mensagens flash
│   ├── listagem.html       # tabela + filtros + botão de exportar
│   ├── form_equipamento.html  # formulário (cadastro e edição)
│   └── dashboard.html      # cards de resumo + 3 gráficos
├── static/
│   ├── css/style.css
│   └── js/chart.min.js    # Chart.js hospedado localmente (sem depender de CDN externo)
└── instance/estoque.db    # banco SQLite (gerado ao rodar, não versionado)
```

## Funcionalidades

**Cadastro** (`/equipamentos/novo`) — formulário com os 6 campos pedidos.
A categoria tem uma lista pré-definida (Notebook, Monitor, Periférico, Cabo,
Impressora, Coletor de Dados, Leitor/Scanner) + opção "Outro" que libera um
campo de texto livre para categorias novas (essas passam a aparecer nos
filtros e no próprio formulário depois de cadastradas uma vez). O campo de
técnico tem autocomplete com os nomes já usados.

**Listagem** (`/equipamentos/`, também a home) — tabela com todos os itens,
mais recentes primeiro, com filtro por categoria, status e técnico (via
querystring, então dá pra favoritar/compartilhar um link já filtrado).
Badges coloridos por status para escaneamento visual rápido.

**Dashboard** (`/dashboard`) — quantidade total por categoria (barras),
distribuição por status (rosca) e evolução de cadastros por dia (linha),
mais dois cards de resumo (itens totais em estoque e nº de equipamentos
cadastrados).

**Exportação** (`/equipamentos/exportar`) — gera um .xlsx com cabeçalho
estilizado e largura de coluna ajustada, respeitando os filtros ativos na
listagem no momento do clique (limpe os filtros antes se quiser exportar tudo).

**Edição/Exclusão** — a partir da listagem (ícones ✏️/🗑️). Exclusão pede
confirmação antes de enviar.

## Modelo de dados (Equipamento)
| Campo                 | Tipo      | Observação                              |
|-----------------------|-----------|------------------------------------------|
| nome                  | string    | nome/tipo do equipamento                 |
| categoria             | string    | lista fixa + customizadas via "Outro"    |
| quantidade            | inteiro   | > 0                                       |
| data_registro         | datetime  | preenchida automaticamente               |
| tecnico_responsavel   | string    | quem cadastrou                           |
| status                | string    | Disponível / Em uso / Manutenção / Baixado |

## Limitações conhecidas / possíveis melhorias futuras
- Sem autenticação e sem CSRF nos formulários — adequado para uso em
  localhost/rede interna confiável; se for exposto mais amplamente, vale
  adicionar Flask-WTF (CSRF) e algum login.
- Rastreio é por lote (tipo + quantidade + status), não por nº de série
  individual. Dá pra evoluir se precisar rastrear unidade a unidade.
- Sem paginação na listagem — tranquilo até uns milhares de registros;
  se crescer muito, é a próxima coisa a adicionar.
- Gráfico de evolução agrupa por dia; se o histórico ficar muito longo,
  pode fazer sentido agrupar por semana/mês.
