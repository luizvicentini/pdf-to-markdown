# PDF → Markdown

Aplicativo desktop Windows em Python que converte PDFs nativos, arquivos `.txt` e `.docx` em Markdown bem estruturado, preservando ao máximo a formatação original (títulos, listas, tabelas, negrito e itálico).

## Requisitos

- Windows 10/11
- Python 3.10 ou superior

## Instalação

```powershell
# 1. Clone ou copie o diretório
cd pdf_to_markdown

# 2. (Opcional, recomendado) Crie um ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instale as dependências fixadas
pip install -r requirements.txt
```

## Execução

```powershell
python main.py
```

Na primeira execução o arquivo `config.json` é criado automaticamente no diretório do projeto. Ele guarda o último modo escolhido e a última `ANTHROPIC_API_KEY` digitada.

## Modos de operação

O aplicativo possui dois modos selecionáveis pelo toggle switch na interface:

### Modo Local (sem API)

- Funciona totalmente offline, sem chamadas externas.
- Usa PyMuPDF para analisar blocos do PDF e detectar hierarquia de títulos pelo tamanho relativo da fonte (até 3 níveis).
- Detecta listas (`•`, `-`, `*`, padrões numéricos `1.` ou `1)`), tabelas via `page.find_tables()`, negrito/itálico pelas flags de fonte.
- Remove hifenização de fim de linha, espaços duplicados, e cabeçalhos/rodapés que se repetem em 3+ páginas consecutivas.

### Modo API (Anthropic)

- Envia o texto extraído (com marcadores estruturais) para o modelo `claude-sonnet-4-20250514`.
- Documentos com mais de ~15.000 tokens são divididos em chunks por seção (preferência por quebra em headings) e processados sequencialmente; o resultado é concatenado preservando hierarquia.
- O label de status mostra o total de tokens consumidos ao final.
- A `ANTHROPIC_API_KEY` é solicitada apenas quando esse modo está ativo. Ela é armazenada em `config.json` (que **não** deve ser versionado) e nunca aparece em logs, prints ou títulos de janela.

## Formatos de entrada suportados

- `.pdf` — PDFs com texto selecionável (nativos). PDFs escaneados (somente imagem) não são suportados; passe-os por OCR externo (Tesseract, Adobe Acrobat etc.) antes de converter.
- `.txt` — UTF-8 ou Latin-1.
- `.docx` — qualquer arquivo Word moderno.

## Mensagens de erro mais comuns

- **PDF protegido por senha** — remova a proteção antes de converter.
- **PDF sem texto selecionável** — execute OCR externo primeiro.
- **API key não configurada** — alterne para o modo local ou insira sua chave no campo correspondente.

## Estrutura do projeto

```
pdf_to_markdown/
├── main.py              # Entry point
├── app.py               # Interface CustomTkinter
├── extractor.py         # Extração de PDF/TXT/DOCX
├── converter_local.py   # Conversão algorítmica
├── converter_api.py     # Integração com API Anthropic
├── config.py            # Leitura/escrita de config.json
├── utils.py             # Helpers
├── config.json          # Criado automaticamente (gitignored)
├── .gitignore
├── requirements.txt
└── README.md
```


