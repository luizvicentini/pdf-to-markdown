"""Entry point — instancia a janela principal."""
from app import PdfToMarkdownApp


def main():
    app = PdfToMarkdownApp()
    app.mainloop()


if __name__ == "__main__":
    main()
