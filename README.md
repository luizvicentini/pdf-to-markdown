# PDF to Markdown

Converte PDFs nativos, `.txt` e `.docx` em Markdown. Interface gráfica, sem terminal.

## Download

Pegue o `.zip` em [Releases](https://github.com/luizvicentini/pdf-to-markdown/releases/latest), extraia e execute `PDF-to-Markdown.exe`. Não precisa instalar Python.

> Windows pode avisar "fabricante desconhecido" — clique em **Mais informações → Executar assim mesmo**.

## Uso

1. Arraste o arquivo na janela ou clique em **Abrir arquivo**.
2. Escolha o modo:
   - **Local** — conversão offline.
   - **API** — usa Claude (precisa de chave Anthropic).
3. **Salvar .md** ou **Copiar**.

PDFs escaneados (sem texto selecionável) precisam de OCR antes.

## Rodar a partir do código

```powershell
git clone https://github.com/luizvicentini/pdf-to-markdown.git
cd pdf-to-markdown
pip install -r requirements.txt
python main.py
```

## Gerar o `.exe`

```powershell
.\build.bat
```

Saída em `dist\PDF-to-Markdown\`. Para um ícone próprio, coloque `assets\icon.ico` antes de buildar.
