# 💻 Exemplos de Código - Fase 1 (Persistência)

## 1. Schema SQLite

### arquivo: `persistencia.py`

```python
"""
Módulo de persistência com SQLite.
Responsável por salvar, carregar e atualizar estimativas.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Definir caminho do banco
DB_PATH = Path(__file__).parent.parent / "data" / "estimativas.db"


@dataclass
class EstimativaRecord:
    """Representa uma estimativa persistida."""
    id: Optional[int] = None
    demanda: str = ""
    responsavel: str = ""
    data_criacao: str = ""  # ISO format
    versao_modelo: str = "1.0"
    notas: str = ""  # JSON string
    score: float = 0.0
    horas_base: float = 0.0
    buffer_risco: float = 0.0
    horas_finais: float = 0.0
    prazo_dias_frente: float = 0.0
    prazo_dias_apoio: float = 0.0
    status: str = "planejado"  # planejado|em_progresso|concluido|cancelado
    horas_reais: Optional[float] = None
    dias_reais: Optional[int] = None
    observacoes: str = ""
    data_atualizacao: str = ""  # ISO format


class PersistenciaEstimativas:
    """Gerencia persistência de estimativas em SQLite."""
    
    # SQL DDL para criar tabelas
    SQL_CREATE_ESTIMATIVAS = """
    CREATE TABLE IF NOT EXISTS estimativas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        demanda TEXT NOT NULL,
        responsavel TEXT NOT NULL,
        data_criacao TEXT NOT NULL,
        versao_modelo TEXT NOT NULL,
        notas TEXT NOT NULL,  -- JSON: {analise: 3, sql: 2, ...}
        score REAL NOT NULL,
        horas_base REAL NOT NULL,
        buffer_risco REAL NOT NULL,
        horas_finais REAL NOT NULL,
        prazo_dias_frente REAL NOT NULL,
        prazo_dias_apoio REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'planejado',
        horas_reais REAL,
        dias_reais INTEGER,
        observacoes TEXT,
        data_atualizacao TEXT NOT NULL,
        UNIQUE(demanda, responsavel, data_criacao)
    )
    """
    
    SQL_CREATE_MODELO_VERSOES = """
    CREATE TABLE IF NOT EXISTS modelo_versoes (
        versao TEXT PRIMARY KEY,
        data_criacao TEXT NOT NULL,
        criterios TEXT NOT NULL,  -- JSON: lista de critérios e pesos
        notas TEXT,  -- Motivo da mudança
        UNIQUE(versao)
    )
    """
    
    SQL_CREATE_INDICES = """
    CREATE INDEX IF NOT EXISTS idx_responsavel ON estimativas(responsavel);
    CREATE INDEX IF NOT EXISTS idx_status ON estimativas(status);
    CREATE INDEX IF NOT EXISTS idx_data_criacao ON estimativas(data_criacao);
    """
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar_db()
    
    def _inicializar_db(self) -> None:
        """Cria tabelas se não existirem."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(self.SQL_CREATE_ESTIMATIVAS)
        cursor.execute(self.SQL_CREATE_MODELO_VERSOES)
        cursor.execute(self.SQL_CREATE_INDICES)
        
        conn.commit()
        conn.close()
    
    def salvar_estimativa(
        self,
        demanda: str,
        responsavel: str,
        notas: Dict[str, int],
        score: float,
        horas_base: float,
        buffer_risco: float,
        horas_finais: float,
        prazo_dias_frente: float,
        prazo_dias_apoio: float,
        versao_modelo: str = "1.0",
    ) -> int:
        """Salva uma nova estimativa. Retorna o ID."""
        agora = datetime.now().isoformat()
        notas_json = json.dumps(notas)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO estimativas (
                demanda, responsavel, data_criacao, versao_modelo,
                notas, score, horas_base, buffer_risco, horas_finais,
                prazo_dias_frente, prazo_dias_apoio, status, data_atualizacao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                demanda, responsavel, agora, versao_modelo,
                notas_json, score, horas_base, buffer_risco, horas_finais,
                prazo_dias_frente, prazo_dias_apoio, "planejado", agora
            ),
        )
        
        estimativa_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return estimativa_id
    
    def carregar_estimativa(self, estimativa_id: int) -> Optional[EstimativaRecord]:
        """Carrega uma estimativa pelo ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, demanda, responsavel, data_criacao, versao_modelo,
                   notas, score, horas_base, buffer_risco, horas_finais,
                   prazo_dias_frente, prazo_dias_apoio, status, horas_reais,
                   dias_reais, observacoes, data_atualizacao
            FROM estimativas
            WHERE id = ?
            """,
            (estimativa_id,),
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return EstimativaRecord(
            id=row[0],
            demanda=row[1],
            responsavel=row[2],
            data_criacao=row[3],
            versao_modelo=row[4],
            notas=row[5],
            score=row[6],
            horas_base=row[7],
            buffer_risco=row[8],
            horas_finais=row[9],
            prazo_dias_frente=row[10],
            prazo_dias_apoio=row[11],
            status=row[12],
            horas_reais=row[13],
            dias_reais=row[14],
            observacoes=row[15],
            data_atualizacao=row[16],
        )
    
    def listar_estimativas(
        self,
        responsavel: Optional[str] = None,
        status: Optional[str] = None,
        limite: int = 100,
    ) -> List[EstimativaRecord]:
        """Lista estimativas com filtros opcionais."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM estimativas WHERE 1=1"
        params = []
        
        if responsavel:
            query += " AND responsavel = ?"
            params.append(responsavel)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY data_criacao DESC LIMIT ?"
        params.append(limite)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_para_record(row) for row in rows]
    
    def atualizar_resultado(
        self,
        estimativa_id: int,
        horas_reais: float,
        dias_reais: int,
        observacoes: str = "",
        status: str = "concluido",
    ) -> bool:
        """Atualiza uma estimativa com resultado real."""
        agora = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            UPDATE estimativas
            SET horas_reais = ?, dias_reais = ?, observacoes = ?,
                status = ?, data_atualizacao = ?
            WHERE id = ?
            """,
            (horas_reais, dias_reais, observacoes, status, agora, estimativa_id),
        )
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return sucesso
    
    def calcular_acuracidade(self, estimativa_id: int) -> Optional[float]:
        """Calcula acuracidade: horas_reais / horas_finais."""
        estimativa = self.carregar_estimativa(estimativa_id)
        
        if not estimativa or estimativa.horas_reais is None:
            return None
        
        return estimativa.horas_reais / estimativa.horas_finais
    
    @staticmethod
    def _row_para_record(row: tuple) -> EstimativaRecord:
        """Converte linha do BD em EstimativaRecord."""
        return EstimativaRecord(
            id=row[0], demanda=row[1], responsavel=row[2],
            data_criacao=row[3], versao_modelo=row[4],
            notas=row[5], score=row[6], horas_base=row[7],
            buffer_risco=row[8], horas_finais=row[9],
            prazo_dias_frente=row[10], prazo_dias_apoio=row[11],
            status=row[12], horas_reais=row[13], dias_reais=row[14],
            observacoes=row[15], data_atualizacao=row[16],
        )
```

