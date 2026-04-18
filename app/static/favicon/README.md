# Favicons

Coloque seus arquivos de favicon nesta pasta.

Arquivos recomendados:

- `favicon.ico`
- `favicon.svg`
- `apple-touch-icon.png`
- `favicon-48x48.png`
- `favicon-192x192.png`
- `favicon-512x512.png`

Para manter compatibilidade com Google e navegadores:

- use imagem quadrada
- prefira tamanhos multiplos de `48x48`
- mantenha `favicon.ico` para compatibilidade legada
- se trocar os nomes, ajuste tambem os links em [base.html](/c:/Users/Rabel/OneDrive/Documentos/14.%20BlueOcean/pdv/app/templates/bases/base.html:1)

O sistema ja expõe:

- `/favicon.ico`
- `/site.webmanifest`
- `/browserconfig.xml`

Se `favicon.ico` ainda nao existir, a aplicacao usa `favicon.svg` como fallback.
