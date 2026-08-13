"""
Extração do número de série a partir de foto, usando a API de visão do
Gemini (Google AI Studio — tem camada gratuita, sem cartão de crédito).
Mantido separado das rotas para deixar routes/equipamentos.py focado em
request/response (mesmo padrão de exportacao.py).
"""
import json
import sys
import traceback

from google import genai
from google.genai import types

PROMPT_EXTRACAO_SERIAL = (
    "Esta é uma foto de uma etiqueta ou caixa de produto eletrônico. "
    'Extraia apenas o número de série do equipamento — geralmente indicado '
    'como "S/N", "SN", "Serial", "Serial No" ou "Nº de série". '
    "Ignore outros códigos como modelo (Model/P/N), endereço MAC, número de "
    "nota fiscal ou código de barras sem rótulo de serial. "
    "Se não encontrar nenhum número de série legível na imagem, informe null."
)

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "serial": {
            "type": "STRING",
            "nullable": True,
            "description": "O número de série exato encontrado na etiqueta, ou null.",
        },
    },
    "required": ["serial"],
}

TAMANHO_MAXIMO_BYTES = 8 * 1024 * 1024


class ExtracaoIndisponivel(Exception):
    """A chave do Gemini não está configurada neste ambiente."""


class ExtracaoFalhou(Exception):
    """A chamada ao Gemini falhou ou retornou algo que não deu pra interpretar."""


def extrair_serial_da_imagem(conteudo_bytes, mimetype, api_key, model):
    """Envia a imagem para o Gemini e devolve o serial encontrado (ou None)."""
    if not api_key:
        raise ExtracaoIndisponivel("Extração por foto não está configurada.")

    if len(conteudo_bytes) > TAMANHO_MAXIMO_BYTES:
        raise ValueError("Imagem muito grande (máximo 8MB).")

    client = genai.Client(api_key=api_key)

    try:
        resposta = client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(data=conteudo_bytes, mime_type=mimetype),
                PROMPT_EXTRACAO_SERIAL,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
                max_output_tokens=300,
            ),
        )
        dados = resposta.parsed if resposta.parsed is not None else json.loads(resposta.text)
    except Exception as erro:
        # Impresso em stderr pra aparecer nos Function Logs da Vercel — a causa mais
        # comum é falta de crédito/limite da camada gratuita esgotado na conta do
        # Google AI Studio, que fica escondida atrás da mensagem genérica abaixo.
        print(f"[extrair_serial] Falha na chamada ao Gemini: {erro!r}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise ExtracaoFalhou("Não consegui processar a imagem agora.") from erro

    serial = (dados.get("serial") or "").strip() or None
    return serial