---

## 2. Integração com Frontend Tkinter

### Modificações em `calculadora_frontend.py`

```python
# Adicionar no topo do arquivo

from persistencia import PersistenciaEstimativas
from tkinter import messagebox, simpledialog

# Na classe AppEstimativa:

def __init__(self, root: tk.Tk) -> None:
    # ... código existente ...
    self.persistencia = PersistenciaEstimativas()
    # ... resto do init ...

def _montar_layout(self) -> None:
    # ... código existente até seção de botões ...
    
    # ADICIONAR: Area de identificação
    
    identificacao_card = ttk.Frame(
        criterios_card,
        style="SoftCard.TFrame",
        padding=10,
    )
    identificacao_card.pack(fill="x", pady=(0, 12))
    
    ttk.Label(
        identificacao_card,
        text="Identificação",
        style="Texto.TLabel",
    ).pack(anchor="w", pady=(0, 6))
    
    ttk.Label(
        identificacao_card,
        text="Nome da demanda:",
        style="Dica.TLabel",
    ).pack(anchor="w")
    
    self.var_demanda = tk.StringVar()
    entry_demanda = ttk.Entry(
        identificacao_card,
        textvariable=self.var_demanda,
        width=40,
    )
    entry_demanda.pack(anchor="w", pady=(2, 8))
    
    ttk.Label(
        identificacao_card,
        text="Responsável:",
        style="Dica.TLabel",
    ).pack(anchor="w")
    
    self.var_responsavel = tk.StringVar()
    entry_responsavel = ttk.Entry(
        identificacao_card,
        textvariable=self.var_responsavel,
        width=40,
    )
    entry_responsavel.pack(anchor="w", pady=(2, 0))
    
    # ... resto do layout existente ...

def calcular(self) -> None:
    """Calcula e salva a estimativa."""
    # Validações
    if not self.var_demanda.get().strip():
        messagebox.showwarning(
            "Campo obrigatório",
            "Informe o nome da demanda."
        )
        return
    
    if not self.var_responsavel.get().strip():
        messagebox.showwarning(
            "Campo obrigatório",
            "Informe o responsável."
        )
        return
    
    # ... código existente de cálculo ...
    
    # NOVO: Salvar após calcular
    try:
        estimativa_id = self.persistencia.salvar_estimativa(
            demanda=self.var_demanda.get().strip(),
            responsavel=self.var_responsavel.get().strip(),
            notas=notas_dict,
            score=score,
            horas_base=horas_base,
            buffer_risco=buffer_percentual,
            horas_finais=horas_finais,
            prazo_dias_frente=prazo_dias_frente,
            prazo_dias_apoio=prazo_dias_apoio,
        )
        
        messagebox.showinfo(
            "Sucesso",
            f"Estimativa #${estimativa_id} salva com sucesso!"
        )
    except Exception as e:
        messagebox.showerror("Erro ao salvar", str(e))

def listar_historico(self) -> None:
    """Abre janela com histórico de estimativas."""
    janela = tk.Toplevel(self.root)
    janela.title("Histórico de Estimativas")
    janela.geometry("800x400")
    
    # Listar últimas 20
    estimativas = self.persistencia.listar_estimativas(limite=20)
    
    # Criar tabela (simplificado)
    ttk.Label(janela, text="Últimas estimativas:").pack(anchor="w", padx=10, pady=10)
    
    for est in estimativas:
        txt = f"#{est.id}: {est.demanda} ({est.responsavel}) - Score: {est.score:.1f} - Status: {est.status}"
        ttk.Label(janela, text=txt).pack(anchor="w", padx=20, pady=2)
```

