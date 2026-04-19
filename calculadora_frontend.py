#!/usr/bin/env python3
"""
Frontend desktop (Tkinter) para a calculadora de estimativas.
Tema dark e selecao discreta de 0 a 5 para melhor usabilidade.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict

from calculadora_estimativa import (
    ANALISTAS_TOTAL,
    CRITERIOS,
    calcular_analistas_por_frente,
    calcular_buffer_risco_percentual,
    calcular_horas_base,
    calcular_horas_com_buffer,
    calcular_prazo_dias_uteis,
    calcular_score,
    classificar_complexidade,
    classificar_confianca,
)


def texto_nivel(valor: int) -> str:
    niveis = {
        0: "Nenhum",
        1: "Muito baixo",
        2: "Baixo",
        3: "Moderado",
        4: "Alto",
        5: "Muito alto",
    }
    return niveis.get(valor, "-")


class AppEstimativa:
    BG_APP = "#111827"
    BG_CARD = "#1f2937"
    BG_CARD_SOFT = "#243244"
    TXT_PRI = "#f9fafb"
    TXT_SEC = "#cbd5e1"
    TXT_MUTE = "#94a3b8"
    ACCENT = "#0ea5e9"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Calculadora de Esforco e Tempo")
        self.root.geometry("1200x800")
        self.root.configure(bg=self.BG_APP)

        self.estilo = ttk.Style()
        self.estilo.theme_use("clam")
        self.estilo.configure("TFrame", background=self.BG_APP)
        self.estilo.configure("Card.TFrame", background=self.BG_CARD)
        self.estilo.configure("SoftCard.TFrame", background=self.BG_CARD_SOFT)
        self.estilo.configure(
            "Titulo.TLabel",
            background=self.BG_CARD,
            foreground=self.TXT_PRI,
            font=("Segoe UI", 14, "bold"),
        )
        self.estilo.configure(
            "Texto.TLabel",
            background=self.BG_CARD,
            foreground=self.TXT_SEC,
            font=("Segoe UI", 10),
        )
        self.estilo.configure(
            "Dica.TLabel",
            background=self.BG_CARD,
            foreground=self.TXT_MUTE,
            font=("Segoe UI", 9),
        )
        self.estilo.configure(
            "Resultado.TLabel",
            background=self.BG_CARD,
            foreground=self.TXT_PRI,
            font=("Segoe UI", 11, "bold"),
        )
        self.estilo.configure(
            "Primary.TButton",
            background=self.ACCENT,
            foreground="#08121a",
            borderwidth=0,
            focusthickness=0,
            font=("Segoe UI", 10, "bold"),
            padding=(10, 7),
        )
        self.estilo.map(
            "Primary.TButton",
            background=[("active", "#38bdf8")],
        )
        self.estilo.configure(
            "Ghost.TButton",
            background=self.BG_CARD_SOFT,
            foreground=self.TXT_PRI,
            borderwidth=0,
            focusthickness=0,
            font=("Segoe UI", 10),
            padding=(10, 7),
        )
        self.estilo.map(
            "Ghost.TButton",
            background=[("active", "#334155")],
        )

        self.vars_notas: Dict[str, tk.IntVar] = {}
        self.labels_nivel: Dict[str, ttk.Label] = {}

        self._montar_layout()

    def _montar_layout(self) -> None:
        container = ttk.Frame(self.root, padding=18)
        container.pack(fill="both", expand=True)

        cabecalho = ttk.Frame(container, style="Card.TFrame", padding=16)
        cabecalho.pack(fill="x", pady=(0, 12))

        ttk.Label(
            cabecalho,
            text="Estimativa de Esforco para Demandas",
            style="Titulo.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            cabecalho,
            text=(
                "Preencha cada criterio de 0 a 5 para gerar uma previsao "
                "mais realista de horas e nivel de confianca."
            ),
            style="Texto.TLabel",
        ).pack(anchor="w", pady=(6, 0))
        ttk.Label(
            cabecalho,
            text="Dica: use os presets para estimar mais rapido.",
            style="Dica.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        area_principal = ttk.Frame(container)
        area_principal.pack(fill="both", expand=True)

        criterios_card = ttk.Frame(
            area_principal,
            style="Card.TFrame",
            padding=16,
        )
        criterios_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        ttk.Label(
            criterios_card,
            text="Criterios",
            style="Titulo.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            criterios_card,
            text="Escala: 0 Nenhum | 3 Moderado | 5 Muito alto",
            style="Dica.TLabel",
        ).pack(anchor="w", pady=(2, 12))

        atalho = ttk.Frame(criterios_card, style="Card.TFrame")
        atalho.pack(fill="x", pady=(0, 12))
        ttk.Button(
            atalho,
            text="Preset Baixo (1)",
            style="Ghost.TButton",
            command=lambda: self.aplicar_preset(1),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            atalho,
            text="Preset Medio (3)",
            style="Ghost.TButton",
            command=lambda: self.aplicar_preset(3),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            atalho,
            text="Preset Alto (4)",
            style="Ghost.TButton",
            command=lambda: self.aplicar_preset(4),
        ).pack(side="left")

        area_scroll = ttk.Frame(criterios_card, style="Card.TFrame")
        area_scroll.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            area_scroll,
            bg=self.BG_CARD,
            highlightthickness=0,
            borderwidth=0,
        )
        barra = ttk.Scrollbar(
            area_scroll,
            orient="vertical",
            command=self.canvas.yview,
        )
        lista_criterios = ttk.Frame(self.canvas, style="Card.TFrame")

        lista_criterios.bind(
            "<Configure>",
            lambda event: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            ),
        )
        self.canvas.create_window((0, 0), window=lista_criterios, anchor="nw")
        self.canvas.configure(yscrollcommand=barra.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        for criterio in CRITERIOS:
            bloco = ttk.Frame(
                lista_criterios,
                style="SoftCard.TFrame",
                padding=10,
            )
            bloco.pack(fill="x", pady=6)

            ttk.Label(
                bloco,
                text=f"{criterio.nome_exibicao} (peso {criterio.peso})",
                style="Texto.TLabel",
            ).pack(anchor="w", pady=(0, 2))
            ttk.Label(
                bloco,
                text=criterio.descricao,
                style="Dica.TLabel",
            ).pack(anchor="w")

            var = tk.IntVar(value=0)
            self.vars_notas[criterio.chave] = var

            seletor = ttk.Frame(bloco, style="SoftCard.TFrame")
            seletor.pack(anchor="w", pady=(8, 0))

            for valor in range(6):
                radio = tk.Radiobutton(
                    seletor,
                    text=str(valor),
                    variable=var,
                    value=valor,
                    indicatoron=0,
                    width=3,
                    command=lambda chave=criterio.chave: (
                        self._atualizar_texto_nivel(chave)
                    ),
                    bg="#334155",
                    fg="#e2e8f0",
                    activebackground="#475569",
                    activeforeground="#f8fafc",
                    selectcolor="#0ea5e9",
                    font=("Segoe UI", 9, "bold"),
                    relief="flat",
                    padx=6,
                    pady=3,
                    highlightthickness=0,
                    bd=0,
                )
                radio.pack(side="left", padx=(0, 6))

            nivel_label = ttk.Label(
                bloco,
                text="Nivel selecionado: 0 (Nenhum)",
                style="Dica.TLabel",
            )
            nivel_label.pack(anchor="w", pady=(8, 0))
            self.labels_nivel[criterio.chave] = nivel_label

        botoes = ttk.Frame(criterios_card, style="Card.TFrame")
        botoes.pack(fill="x", pady=(12, 0))

        ttk.Button(
            botoes,
            text="Calcular estimativa",
            style="Primary.TButton",
            command=self.calcular,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            botoes,
            text="Limpar",
            style="Ghost.TButton",
            command=self.limpar,
        ).pack(side="left")

        resultado_card = ttk.Frame(
            area_principal,
            style="Card.TFrame",
            padding=16,
        )
        resultado_card.pack(side="right", fill="y", padx=(8, 0))

        ttk.Label(
            resultado_card,
            text="Resultado",
            style="Titulo.TLabel",
        ).pack(anchor="w")

        self.var_score = tk.StringVar(value="Score: -")
        self.var_complexidade = tk.StringVar(value="Complexidade: -")
        self.var_horas_base = tk.StringVar(value="Horas base: -")
        self.var_buffer = tk.StringVar(value="Buffer de risco: -")
        self.var_confianca = tk.StringVar(value="Confianca: -")
        self.var_horas_finais = tk.StringVar(value="Horas finais: -")
        self.var_prazo_frente = tk.StringVar(value="Prazo (1 analista): -")
        self.var_prazo_apoio = tk.StringVar(value="Prazo (2 analistas): -")

        for variavel in [
            self.var_score,
            self.var_complexidade,
            self.var_horas_base,
            self.var_buffer,
            self.var_confianca,
            self.var_horas_finais,
            self.var_prazo_frente,
            self.var_prazo_apoio,
        ]:
            ttk.Label(
                resultado_card,
                textvariable=variavel,
                style="Resultado.TLabel",
            ).pack(anchor="w", pady=4)

        linha = tk.Frame(resultado_card, bg="#374151", height=1)
        linha.pack(fill="x", pady=10)

        self.var_recomendacao = tk.StringVar(
            value=(
                "Recomendacao: use este resultado como baseline e some "
                "contexto de capacidade do time na sprint."
            )
        )
        ttk.Label(
            resultado_card,
            textvariable=self.var_recomendacao,
            style="Dica.TLabel",
            wraplength=260,
            justify="left",
        ).pack(anchor="w")

        self.canvas.bind_all(
            "<MouseWheel>",
            lambda event: self.canvas.yview_scroll(
                int(-event.delta / 120),
                "units",
            ),
        )

    def _atualizar_texto_nivel(self, chave: str) -> None:
        valor = self.vars_notas[chave].get()
        self.labels_nivel[chave].configure(
            text=f"Nivel selecionado: {valor} ({texto_nivel(valor)})"
        )

    def _capturar_notas(self) -> Dict[str, int]:
        notas: Dict[str, int] = {}
        for criterio in CRITERIOS:
            notas[criterio.chave] = max(
                0,
                min(5, self.vars_notas[criterio.chave].get()),
            )
        return notas

    def aplicar_preset(self, valor: int) -> None:
        for criterio in CRITERIOS:
            self.vars_notas[criterio.chave].set(valor)
            self._atualizar_texto_nivel(criterio.chave)

    def calcular(self) -> None:
        notas = self._capturar_notas()
        score = calcular_score(notas)
        horas_base = calcular_horas_base(score)
        buffer_pct = calcular_buffer_risco_percentual(notas)
        horas_finais = calcular_horas_com_buffer(horas_base, buffer_pct)
        analistas_frente = calcular_analistas_por_frente()
        prazo_frente = calcular_prazo_dias_uteis(
            horas_finais,
            analistas_frente,
        )
        prazo_apoio = calcular_prazo_dias_uteis(horas_finais, ANALISTAS_TOTAL)

        self.var_score.set(f"Score: {score:.1f}/100")
        self.var_complexidade.set(
            f"Complexidade: {classificar_complexidade(score)}"
        )
        self.var_horas_base.set(f"Horas base: {horas_base:.1f}h")
        self.var_buffer.set(f"Buffer de risco: {buffer_pct * 100:.0f}%")
        self.var_confianca.set(
            f"Confianca da estimativa: {classificar_confianca(buffer_pct)}"
        )
        self.var_horas_finais.set(
            f"Horas finais sugeridas: {horas_finais:.1f}h"
        )
        self.var_prazo_frente.set(
            f"Prazo (1 analista na frente): {prazo_frente:.1f} dias"
        )
        self.var_prazo_apoio.set(
            f"Prazo (2 analistas com apoio): {prazo_apoio:.1f} dias"
        )

    def limpar(self) -> None:
        for criterio in CRITERIOS:
            self.vars_notas[criterio.chave].set(0)
            self._atualizar_texto_nivel(criterio.chave)

        self.var_score.set("Score: -")
        self.var_complexidade.set("Complexidade: -")
        self.var_horas_base.set("Horas base: -")
        self.var_buffer.set("Buffer de risco: -")
        self.var_confianca.set("Confianca: -")
        self.var_horas_finais.set("Horas finais: -")
        self.var_prazo_frente.set("Prazo (1 analista): -")
        self.var_prazo_apoio.set("Prazo (2 analistas): -")


def main() -> None:
    root = tk.Tk()
    AppEstimativa(root)
    root.mainloop()


if __name__ == "__main__":
    main()
