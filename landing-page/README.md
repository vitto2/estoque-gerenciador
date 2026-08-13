# Landing page — Sistema digital para corretores de imóveis

Landing page comercial estática (HTML/CSS/JS puro, sem build) para divulgação de serviços de sites, landing pages e automações voltados a corretores de imóveis. CTA único: conversa no WhatsApp.

## Como rodar localmente

Abra `index.html` direto no navegador, ou sirva a pasta com qualquer servidor estático:

```bash
python3 -m http.server 8000
```

## Antes de publicar

Substitua os placeholders:

- `script.js` → `CONFIG.whatsappNumber`: número de WhatsApp em formato DDI+DDD+número (só dígitos), usado para montar todos os links `wa.me`.
- `index.html` → `[INSTAGRAM_HANDLE]` (rodapé): usuário do Instagram.
- `index.html` → `[WHATSAPP_NUMBER]` (rodapé, texto exibido): número de WhatsApp em formato legível.

## Estrutura

- `index.html` — marcação e conteúdo das 13 seções.
- `styles.css` — design tokens (paleta, tipografia) e estilos de componente, mobile-first.
- `script.js` — menu mobile, acordeão do FAQ, calculadora interativa, reveal on scroll, montagem dos links de WhatsApp.

Sem dependências externas além das fontes do Google Fonts (Bricolage Grotesque, IBM Plex Mono, Work Sans).
