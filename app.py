"""
Interface principal CustomTkinter.
Tema dark, ~900x650, drag-and-drop, toggle Local/API, preview, salvar/copiar.
"""
import os
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

import pyperclip

from config import load_config, save_config
from converter_api import APIError, convert_api
from converter_local import convert_local
from extractor import ExtractionError, extract_any


# Mistura CTk com TkinterDnD para habilitar drag-and-drop em janela CustomTkinter
if DND_AVAILABLE:
    class CTkDnD(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)
    BaseRoot = CTkDnD
else:
    BaseRoot = ctk.CTk


class PdfToMarkdownApp(BaseRoot):
    """Janela principal do conversor."""

    SUPPORTED_EXTS = {".pdf", ".txt", ".docx"}

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("PDF → Markdown")
        self.geometry("900x650")
        self.minsize(800, 580)

        self.config_data = load_config()
        self.current_file: str | None = None
        self.current_markdown: str = ""

        self._build_ui()
        self._apply_initial_state()

    # ----------------------------- UI -----------------------------

    def _build_ui(self):
        """Constrói layout da janela."""
        # Grid raiz: linha 0 toolbar, linha 1 área central, linha 2 botões inferiores, linha 3 status
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ---- Toolbar superior ----
        top = ctk.CTkFrame(self, corner_radius=0)
        top.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        top.grid_columnconfigure(3, weight=1)

        self.btn_open = ctk.CTkButton(top, text="Abrir arquivo", width=140, command=self._on_open_file)
        self.btn_open.grid(row=0, column=0, padx=12, pady=12)

        self.mode_label = ctk.CTkLabel(top, text="Modo:")
        self.mode_label.grid(row=0, column=1, padx=(20, 4), pady=12)

        self.mode_var = ctk.StringVar(value="local")
        self.mode_switch = ctk.CTkSwitch(
            top,
            text="Modo Local",
            command=self._on_mode_toggle,
            variable=self.mode_var,
            onvalue="api",
            offvalue="local",
        )
        self.mode_switch.grid(row=0, column=2, padx=4, pady=12)

        self.api_label = ctk.CTkLabel(top, text="ANTHROPIC_API_KEY:")
        self.api_entry = ctk.CTkEntry(top, show="•", width=300, placeholder_text="sk-ant-...")
        self.api_label.grid(row=0, column=4, padx=(20, 4), pady=12, sticky="e")
        self.api_entry.grid(row=0, column=5, padx=(0, 12), pady=12, sticky="e")

        # ---- Área central: drop zone + preview ----
        center = ctk.CTkFrame(self)
        center.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 6))
        center.grid_columnconfigure(0, weight=1)
        center.grid_rowconfigure(1, weight=1)

        self.drop_zone = ctk.CTkFrame(center, height=80, fg_color=("gray85", "gray20"), corner_radius=8)
        self.drop_zone.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        self.drop_zone.grid_propagate(False)
        self.drop_zone.grid_columnconfigure(0, weight=1)
        self.drop_zone.grid_rowconfigure(0, weight=1)
        self.drop_label = ctk.CTkLabel(
            self.drop_zone,
            text=self._drop_label_text(),
            font=ctk.CTkFont(size=13),
        )
        self.drop_label.grid(row=0, column=0, sticky="nsew")

        if DND_AVAILABLE:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<Drop>>", self._on_drop)
            self.drop_label.drop_target_register(DND_FILES)
            self.drop_label.dnd_bind("<<Drop>>", self._on_drop)

        # Preview
        self.preview = ctk.CTkTextbox(center, wrap="word", font=ctk.CTkFont(family="Consolas", size=12))
        self.preview.grid(row=1, column=0, sticky="nsew", padx=8, pady=(2, 8))
        self.preview.configure(state="disabled")

        # ---- Linha de progresso + botões ----
        bottom = ctk.CTkFrame(self, corner_radius=0)
        bottom.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        bottom.grid_columnconfigure(0, weight=1)

        self.progress = ctk.CTkProgressBar(bottom)
        self.progress.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        self.progress.set(0.0)

        btn_row = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_row.grid(row=1, column=0, sticky="e", padx=12, pady=(0, 10))
        self.btn_save = ctk.CTkButton(btn_row, text="Salvar .md", width=140, command=self._on_save, state="disabled")
        self.btn_save.grid(row=0, column=0, padx=(0, 8))
        self.btn_copy = ctk.CTkButton(btn_row, text="Copiar para área de transferência", width=240, command=self._on_copy, state="disabled")
        self.btn_copy.grid(row=0, column=1)

        # ---- Status ----
        self.status_label = ctk.CTkLabel(self, text="Pronto.", anchor="w")
        self.status_label.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 10))

    def _drop_label_text(self) -> str:
        if DND_AVAILABLE:
            return "Arraste e solte aqui um arquivo .pdf, .txt ou .docx — ou use “Abrir arquivo”"
        return "Drag-and-drop indisponível (instale tkinterdnd2). Use “Abrir arquivo”"

    def _apply_initial_state(self):
        """Aplica config carregada à interface."""
        mode = self.config_data.get("mode", "local")
        api_key = self.config_data.get("api_key", "")

        if mode == "api":
            self.mode_switch.select()
            self.mode_var.set("api")
        else:
            self.mode_switch.deselect()
            self.mode_var.set("local")

        if api_key:
            self.api_entry.insert(0, api_key)

        self._update_api_field_visibility()

    # ----------------------------- Eventos -----------------------------

    def _on_mode_toggle(self):
        """Alterna entre Local e API."""
        mode = self.mode_var.get()
        self.mode_switch.configure(text="Modo API" if mode == "api" else "Modo Local")
        self._update_api_field_visibility()
        self._persist_config()

    def _update_api_field_visibility(self):
        """Mostra/oculta campo de API key conforme modo ativo."""
        mode = self.mode_var.get()
        if mode == "api":
            self.api_label.grid()
            self.api_entry.grid()
            self.api_entry.configure(state="normal")
        else:
            self.api_label.grid_remove()
            self.api_entry.grid_remove()

    def _on_open_file(self):
        """Abre file dialog para escolher arquivo de entrada."""
        path = filedialog.askopenfilename(
            title="Selecione um arquivo",
            filetypes=[
                ("Arquivos suportados", "*.pdf *.txt *.docx"),
                ("PDF", "*.pdf"),
                ("Texto", "*.txt"),
                ("Word", "*.docx"),
            ],
        )
        if path:
            self._start_conversion(path)

    def _on_drop(self, event):
        """Handler de drag-and-drop."""
        raw = event.data
        # tkinterdnd2 pode entregar caminhos com chaves quando há espaços
        path = raw.strip()
        if path.startswith("{") and path.endswith("}"):
            path = path[1:-1]
        # Se múltiplos arquivos, pega o primeiro
        if " " in path and Path(path).suffix == "":
            path = path.split(" ")[0]

        ext = Path(path).suffix.lower()
        if ext not in self.SUPPORTED_EXTS:
            messagebox.showwarning("Formato não suportado", f"Extensão {ext} não é aceita.")
            return
        self._start_conversion(path)

    def _on_save(self):
        """Salva markdown atual em arquivo .md."""
        if not self.current_markdown:
            return
        default_name = "saida.md"
        if self.current_file:
            default_name = Path(self.current_file).stem + ".md"
        initial_dir = str(Path(self.current_file).parent) if self.current_file else os.getcwd()
        target = filedialog.asksaveasfilename(
            title="Salvar Markdown",
            defaultextension=".md",
            initialdir=initial_dir,
            initialfile=default_name,
            filetypes=[("Markdown", "*.md"), ("Todos os arquivos", "*.*")],
        )
        if not target:
            return
        try:
            Path(target).write_text(self.current_markdown, encoding="utf-8")
            self._set_status(f"Salvo: {target}")
        except OSError as exc:
            messagebox.showerror("Erro ao salvar", str(exc))

    def _on_copy(self):
        """Copia markdown atual para área de transferência."""
        if not self.current_markdown:
            return
        try:
            pyperclip.copy(self.current_markdown)
            self._set_status("Copiado para a área de transferência.")
        except Exception as exc:  # pyperclip pode falhar em ambiente sem clipboard
            messagebox.showerror("Erro ao copiar", str(exc))

    # ----------------------------- Conversão -----------------------------

    def _start_conversion(self, path: str):
        """Dispara conversão em thread para não congelar a UI."""
        self.current_file = path
        self.current_markdown = ""
        self._set_preview("")
        self.btn_save.configure(state="disabled")
        self.btn_copy.configure(state="disabled")
        self.btn_open.configure(state="disabled")
        self.progress.set(0.0)
        self.progress.start()
        self._set_status(f"Processando: {Path(path).name} ...")

        mode = self.mode_var.get()
        api_key = self.api_entry.get().strip() if mode == "api" else ""
        self._persist_config()

        thread = threading.Thread(
            target=self._run_conversion,
            args=(path, mode, api_key),
            daemon=True,
        )
        thread.start()

    def _run_conversion(self, path: str, mode: str, api_key: str):
        """Executado em thread separada. Não toca widgets diretamente — usa after()."""
        try:
            blocks = extract_any(path)

            if mode == "api":
                def progress_cb(done, total):
                    if total > 0:
                        frac = done / total
                        self.after(0, lambda: self._set_progress(frac))
                md, tokens = convert_api(blocks, api_key, progress_cb=progress_cb)
                status = f"Concluído — {tokens} tokens usados"
            else:
                md = convert_local(blocks)
                tokens = 0
                status = "Concluído (modo local)"

            self.after(0, lambda: self._on_conversion_success(md, status))
        except ExtractionError as exc:
            self.after(0, lambda e=exc: self._on_conversion_error(str(e)))
        except APIError as exc:
            # Garante que API key não vaze na mensagem
            msg = str(exc)
            if api_key and api_key in msg:
                msg = msg.replace(api_key, "[REDACTED]")
            self.after(0, lambda m=msg: self._on_conversion_error(m))
        except Exception as exc:
            msg = str(exc)
            if api_key and api_key in msg:
                msg = msg.replace(api_key, "[REDACTED]")
            self.after(0, lambda m=msg: self._on_conversion_error(f"Erro inesperado: {m}"))

    def _on_conversion_success(self, markdown: str, status: str):
        """Callback no thread principal — atualiza UI após sucesso."""
        self.progress.stop()
        self.progress.set(1.0)
        self.current_markdown = markdown
        self._set_preview(markdown)
        self.btn_save.configure(state="normal")
        self.btn_copy.configure(state="normal")
        self.btn_open.configure(state="normal")
        self._set_status(status)

    def _on_conversion_error(self, message: str):
        """Callback no thread principal — atualiza UI após erro."""
        self.progress.stop()
        self.progress.set(0.0)
        self.btn_open.configure(state="normal")
        self._set_status(f"Erro: {message}")
        messagebox.showerror("Erro", message)

    # ----------------------------- Helpers de UI -----------------------------

    def _set_preview(self, text: str):
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)
        self.preview.configure(state="disabled")

    def _set_progress(self, frac: float):
        self.progress.stop()
        self.progress.set(max(0.0, min(1.0, frac)))

    def _set_status(self, msg: str):
        self.status_label.configure(text=msg)

    def _persist_config(self):
        """Salva modo atual e API key em config.json."""
        self.config_data["mode"] = self.mode_var.get()
        self.config_data["api_key"] = self.api_entry.get().strip()
        save_config(self.config_data)