---

## 3. Testes Unitários

### arquivo: `tests/test_persistencia.py`

```python
"""Testes para módulo de persistência."""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime

from persistencia import PersistenciaEstimativas, EstimativaRecord


@pytest.fixture
def persistencia(tmp_path):
    """Fixture com BD temporário para testes."""
    db_temp = tmp_path / "test.db"
    return PersistenciaEstimativas(db_path=db_temp)


def test_inicializar_db(persistencia):
    """Testa criação de tabelas."""
    assert persistencia.db_path.exists()
    
    # Verificar que tabelas existem
    conn = sqlite3.connect(persistencia.db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tabelas = {row[0] for row in cursor.fetchall()}
    
    assert "estimativas" in tabelas
    assert "modelo_versoes" in tabelas
    conn.close()


def test_salvar_estimativa(persistencia):
    """Testa salvamento de estimativa."""
    estimativa_id = persistencia.salvar_estimativa(
        demanda="Corrigir erro SOAP",
        responsavel="João",
        notas={"analise": 3, "sql": 2, "debug": 4, "testes": 2, "deps": 1, "risco": 2},
        score=54.0,
        horas_base=34.4,
        buffer_risco=0.18,
        horas_finais=40.6,
        prazo_dias_frente=6.8,
        prazo_dias_apoio=3.4,
    )
    
    assert estimativa_id > 0


def test_carregar_estimativa(persistencia):
    """Testa carregamento de estimativa."""
    # Salvar
    estimativa_id = persistencia.salvar_estimativa(
        demanda="Teste",
        responsavel="Maria",
        notas={"analise": 3, "sql": 2, "debug": 4, "testes": 2, "deps": 1, "risco": 2},
        score=54.0,
        horas_base=34.4,
        buffer_risco=0.18,
        horas_finais=40.6,
        prazo_dias_frente=6.8,
        prazo_dias_apoio=3.4,
    )
    
    # Carregar
    est = persistencia.carregar_estimativa(estimativa_id)
    
    assert est is not None
    assert est.demanda == "Teste"
    assert est.responsavel == "Maria"
    assert est.score == 54.0


def test_atualizar_resultado(persistencia):
    """Testa atualização com resultado real."""
    # Salvar
    estimativa_id = persistencia.salvar_estimativa(
        demanda="Teste",
        responsavel="Pedro",
        notas={"analise": 3, "sql": 2, "debug": 4, "testes": 2, "deps": 1, "risco": 2},
        score=54.0,
        horas_base=34.4,
        buffer_risco=0.18,
        horas_finais=40.6,
        prazo_dias_frente=6.8,
        prazo_dias_apoio=3.4,
    )
    
    # Atualizar com resultado
    sucesso = persistencia.atualizar_resultado(
        estimativa_id=estimativa_id,
        horas_reais=45.0,
        dias_reais=8,
        observacoes="Demorou mais que esperado",
        status="concluido",
    )
    
    assert sucesso
    
    # Verificar
    est = persistencia.carregar_estimativa(estimativa_id)
    assert est.horas_reais == 45.0
    assert est.dias_reais == 8
    assert est.status == "concluido"


def test_calcular_acuracidade(persistencia):
    """Testa cálculo de acuracidade."""
    # Salvar
    estimativa_id = persistencia.salvar_estimativa(
        demanda="Teste",
        responsavel="Ana",
        notas={"analise": 3, "sql": 2, "debug": 4, "testes": 2, "deps": 1, "risco": 2},
        score=54.0,
        horas_base=34.4,
        buffer_risco=0.18,
        horas_finais=40.6,
        prazo_dias_frente=6.8,
        prazo_dias_apoio=3.4,
    )
    
    # Sem resultado real
    assert persistencia.calcular_acuracidade(estimativa_id) is None
    
    # Atualizar com resultado
    persistencia.atualizar_resultado(
        estimativa_id=estimativa_id,
        horas_reais=40.6,
        dias_reais=7,
    )
    
    # Acuracidade = 40.6 / 40.6 = 1.0 (perfeito)
    acuracia = persistencia.calcular_acuracidade(estimativa_id)
    assert abs(acuracia - 1.0) < 0.01


def test_listar_estimativas(persistencia):
    """Testa listagem com filtros."""
    # Salvar várias
    persistencia.salvar_estimativa(
        demanda="Demanda 1", responsavel="João",
        notas={"analise": 3, "sql": 2, "debug": 4, "testes": 2, "deps": 1, "risco": 2},
        score=54.0, horas_base=34.4, buffer_risco=0.18, horas_finais=40.6,
        prazo_dias_frente=6.8, prazo_dias_apoio=3.4,
    )
    persistencia.salvar_estimativa(
        demanda="Demanda 2", responsavel="Maria",
        notas={"analise": 3, "sql": 2, "debug": 4, "testes": 2, "deps": 1, "risco": 2},
        score=54.0, horas_base=34.4, buffer_risco=0.18, horas_finais=40.6,
        prazo_dias_frente=6.8, prazo_dias_apoio=3.4,
    )
    
    # Listar todas
    todas = persistencia.listar_estimativas()
    assert len(todas) == 2
    
    # Listar por responsável
    joao = persistencia.listar_estimativas(responsavel="João")
    assert len(joao) == 1
    assert joao[0].responsavel == "João"
```

