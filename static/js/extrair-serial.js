/**
 * Extração do número de série a partir de foto (câmera ou galeria).
 * Redimensiona a imagem no navegador antes de enviar, pra manter o upload
 * rápido e leve mesmo com fotos grandes de celular.
 */
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
 * Liga um botão de câmera + input de arquivo a um fluxo de extração.
 * `aoAtualizar(resultado)` é chamado em cada etapa com:
 *   { status: 'carregando' }
 *   { status: 'sucesso', serial: '...' }
 *   { status: 'falha', mensagem: '...' }
 *   { status: 'erro' }
 */
function ligarBotaoExtrairSerial(botao, inputArquivo, urlEndpoint, aoAtualizar) {
    botao.addEventListener('click', () => inputArquivo.click());

    inputArquivo.addEventListener('change', async () => {
        const arquivo = inputArquivo.files[0];
        if (!arquivo) return;

        botao.disabled = true;
        aoAtualizar({ status: 'carregando' });

        try {
            const imagem = await redimensionarImagem(arquivo, 1280, 0.82);
            const formData = new FormData();
            formData.append('foto', imagem, 'foto.jpg');
            const tokenEl = document.querySelector('input[name=csrf_token]');
            if (tokenEl) formData.append('csrf_token', tokenEl.value);

            const resp = await fetch(urlEndpoint, { method: 'POST', body: formData });
            const dados = await resp.json();

            if (resp.ok && dados.serial) {
                aoAtualizar({ status: 'sucesso', serial: dados.serial });
            } else {
                aoAtualizar({ status: 'falha', mensagem: dados.mensagem || dados.erro });
            }
        } catch (e) {
            aoAtualizar({ status: 'erro' });
        } finally {
            botao.disabled = false;
            inputArquivo.value = '';
        }
    });
}
