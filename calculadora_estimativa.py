#!/usr/bin/env python3
"""
Calculadora de esforco/tempo para estimativas de demandas.
Escala por criterio: 0 (nenhum esforco) a 5 (muito esforco).

Modelo:
- Score de esforco (0-100) baseado em criterios ponderados.
- Horas base calculadas pelo score.
- Buffer de risco para refletir incerteza e dependencias.

Contexto operacional padrao:
- Time com 2 analistas.
- 2 frentes de atuacao em paralelo (1 analista por frente).
- Atividade principal de suporte/debug em servico SOAP construido em C#.
- Analise com consultas SQL manuais (sem analise de logs de servidor).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


ANALISTAS_TOTAL = 2
FRENTES_ATIVAS = 2
HORAS_PRODUTIVAS_DIA_ANALISTA = 8.0


@dataclass(frozen=True)
class Criterio:
    chave: str
    nome_exibicao: str
    descricao: str
    peso: int
    tipo: str  # esforco | risco


CRITERIOS: List[Criterio] = [
    Criterio(
        "analise_problema_geral",
        "Analise do problema geral",
        "Nivel de investigacao para entender causa raiz e impacto.",
        20,
        "esforco",
    ),
    Criterio(
        "investigacao_sql_manual",
        "Investigacao SQL manual",
        (
            "Esforco de consultas SQL para validar dados "
            "e rastrear inconsistencias."
        ),
        20,
        "esforco",
    ),
    Criterio(
        "debug_servico_csharp",
        "Complexidade de debug no servico C#",
        "Dificuldade de reproduzir e corrigir no servico SOAP em C#.",
        25,
        "esforco",
    ),
    Criterio(
        "testes_servico_soap",
        "Esforco de testes no servico SOAP",
        "Volume de testes manuais e validacoes fim a fim apos ajustes.",
        15,
        "esforco",
    ),
    Criterio(
        "dependencias_externas",
        "Dependencias externas",
        "Bloqueios por terceiros e integracoes fora do controle da frente.",
        10,
        "risco",
    ),
    Criterio(
        "risco_tecnico",
        "Incerteza tecnica",
        "Risco de retrabalho por baixa previsibilidade da solucao.",
        10,
        "risco",
    ),
]


def ler_nota(nome_criterio: str) -> int:
    while True:
        entrada = input(f"{nome_criterio} (0 a 5): ").strip().replace(",", ".")
        if not entrada:
            print("Informe um valor entre 0 e 5.")
            continue

        try:
            valor = float(entrada)
        except ValueError:
            print("Valor invalido. Digite um numero de 0 a 5.")
            continue

        if valor.is_integer() and 0 <= int(valor) <= 5:
            return int(valor)

        print("Use apenas inteiros de 0 a 5.")


def calcular_score(notas: Dict[str, int]) -> float:
    soma_ponderada = 0
    for criterio in CRITERIOS:
        soma_ponderada += notas[criterio.chave] * criterio.peso

    return soma_ponderada / 5.0


def calcular_horas_base(
    score: float,
    base_horas: float = 2.0,
    fator: float = 0.60,
) -> float:
    return base_horas + (score * fator)


def calcular_buffer_risco_percentual(notas: Dict[str, int]) -> float:
    notas_risco = [
        notas[criterio.chave]
        for criterio in CRITERIOS
        if criterio.tipo == "risco"
    ]
    media_risco = sum(notas_risco) / len(notas_risco)

    # Buffer entre 8% e 35% para refletir incerteza da demanda.
    return 0.08 + ((media_risco / 5.0) * 0.27)


def calcular_horas_com_buffer(
    horas_base: float,
    buffer_percentual: float,
) -> float:
    return horas_base * (1 + buffer_percentual)


def calcular_analistas_por_frente() -> float:
    return ANALISTAS_TOTAL / FRENTES_ATIVAS


def calcular_prazo_dias_uteis(
    horas_finais: float,
    analistas_disponiveis: float,
    horas_dia_por_analista: float = HORAS_PRODUTIVAS_DIA_ANALISTA,
) -> float:
    capacidade_dia = analistas_disponiveis * horas_dia_por_analista
    return horas_finais / capacidade_dia


def classificar_complexidade(score: float) -> str:
    if score <= 20:
        return "Muito baixa"
    if score <= 40:
        return "Baixa"
    if score <= 60:
        return "Media"
    if score <= 80:
        return "Alta"
    return "Muito alta"


def classificar_confianca(buffer_percentual: float) -> str:
    if buffer_percentual <= 0.16:
        return "Alta"
    if buffer_percentual <= 0.24:
        return "Media"
    return "Baixa"


def imprimir_resumo(
    notas: Dict[str, int],
    score: float,
    horas_base: float,
    buffer_percentual: float,
    horas_finais: float,
    prazo_dias_frente: float,
    prazo_dias_apoio: float,
) -> None:
    print("\nResumo da estimativa")
    print("-" * 70)
    for criterio in CRITERIOS:
        print(
            f"{criterio.nome_exibicao:<35} "
            f"nota={notas[criterio.chave]}  peso={criterio.peso}"
        )

    print("-" * 70)
    print(f"Score ponderado (0-100): {score:.1f}")
    print(f"Complexidade: {classificar_complexidade(score)}")
    print(f"Horas base: {horas_base:.1f}h")
    print(f"Buffer de risco: {buffer_percentual * 100:.0f}%")
    print(
        f"Confianca da estimativa: "
        f"{classificar_confianca(buffer_percentual)}"
    )
    print(f"Horas estimadas (com buffer): {horas_finais:.1f}h")
    print(
        f"Prazo estimado (1 analista na frente): "
        f"{prazo_dias_frente:.1f} dias uteis"
    )
    print(
        f"Prazo com apoio da outra frente (2 analistas): "
        f"{prazo_dias_apoio:.1f} dias uteis"
    )


def main() -> None:
    print("Calculadora de estimativa de esforco/tempo")
    print("Escala: 0 (nenhum esforco) a 5 (muito esforco)\n")
    print(
        "Contexto aplicado: 2 analistas, 2 frentes, "
        "sem analise de logs de servidor.\n"
    )

    notas: Dict[str, int] = {}
    for criterio in CRITERIOS:
        notas[criterio.chave] = ler_nota(criterio.nome_exibicao)

    score = calcular_score(notas)
    horas_base = calcular_horas_base(score)
    buffer_percentual = calcular_buffer_risco_percentual(notas)
    horas_finais = calcular_horas_com_buffer(horas_base, buffer_percentual)
    analistas_frente = calcular_analistas_por_frente()
    prazo_dias_frente = calcular_prazo_dias_uteis(
        horas_finais,
        analistas_frente,
    )
    prazo_dias_apoio = calcular_prazo_dias_uteis(horas_finais, ANALISTAS_TOTAL)

    imprimir_resumo(
        notas,
        score,
        horas_base,
        buffer_percentual,
        horas_finais,
        prazo_dias_frente,
        prazo_dias_apoio,
    )


if __name__ == "__main__":
    main()