---

## 4. Relatório Básico de Acuracidade

### arquivo: `analise.py`

```python
"""Módulo de análise e relatórios."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from persistencia import PersistenciaEstimativas


@dataclass
class RelatorioAcuracidade:
    """Resultado do relatório de acuracidade."""
    total_estimativas: int
    estimativas_concluidas: int
    taxa_acuracidade_media: float  # horas_reais / horas_finais
    desvio_medio_horas: float  # em horas
    desvio_medio_percentual: float  # em %
    melhor_estimativa_id: Optional[int]
    pior_estimativa_id: Optional[int]
    detalhes: List[dict]  # Lista com dados de cada estimativa


class AnalisadorEstimativas:
    """Analisa estimativas para gerar relatórios."""
    
    def __init__(self, persistencia: PersistenciaEstimativas):
        self.persistencia = persistencia
    
    def gerar_relatorio_acuracidade(
        self,
        responsavel: Optional[str] = None,
    ) -> RelatorioAcuracidade:
        """Gera relatório de acuracidade."""
        estimativas = self.persistencia.listar_estimativas(
            responsavel=responsavel,
            status="concluido",
            limite=1000,
        )
        
        total = len(estimativas)
        concluidas = sum(1 for e in estimativas if e.horas_reais is not None)
        
        if concluidas == 0:
            return RelatorioAcuracidade(
                total_estimativas=total,
                estimativas_concluidas=0,
                taxa_acuracidade_media=0.0,
                desvio_medio_horas=0.0,
                desvio_medio_percentual=0.0,
                melhor_estimativa_id=None,
                pior_estimativa_id=None,
                detalhes=[],
            )
        
        detalhes = []
        desvios = []
        acuracias = []
        
        for est in estimativas:
            if est.horas_reais is None:
                continue
            
            acuracia = est.horas_reais / est.horas_finais
            desvio_horas = est.horas_reais - est.horas_finais
            desvio_pct = (desvio_horas / est.horas_finais) * 100
            
            detalhes.append({
                "id": est.id,
                "demanda": est.demanda,
                "responsavel": est.responsavel,
                "estimado_horas": est.horas_finais,
                "realizado_horas": est.horas_reais,
                "acuracia": acuracia,
                "desvio_horas": desvio_horas,
                "desvio_percentual": desvio_pct,
            })
            
            acuracias.append(acuracia)
            desvios.append(abs(desvio_horas))
        
        media_acuracia = sum(acuracias) / len(acuracias)
        media_desvio_horas = sum(desvios) / len(desvios)
        media_desvio_pct = (media_desvio_horas / 40.0) * 100  # 40h é base média
        
        # Melhor e pior
        idx_melhor = acuracias.index(min(acuracias, key=lambda x: abs(x - 1.0)))
        idx_pior = acuracias.index(max(acuracias, key=lambda x: abs(x - 1.0)))
        
        return RelatorioAcuracidade(
            total_estimativas=total,
            estimativas_concluidas=concluidas,
            taxa_acuracidade_media=media_acuracia,
            desvio_medio_horas=media_desvio_horas,
            desvio_medio_percentual=media_desvio_pct,
            melhor_estimativa_id=detalhes[idx_melhor]["id"],
            pior_estimativa_id=detalhes[idx_pior]["id"],
            detalhes=detalhes,
        )
    
    def imprimir_relatorio(self, relatorio: RelatorioAcuracidade) -> None:
        """Imprime relatório formatado."""
        print("\n" + "="*70)
        print("RELATÓRIO DE ACURACIDADE")
        print("="*70)
        print(f"\nTotal de estimativas: {relatorio.total_estimativas}")
        print(f"Estimativas concluídas: {relatorio.estimativas_concluidas}")
        
        if relatorio.estimativas_concluidas == 0:
            print("\nNenhuma estimativa concluída ainda.")
            return
        
        print(f"\nTaxa de acuracidade média: {relatorio.taxa_acuracidade_media:.2f}x")
        print(f"  (1.0 = perfeito, <1.0 = subestimado, >1.0 = superestimado)")
        
        print(f"\nDesvio médio: {relatorio.desvio_medio_horas:.1f}h ({relatorio.desvio_medio_percentual:.1f}%)")
        print(f"Melhor estimativa: #{relatorio.melhor_estimativa_id}")
        print(f"Pior estimativa: #{relatorio.pior_estimativa_id}")
        
        print("\n" + "-"*70)
        print(f"{'ID':<5} {'Demanda':<25} {'Est(h)':<8} {'Real(h)':<8} {'Acur':<6} {'Desv%':<8}")
        print("-"*70)
        
        for detalhe in relatorio.detalhes:
            print(
                f"{detalhe['id']:<5} "
                f"{detalhe['demanda'][:25]:<25} "
                f"{detalhe['estimado_horas']:<8.1f} "
                f"{detalhe['realizado_horas']:<8.1f} "
                f"{detalhe['acuracia']:<6.2f} "
                f"{detalhe['desvio_percentual']:<8.1f}"
            )
```

