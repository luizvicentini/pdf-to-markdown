# Assets

Coloque aqui o arquivo `icon.ico` que será embutido no executável.

- Formato: `.ico` (Windows Icon).
- Tamanhos recomendados dentro do `.ico`: 16x16, 32x32, 48x48, 256x256.
- Ferramentas para gerar: https://www.icoconverter.com/, GIMP, ImageMagick.

Se `icon.ico` não existir, o `build.spec` ignora silenciosamente e o `.exe` usa o ícone padrão do PyInstaller.
