"""
Extração do número de série a partir de foto, usando a API de visão da OpenAI.
Mantido separado das rotas para deixar routes/equipamentos.py focado em
request/response (mesmo padrão de exportacao.py).
"""
import base64
import json

from openai import OpenAI

PROMPT_EXTRACAO_SERIAL = (
    "Esta é uma foto de uma etiqueta ou caixa de produto eletrônico. "
    'Extraia apenas o número de série do equipamento — geralmente indicado '
    'como "S/N", "SN", "Serial", "Serial No" ou "Nº de série". '
    "Ignore outros códigos como modelo (Model/P/N), endereço MAC, número de "
    "nota fiscal ou código de barras sem rótulo de serial. "
    'Responda estritamente em JSON no formato {"serial": "VALOR"} ou '
    '{"serial": null} se não encontrar nenhum número de série legível na '
    "imagem. Não inclua explicações, apenas o JSON."
)

TAMANHO_MAXIMO_BYTES = 8 * 1024 * 1024


class ExtracaoIndisponivel(Exception):
    """A chave da OpenAI não está configurada neste ambiente."""


class ExtracaoFalhou(Exception):
    """A chamada à OpenAI falhou ou retornou algo que não deu pra interpretar."""


def extrair_serial_da_imagem(conteudo_bytes, mimetype, api_key, model):
    """Envia a imagem para a OpenAI e devolve o serial encontrado (ou None)."""
    if not api_key:
        raise ExtracaoIndisponivel("Extração por foto não está configurada.")

    if len(conteudo_bytes) > TAMANHO_MAXIMO_BYTES:
        raise ValueError("Imagem muito grande (máximo 8MB).")

    img_b64 = base64.b64encode(conteudo_bytes).decode("ascii")
    client = OpenAI(api_key=api_key)

    try:
        resposta = client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT_EXTRACAO_SERIAL},
                    {"type": "image_url", "image_url": {"url": f"data:{mimetype};base64,{img_b64}"}},
                ],
            }],
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        dados = json.loads(resposta.choices[0].message.content)
    except Exception as erro:
        raise ExtracaoFalhou("Não consegui processar a imagem agora.") from erro

    serial = (dados.get("serial") or "").strip() or None
    return serial