---

## 5. Script de Teste

### arquivo: `exemplo_uso_fase1.py`

```python
"""
Exemplo de uso da Fase 1 (Persistência).
Simula fluxo completo: estimar -> salvar -> atualizar -> analisar.
"""

from persistencia import PersistenciaEstimativas
from analise import AnalisadorEstimativas

def main():
    # Inicializar persistência
    persist = PersistenciaEstimativas()
    
    # PASSO 1: Salvar algumas estimativas
    print("📝 Salvando estimativas...")
    
    est1_id = persist.salvar_estimativa(
        demanda="Corrigir erro SOAP em produção",
        responsavel="João Silva",
        notas={"analise": 4, "sql": 4, "debug": 5, "testes": 4, "deps": 3, "risco": 4},
        score=78.0,
        horas_base=48.8,
        buffer_risco=0.27,
        horas_finais=62.0,
        prazo_dias_frente=10.3,
        prazo_dias_apoio=5.2,
    )
    print(f"  ✅ Estimativa #{est1_id} salva")
    
    est2_id = persist.salvar_estimativa(
        demanda="Implementar nova feature X",
        responsavel="Maria Santos",
        notas={"analise": 2, "sql": 2, "debug": 2, "testes": 2, "deps": 1, "risco": 1},
        score=25.0,
        horas_base=17.0,
        buffer_risco=0.10,
        horas_finais=18.7,
        prazo_dias_frente=3.1,
        prazo_dias_apoio=1.6,
    )
    print(f"  ✅ Estimativa #{est2_id} salva")
    
    # PASSO 2: Simular conclusão (atualizar com resultado real)
    print("\n⏰ Atualizando com tempo real...")
    
    persist.atualizar_resultado(
        estimativa_id=est1_id,
        horas_reais=65.0,  # Demorou mais que estimado
        dias_reais=11,
        observacoes="Cliente pediu ajustes adicionais",
        status="concluido",
    )
    print(f"  ✅ Estimativa #{est1_id} atualizada (65h reais)")
    
    persist.atualizar_resultado(
        estimativa_id=est2_id,
        horas_reais=15.0,  # Saiu antes do estimado
        dias_reais=2,
        observacoes="Feature mais simples que o esperado",
        status="concluido",
    )
    print(f"  ✅ Estimativa #{est2_id} atualizada (15h reais)")
    
    # PASSO 3: Gerar relatório
    print("\n📊 Gerando relatório de acuracidade...")
    analisador = AnalisadorEstimativas(persist)
    relatorio = analisador.gerar_relatorio_acuracidade()
    analisador.imprimir_relatorio(relatorio)
    
    # PASSO 4: Calcular acuracias individuais
    print("\n🎯 Análise Individual:")
    acur1 = persist.calcular_acuracidade(est1_id)
    acur2 = persist.calcular_acuracidade(est2_id)
    print(f"  Estimativa #{est1_id}: {acur1:.2f}x (superestimado: +{(acur1-1)*100:.1f}%)")
    print(f"  Estimativa #{est2_id}: {acur2:.2f}x (subestimado: {(1-acur2)*100:.1f}%)")
    
    # PASSO 5: Listar histórico
    print(f"\n📋 Histórico (últimas 10):")
    historico = persist.listar_estimativas(limite=10)
    for est in historico:
        status_str = f"({est.status})" if est.status != "planejado" else ""
        print(f"  #{est.id}: {est.demanda} - {est.responsavel} {status_str}")

if __name__ == "__main__":
    main()
```

