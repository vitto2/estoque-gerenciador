/**
 * Extração do número de série a partir de foto — OCR 100% no navegador via
 * Tesseract.js. Gratuito: nenhuma foto sai do dispositivo, não depende de
 * chave de API nem de crédito em nenhuma conta.
 *
 * Como o OCR não entende "o que é um serial" (só lê texto cru), procuramos
 * no texto reconhecido uma linha com um rótulo típico de etiqueta
 * ("S/N", "Serial", "Nº de série"...) e extraímos o valor ao lado dele.
 * Isso evita pegar por engano o modelo, o MAC address ou o código de barras.
 */

const _PADRAO_ROTULO_SERIAL = /^(s\/?n|serial(?:\s*(?:no\.?|number|n[uú]mero)?)?|n[ºo]\.?\s*de\s*s[ée]rie|numero\s*de\s*serie)\s*[:\-.]?\s*(.*)$/i;

function _limparValorSerial(valor) {
    valor = valor.replace(/^[:\-.\s]+|[:\-.\s]+$/g, '');
    const corte = valor.search(/\s{2,}|\t/);
    if (corte > 0) valor = valor.slice(0, corte);
    return valor.trim();
}

/** Exportada à parte pra poder ser testada isoladamente (sem precisar de OCR de verdade). */
function extrairSerialDoTexto(textoOcr) {
    const linhas = (textoOcr || '').split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    for (let i = 0; i < linhas.length; i++) {
        const m = linhas[i].match(_PADRAO_ROTULO_SERIAL);
        if (!m) continue;
        let valor = _limparValorSerial(m[2] || '');
        if (!valor && i + 1 < linhas.length) {
            valor = _limparValorSerial(linhas[i + 1]);
        }
        if (valor && valor.replace(/[^a-zA-Z0-9]/g, '').length >= 3) {
            return valor;
        }
    }
    return null;
}

function redimensionarImagem(arquivo, maxDim, qualidade) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        const url = URL.createObjectURL(arquivo);
        img.onload = () => {
            let { width, height } = img;
            if (width > maxDim || height > maxDim) {
                if (width > height) {
                    height = Math.round((height * maxDim) / width);
                    width = maxDim;
                } else {
                    width = Math.round((width * maxDim) / height);
                    height = maxDim;
                }
            }
            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            canvas.getContext('2d').drawImage(img, 0, 0, width, height);
            canvas.toBlob((blob) => {
                URL.revokeObjectURL(url);
                blob ? resolve(blob) : reject(new Error('Falha ao processar a imagem'));
            }, 'image/jpeg', qualidade);
        };
        img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('Falha ao carregar a imagem')); };
        img.src = url;
    });
}

/**
 * Liga um botão de câmera + input de arquivo a um fluxo de OCR local.
 * `aoAtualizar(resultado)` é chamado em cada etapa com:
 *   { status: 'carregando' }
 *   { status: 'sucesso', serial: '...' }
 *   { status: 'falha', mensagem: '...' }
 *   { status: 'erro' }
 */
function ligarBotaoExtrairSerial(botao, inputArquivo, aoAtualizar) {
    botao.addEventListener('click', () => inputArquivo.click());

    inputArquivo.addEventListener('change', async () => {
        const arquivo = inputArquivo.files[0];
        if (!arquivo) return;

        botao.disabled = true;
        aoAtualizar({ status: 'carregando' });

        try {
            const imagem = await redimensionarImagem(arquivo, 1600, 0.9);
            const { data } = await Tesseract.recognize(imagem, 'eng');
            const serial = extrairSerialDoTexto(data.text);

            if (serial) {
                aoAtualizar({ status: 'sucesso', serial });
            } else {
                aoAtualizar({ status: 'falha', mensagem: 'Não encontrei um "S/N" ou "Serial" legível nessa foto. Tente uma foto mais próxima e nítida da etiqueta.' });
            }
        } catch (e) {
            aoAtualizar({ status: 'erro' });
        } finally {
            botao.disabled = false;
            inputArquivo.value = '';
        }
    });
}