---

## 6. Checklist de Implementação

```
FASE 1 - CHECKLIST DE IMPLEMENTAÇÃO
====================================

□ PREPARAÇÃO
  □ Criar branch `feature/persistencia`
  □ Setup de ambiente (pytest, venv atualizado)
  □ Revisar schema SQLite com time

□ IMPLEMENTAÇÃO CORE
  □ Criar arquivo `persistencia.py`
  □ Implementar `PersistenciaEstimativas`
  □ Testes unitários (`test_persistencia.py`)
  □ Coverage > 80%

□ INTEGRAÇÃO FRONTEND
  □ Modificar `calculadora_frontend.py`
  □ Adicionar campos "Demanda" e "Responsável"
  □ Integrar salvamento automático
  □ Adicionar botão "Histórico"
  □ Testes de integração

□ ANÁLISE
  □ Criar arquivo `analise.py`
  □ Implementar `AnalisadorEstimativas`
  □ Relatório de acuracidade básico
  □ Testes unitários

□ DOCUMENTAÇÃO
  □ Comentários no código
  □ Docstrings completas
  □ Exemplos de uso
  □ README.md atualizado com Fase 1

□ TESTES E QUALIDADE
  □ Coverage > 80%
  □ Lint (flake8/black)
  □ Type hints completos
  □ Testes em múltiplos cenários

□ DEPLOY
  □ Merge para main
  □ Tag v1.1.0
  □ Release notes
  □ Comunicar time

ESTIMATIVA: 8-10 pontos (2 sprints)
```

---

**Próximo Passo**: Depois que Fase 1 estiver pronta, começar Fase 2 com dashboard e gráficos.
