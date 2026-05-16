"""
Levantamento Completo de Banco de Dados Microsoft Access
=========================================================
Execute no Windows com Python 3.x instalado e Microsoft Access instalado.

Pré-requisitos:
  pip install pyodbc pandas openpyxl pywin32

  O Microsoft Access precisa estar instalado na máquina para que a extração
  via COM (formulários, relatórios, VBA) funcione corretamente.

Uso:
  python levantamento_access.py "C:\\caminho\\para\\seu_banco.accdb"

O script gera:
  - levantamento_access_TIMESTAMP.xlsx  → visão geral estruturada em Excel
  - vba_TIMESTAMP/                      → pasta com um .txt por módulo VBA

Abas do Excel:
  1 - Tabelas             → todas as tabelas com contagem de registros
  2 - Colunas             → campos, tipos, tamanhos e nulabilidade
  3 - Índices             → chaves primárias e índices
  4 - Relacionamentos     → FKs entre tabelas
  5 - Queries             → queries salvas
  5b - Queries SQL        → SQL completo de cada query
  6 - Formulários         → controles, fontes de dados e propriedades
  7 - Relatórios          → controles e fontes de dados dos relatórios
  8 - Macros              → lista de macros
  9 - Módulos VBA         → lista de módulos (código exportado em pasta separada)
  dados_[tabela]          → amostra de 5 registros por tabela
"""

import sys
import os
import pyodbc
import pandas as pd
from datetime import datetime

# win32com é opcional: se não estiver disponível, pula a extração COM
try:
    import win32com.client
    WIN32_DISPONIVEL = True
except ImportError:
    WIN32_DISPONIVEL = False


# ──────────────────────────────────────────────
# CONEXÃO
# ──────────────────────────────────────────────

def conectar(caminho_accdb: str) -> pyodbc.Connection:
    if not os.path.exists(caminho_accdb):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_accdb}")
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={caminho_accdb};"
    )
    return pyodbc.connect(conn_str)


# ──────────────────────────────────────────────
# TABELAS E COLUNAS
# ──────────────────────────────────────────────

def listar_tabelas(conn: pyodbc.Connection) -> pd.DataFrame:
    cursor = conn.cursor()
    # Materializar a lista antes de iterar — cursor.execute() abaixo invalidaria
    # o iterador de cursor.tables() se ele estivesse aberto no mesmo cursor.
    nomes = [r.table_name for r in cursor.tables(tableType="TABLE")]
    tabelas = []
    for nome in nomes:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM [{nome}]")
            total = cursor.fetchone()[0]
        except Exception:
            total = None
        tabelas.append({
            "Tabela": nome,
            "Total de Registros": total,
        })
    return pd.DataFrame(tabelas)


def listar_colunas(conn: pyodbc.Connection) -> pd.DataFrame:
    cursor = conn.cursor()
    colunas = []

    # Mapa de tipos ODBC → nomes legíveis
    tipos = {
        -7: "BIT", -6: "TINYINT", 5: "SMALLINT", 4: "INTEGER",
        -5: "BIGINT", 6: "FLOAT", 7: "REAL", 8: "DOUBLE",
        2: "NUMERIC", 3: "DECIMAL", 1: "CHAR", 12: "VARCHAR",
        -1: "LONGVARCHAR", -8: "WCHAR", -9: "WVARCHAR",
        -10: "WLONGVARCHAR", 91: "DATE", 92: "TIME", 93: "DATETIME",
        -2: "BINARY", -3: "VARBINARY", -4: "LONGVARBINARY",
    }

    # Materializar nomes antes de iterar (cursor.columns invalida cursor.tables)
    nomes = [r.table_name for r in cursor.tables(tableType="TABLE")]
    for nome_tabela in nomes:
        for col in cursor.columns(table=nome_tabela):
            colunas.append({
                "Tabela":       nome_tabela,
                "Coluna":       col.column_name,
                "Tipo":         tipos.get(col.data_type, str(col.data_type)),
                "Tamanho":      col.column_size,
                "Nulo?":        "Sim" if col.nullable else "Não",
                "Padrão":       col.column_def,
            })
    return pd.DataFrame(colunas)


# ──────────────────────────────────────────────
# CHAVES PRIMÁRIAS E ÍNDICES
# ──────────────────────────────────────────────

def listar_indices(conn: pyodbc.Connection) -> pd.DataFrame:
    cursor = conn.cursor()
    indices = []
    nomes = [r.table_name for r in cursor.tables(tableType="TABLE")]
    for nome_tabela in nomes:
        try:
            for idx in cursor.statistics(nome_tabela):
                if idx.index_name:
                    indices.append({
                        "Tabela":        nome_tabela,
                        "Índice":        idx.index_name,
                        "Coluna":        idx.column_name,
                        "Único?":        "Sim" if idx.non_unique == 0 else "Não",
                        "Chave Primária?": "Sim" if idx.index_name == "PrimaryKey" else "Não",
                        "Ordem":         "ASC" if idx.asc_or_desc == "A" else "DESC",
                    })
        except Exception:
            pass
    return pd.DataFrame(indices)


# ──────────────────────────────────────────────
# RELACIONAMENTOS (via MSysRelationships)
# ──────────────────────────────────────────────

def listar_relacionamentos(conn: pyodbc.Connection) -> pd.DataFrame:
    sql = """
        SELECT
            szRelationship  AS Relacionamento,
            szReferencedObject AS TabelaPai,
            szReferencedColumn AS ColunaPai,
            szObject        AS TabelaFilha,
            szColumn        AS ColunaFilha,
            grbit           AS Flags
        FROM MSysRelationships
        ORDER BY szRelationship
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        cols = [c[0] for c in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=cols)
    except Exception as e:
        return pd.DataFrame([{"Erro": str(e), "Observação": "MSysRelationships pode exigir permissão de leitura em tabelas de sistema."}])


# ──────────────────────────────────────────────
# QUERIES SALVAS
# ──────────────────────────────────────────────

def listar_queries(conn: pyodbc.Connection) -> pd.DataFrame:
    sql = """
        SELECT
            Name        AS Nome,
            DateCreate  AS Criado,
            DateUpdate  AS Atualizado,
            [Type]      AS Tipo
        FROM MSysObjects
        WHERE [Type] = 5
        ORDER BY Name
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        cols = [c[0] for c in cursor.description]
        df = pd.DataFrame(cursor.fetchall(), columns=cols)
        sqls = []
        for nome in df["Nome"]:
            try:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM [{nome}] WHERE 1=0")
                sqls.append("(view — SQL não disponível via ODBC)")
            except Exception as e:
                sqls.append(str(e)[:200])
        df["SQL / Observação"] = sqls
        return df
    except Exception as e:
        return pd.DataFrame([{"Erro": str(e)}])


def listar_queries_sql(conn: pyodbc.Connection) -> pd.DataFrame:
    """Extrai o SQL de cada query via MSysQueries."""
    sql = """
        SELECT
            o.Name        AS Nome,
            q.Attribute,
            q.Expression
        FROM MSysObjects o
        JOIN MSysQueries q ON o.Id = q.ObjectId
        WHERE o.[Type] = 5
        ORDER BY o.Name, q.Attribute
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        cols = [c[0] for c in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=cols)
    except Exception as e:
        return pd.DataFrame([{"Erro": str(e)}])


# ──────────────────────────────────────────────
# FORMULÁRIOS E RELATÓRIOS
# ──────────────────────────────────────────────

def listar_objetos_visuais(conn: pyodbc.Connection) -> pd.DataFrame:
    """
    Tipos em MSysObjects:
      -32768 = Formulário (Form)
      -32764 = Relatório (Report)
      -32766 = Macro
      -32761 = Módulo VBA
    """
    sql = """
        SELECT
            Name        AS Nome,
            [Type]      AS TipoCod,
            DateCreate  AS Criado,
            DateUpdate  AS Atualizado
        FROM MSysObjects
        WHERE [Type] IN (-32768, -32764, -32766, -32761)
        ORDER BY [Type], Name
    """
    tipo_map = {
        -32768: "Formulário",
        -32764: "Relatório",
        -32766: "Macro",
        -32761: "Módulo VBA",
    }
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        cols = [c[0] for c in cursor.description]
        df = pd.DataFrame(cursor.fetchall(), columns=cols)
        df["Tipo"] = df["TipoCod"].map(tipo_map)
        return df[["Nome", "Tipo", "Criado", "Atualizado"]]
    except Exception as e:
        return pd.DataFrame([{"Erro": str(e)}])


# ──────────────────────────────────────────────
# WIN32COM — FORMULÁRIOS
# ──────────────────────────────────────────────

# Mapa de tipos de controle Access → nome legível
TIPO_CONTROLE = {
    100: "Rótulo",
    101: "Caixa de Texto",
    102: "Grupo de Opções",
    103: "Botão de Alternância",
    104: "Botão de Opção",
    105: "Caixa de Seleção",
    106: "Caixa de Combinação",
    107: "Caixa de Listagem",
    108: "Botão de Comando",
    109: "Imagem",
    110: "Quadro de Objeto",
    111: "Quadro de Objeto Acoplado",
    112: "Quebra de Página",
    113: "Controle de Guia",
    114: "Subformulário/Sub-relatório",
    115: "Linha",
    116: "Retângulo",
    118: "Controle ActiveX",
}

def _extrair_controles(obj_access, nome_objeto: str, tipo_objeto: str) -> list[dict]:
    """Abre um formulário ou relatório em modo Design e extrai seus controles."""
    registros = []
    modo_design = 1  # acDesign

    try:
        if tipo_objeto == "Formulário":
            obj_access.DoCmd.OpenForm(nome_objeto, modo_design)
            container = obj_access.Forms(nome_objeto)
        else:
            obj_access.DoCmd.OpenReport(nome_objeto, modo_design)
            container = obj_access.Reports(nome_objeto)

        # Fonte de dados do formulário/relatório
        fonte_principal = ""
        try:
            fonte_principal = container.RecordSource
        except Exception:
            pass

        for ctrl in container.Controls:
            try:
                tipo_cod  = ctrl.ControlType
                tipo_nome = TIPO_CONTROLE.get(tipo_cod, f"Tipo {tipo_cod}")
                fonte     = ""
                formato   = ""
                legenda   = ""
                eventos   = []

                try:
                    fonte = ctrl.ControlSource
                except Exception:
                    pass
                try:
                    formato = ctrl.Format
                except Exception:
                    pass
                try:
                    legenda = ctrl.Caption
                except Exception:
                    pass

                # Verificar eventos com código VBA associado
                for ev in ["OnClick", "OnChange", "OnEnter", "OnExit",
                           "OnDblClick", "OnGotFocus", "OnLostFocus",
                           "BeforeUpdate", "AfterUpdate", "OnLoad",
                           "OnOpen", "OnClose", "OnCurrent"]:
                    try:
                        val = getattr(ctrl, ev, "")
                        if val and str(val).startswith("[Event Procedure]"):
                            eventos.append(ev)
                    except Exception:
                        pass

                registros.append({
                    "Objeto":          nome_objeto,
                    "Tipo Objeto":     tipo_objeto,
                    "Fonte de Dados":  fonte_principal,
                    "Controle":        ctrl.Name,
                    "Tipo Controle":   tipo_nome,
                    "Fonte do Campo":  fonte,
                    "Legenda":         legenda,
                    "Formato":         formato,
                    "Eventos VBA":     ", ".join(eventos) if eventos else "",
                })
            except Exception:
                pass

        # Fechar sem salvar
        obj_access.DoCmd.Close(
            2 if tipo_objeto == "Formulário" else 3,  # acForm / acReport
            nome_objeto,
            2  # acSaveNo
        )

    except Exception as e:
        registros.append({
            "Objeto": nome_objeto,
            "Tipo Objeto": tipo_objeto,
            "Fonte de Dados": "",
            "Controle": f"ERRO ao abrir: {e}",
            "Tipo Controle": "", "Fonte do Campo": "",
            "Legenda": "", "Formato": "", "Eventos VBA": "",
        })

    return registros


def extrair_formularios_com(caminho_accdb: str) -> pd.DataFrame:
    access = win32com.client.Dispatch("Access.Application")
    access.Visible = True          # True evita bloqueio de segurança do Access
    access.UserControl = False     # mas mantém sem interação do usuário
    access.OpenCurrentDatabase(caminho_accdb, False)

    registros = []
    try:
        for form in access.CurrentProject.AllForms:
            print(f"   Formulário: {form.Name}")
            registros += _extrair_controles(access, form.Name, "Formulário")
    finally:
        access.CloseCurrentDatabase()
        access.Quit()

    return pd.DataFrame(registros)


def extrair_relatorios_com(caminho_accdb: str) -> pd.DataFrame:
    access = win32com.client.Dispatch("Access.Application")
    access.Visible = True
    access.UserControl = False
    access.OpenCurrentDatabase(caminho_accdb, False)

    registros = []
    try:
        for rpt in access.CurrentProject.AllReports:
            print(f"   Relatório: {rpt.Name}")
            registros += _extrair_controles(access, rpt.Name, "Relatório")
    finally:
        access.CloseCurrentDatabase()
        access.Quit()

    return pd.DataFrame(registros)


# ──────────────────────────────────────────────
# WIN32COM — VBA
# ──────────────────────────────────────────────

def extrair_vba_com(caminho_accdb: str, pasta_saida: str) -> pd.DataFrame:
    """
    Exporta cada módulo VBA para um arquivo .txt na pasta_saida.
    Retorna um DataFrame com o inventário dos módulos.
    """
    os.makedirs(pasta_saida, exist_ok=True)

    access = win32com.client.Dispatch("Access.Application")
    access.Visible = True
    access.UserControl = False
    access.OpenCurrentDatabase(caminho_accdb, False)

    modulos = []
    try:
        vba_project = access.VBE.ActiveVBProject
        for comp in vba_project.VBComponents:
            nome      = comp.Name
            tipo_cod  = comp.Type
            tipos_vba = {1: "Módulo Padrão", 2: "Módulo de Classe",
                         3: "Formulário", 100: "Documento"}
            tipo_nome = tipos_vba.get(tipo_cod, f"Tipo {tipo_cod}")

            codigo = ""
            linhas = 0
            try:
                mod = comp.CodeModule
                linhas = mod.CountOfLines
                if linhas > 0:
                    codigo = mod.Lines(1, linhas)
            except Exception:
                pass

            # Salvar em arquivo
            arq = os.path.join(pasta_saida, f"{nome}.txt")
            with open(arq, "w", encoding="utf-8") as f:
                f.write(f"' Módulo: {nome}\n")
                f.write(f"' Tipo:   {tipo_nome}\n")
                f.write(f"' Linhas: {linhas}\n")
                f.write("' " + "─" * 60 + "\n\n")
                f.write(codigo)

            modulos.append({
                "Módulo":  nome,
                "Tipo":    tipo_nome,
                "Linhas":  linhas,
                "Arquivo": arq,
            })
            print(f"   VBA exportado: {nome} ({linhas} linhas)")

    finally:
        access.CloseCurrentDatabase()
        access.Quit()

    return pd.DataFrame(modulos)


# ──────────────────────────────────────────────
# WIN32COM — METADADOS (relacionamentos, queries, inventário)
# ──────────────────────────────────────────────

# Tipos de QueryDef do DAO (Type property)
TIPO_QUERY = {
    0:   "SELECT",
    16:  "CROSSTAB",
    32:  "DELETE",
    48:  "UPDATE",
    64:  "APPEND",
    80:  "MAKE TABLE",
    96:  "DDL",
    112: "SQL PASS-THROUGH",
    128: "UNION",
    144: "SPT BULK",
    240: "ACTION",
}

# Flags principais de Relation.Attributes (bitmask)
_REL_FLAGS = [
    (1,        "Unique"),
    (2,        "DontEnforce"),
    (4,        "Inherited"),
    (4096,     "DeleteCascade"),
    (16384,    "UpdateCascade"),
    (16777216, "LeftJoin"),
    (33554432, "RightJoin"),
]


def _decodificar_attrs_relacao(attrs: int) -> str:
    return ", ".join(nome for bit, nome in _REL_FLAGS if attrs & bit) or ""


def _dt_com(val):
    """
    Converte pywintypes.datetime (devolvido pelo COM) para datetime nativo.
    O tipo COM tem tzinfo com gettz() == None, o que faz o pandas estourar
    AttributeError em ints_to_pydatetime ao serializar para Excel.
    """
    if val is None:
        return None
    try:
        return datetime(val.year, val.month, val.day,
                        getattr(val, "hour", 0),
                        getattr(val, "minute", 0),
                        getattr(val, "second", 0))
    except Exception:
        return None


def extrair_metadados_com(caminho_accdb: str) -> dict[str, pd.DataFrame]:
    """
    Extrai via COM (DAO): relacionamentos, queries (com SQL completo) e
    inventário de formulários/relatórios/macros/módulos.

    Substitui as consultas diretas a MSysObjects/MSysRelationships, que
    no Access exigem permissão explícita de leitura em tabelas de sistema
    (via "GRANT SELECT ON MSysObjects" ou pela própria UI do Access).
    """
    access = win32com.client.Dispatch("Access.Application")
    access.Visible = True
    access.UserControl = False
    access.OpenCurrentDatabase(caminho_accdb, False)

    resultado: dict[str, pd.DataFrame] = {}

    try:
        db = access.CurrentDb()

        # --- Relacionamentos ---
        rels = []
        for rel in db.Relations:
            for f in rel.Fields:
                rels.append({
                    "Relacionamento": rel.Name,
                    "TabelaPai":      rel.Table,
                    "ColunaPai":      f.Name,
                    "TabelaFilha":    rel.ForeignTable,
                    "ColunaFilha":    f.ForeignName,
                    "Flags":          _decodificar_attrs_relacao(rel.Attributes),
                })
        resultado["relacionamentos"] = pd.DataFrame(rels)

        # --- Queries (lista + SQL) ---
        queries_basic = []
        queries_sql = []
        for q in db.QueryDefs:
            nome = q.Name
            # Ignorar queries internas/temporárias do Access (prefixo ~)
            if nome.startswith("~"):
                continue
            try:
                criado = _dt_com(q.DateCreated)
            except Exception:
                criado = None
            try:
                atualizado = _dt_com(q.LastUpdated)
            except Exception:
                atualizado = None
            try:
                tipo_cod = q.Type
            except Exception:
                tipo_cod = None
            try:
                sql_text = q.SQL
            except Exception as e:
                sql_text = f"ERRO: {e}"

            queries_basic.append({
                "Nome":       nome,
                "Tipo":       TIPO_QUERY.get(tipo_cod, f"Tipo {tipo_cod}"),
                "Criado":     criado,
                "Atualizado": atualizado,
            })
            queries_sql.append({
                "Nome": nome,
                "SQL":  sql_text,
            })
        resultado["queries"] = pd.DataFrame(queries_basic)
        resultado["queries_sql"] = pd.DataFrame(queries_sql)

        # --- Inventário forms/reports/macros/módulos ---
        inventario = []
        proj = access.CurrentProject

        def _add(colecao, tipo_legivel):
            for obj in colecao:
                try:
                    criado = _dt_com(obj.DateCreated)
                except Exception:
                    criado = None
                try:
                    modif = _dt_com(obj.DateModified)
                except Exception:
                    modif = None
                inventario.append({
                    "Nome":       obj.Name,
                    "Tipo":       tipo_legivel,
                    "Criado":     criado,
                    "Atualizado": modif,
                })

        _add(proj.AllForms,   "Formulário")
        _add(proj.AllReports, "Relatório")
        _add(proj.AllMacros,  "Macro")
        _add(proj.AllModules, "Módulo VBA")
        resultado["inventario"] = pd.DataFrame(inventario)

    finally:
        access.CloseCurrentDatabase()
        access.Quit()

    return resultado


# ──────────────────────────────────────────────
# AMOSTRA DE DADOS
# ──────────────────────────────────────────────

def amostras_dados(conn: pyodbc.Connection, max_linhas: int = 5) -> dict[str, pd.DataFrame]:
    cursor = conn.cursor()
    nomes = [r.table_name for r in cursor.tables(tableType="TABLE")]
    amostras = {}
    for nome in nomes:
        try:
            cursor2 = conn.cursor()
            cursor2.execute(f"SELECT TOP {max_linhas} * FROM [{nome}]")
            cols = [c[0] for c in cursor2.description]
            # pyodbc.Row precisa ser convertido em tupla — pandas 2.x não
            # desempacota a Row automaticamente e enxerga cada linha como
            # uma única coluna (gera "Shape of passed values is (N, 1)").
            rows = [tuple(r) for r in cursor2.fetchall()]
            amostras[nome] = pd.DataFrame(rows, columns=cols)
        except Exception as e:
            amostras[nome] = pd.DataFrame([{"Erro": str(e)}])
    return amostras


# ──────────────────────────────────────────────
# EXPORTAÇÃO PARA EXCEL
# ──────────────────────────────────────────────

def _sanitizar_aba(nome: str) -> str:
    """Remove caracteres inválidos em nomes de aba do Excel e limita a 31 chars."""
    for c in r'\/:*?[]':
        nome = nome.replace(c, "-")
    return nome[:31]


def exportar_excel(dados: dict[str, pd.DataFrame], caminho_saida: str):
    abas_usadas: dict[str, int] = {}
    with pd.ExcelWriter(caminho_saida, engine="openpyxl") as writer:
        for nome_aba, df in dados.items():
            aba = _sanitizar_aba(nome_aba)
            if aba in abas_usadas:
                abas_usadas[aba] += 1
                aba = _sanitizar_aba(f"{aba}_{abas_usadas[aba]}")
            else:
                abas_usadas[aba] = 0
            df.to_excel(writer, sheet_name=aba, index=False)

            # Auto-ajustar largura das colunas
            ws = writer.sheets[aba]
            for col in ws.columns:
                max_len = max((len(str(c.value)) for c in col if c.value), default=10)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)

    print(f"\n✅ Relatório salvo em: {caminho_saida}")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Uso: python levantamento_access.py \"C:\\caminho\\banco.accdb\"")
        sys.exit(1)

    caminho = sys.argv[1]
    print(f"🔍 Conectando a: {caminho}")

    conn = conectar(caminho)
    print("✅ Conexão estabelecida.\n")

    abas = {}

    # ── Etapa 1: via ODBC (pyodbc) ──────────────────────────────────────────

    print("📋 Levantando tabelas...")
    abas["1 - Tabelas"] = listar_tabelas(conn)
    print(f"   {len(abas['1 - Tabelas'])} tabela(s) encontrada(s).")

    print("📋 Levantando colunas...")
    abas["2 - Colunas"] = listar_colunas(conn)
    print(f"   {len(abas['2 - Colunas'])} coluna(s) encontrada(s).")

    print("📋 Levantando índices e chaves...")
    abas["3 - Índices"] = listar_indices(conn)

    # Relacionamentos, queries e inventário: preferimos via COM (mais
    # robusto, dispensa permissão em MSysObjects/MSysRelationships).
    # Reservamos os slots aqui para manter a ordem das abas no Excel,
    # mesmo que o preenchimento aconteça depois (etapa COM).
    abas["4 - Relacionamentos"]          = pd.DataFrame()
    abas["5 - Queries"]                  = pd.DataFrame()
    abas["5b - Queries SQL"]             = pd.DataFrame()
    abas["6 - Inventário Forms/Reports"] = pd.DataFrame()

    if not WIN32_DISPONIVEL:
        print("📋 Levantando relacionamentos (ODBC)...")
        abas["4 - Relacionamentos"] = listar_relacionamentos(conn)

        print("📋 Levantando queries (ODBC)...")
        abas["5 - Queries"] = listar_queries(conn)
        abas["5b - Queries SQL"] = listar_queries_sql(conn)

        print("📋 Levantando inventário forms/reports/macros (ODBC)...")
        abas["6 - Inventário Forms/Reports"] = listar_objetos_visuais(conn)
        obj = abas["6 - Inventário Forms/Reports"]
        if "Tipo" in obj.columns:
            for tipo, qtd in obj["Tipo"].value_counts().items():
                print(f"   {qtd} {tipo}(s)")

    print("📋 Coletando amostras de dados (5 registros por tabela)...")
    for nome, df in amostras_dados(conn).items():
        abas[f"dados_{nome[:24]}"] = df

    conn.close()

    # ── Etapa 2: via COM (win32com) ──────────────────────────────────────────

    pasta_saida = os.path.dirname(caminho) or "."
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    if not WIN32_DISPONIVEL:
        print("\n⚠️  pywin32 não encontrado — pulando extração de formulários, relatórios e VBA.")
        print("   Para ativar: pip install pywin32")
    else:
        print("\n📋 Extraindo relacionamentos, queries e inventário via COM...")
        try:
            meta = extrair_metadados_com(caminho)
            abas["4 - Relacionamentos"]        = meta["relacionamentos"]
            abas["5 - Queries"]                = meta["queries"]
            abas["5b - Queries SQL"]           = meta["queries_sql"]
            abas["6 - Inventário Forms/Reports"] = meta["inventario"]
            print(f"   {len(meta['relacionamentos'])} relacionamento(s), "
                  f"{len(meta['queries'])} query(ies), "
                  f"{len(meta['inventario'])} objeto(s) no inventário.")
            inv = meta["inventario"]
            if "Tipo" in inv.columns:
                for tipo, qtd in inv["Tipo"].value_counts().items():
                    print(f"   {qtd} {tipo}(s)")
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair metadados via COM: {e}")
            df_err = pd.DataFrame([{"Erro": str(e)}])
            abas.setdefault("4 - Relacionamentos", df_err)
            abas.setdefault("5 - Queries", df_err)
            abas.setdefault("5b - Queries SQL", df_err)
            abas.setdefault("6 - Inventário Forms/Reports", df_err)

        print("\n📋 Extraindo controles dos formulários via COM...")
        try:
            abas["7 - Formulários (detalhes)"] = extrair_formularios_com(caminho)
            print(f"   {len(abas['7 - Formulários (detalhes)'])} controle(s) extraído(s).")
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair formulários: {e}")
            abas["7 - Formulários (detalhes)"] = pd.DataFrame([{"Erro": str(e)}])

        print("\n📋 Extraindo controles dos relatórios via COM...")
        try:
            abas["8 - Relatórios (detalhes)"] = extrair_relatorios_com(caminho)
            print(f"   {len(abas['8 - Relatórios (detalhes)'])} controle(s) extraído(s).")
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair relatórios: {e}")
            abas["8 - Relatórios (detalhes)"] = pd.DataFrame([{"Erro": str(e)}])

        print("\n📋 Exportando código VBA...")
        pasta_vba = os.path.join(pasta_saida, f"vba_{ts}")
        try:
            abas["9 - Módulos VBA"] = extrair_vba_com(caminho, pasta_vba)
            print(f"   Código exportado para: {pasta_vba}")
        except Exception as e:
            print(f"   ⚠️  Erro ao exportar VBA: {e}")
            abas["9 - Módulos VBA"] = pd.DataFrame([{"Erro": str(e)}])

    # ── Salvar Excel ─────────────────────────────────────────────────────────

    saida = os.path.join(pasta_saida, f"levantamento_access_{ts}.xlsx")
    exportar_excel(abas, saida)

    # ── Resumo final ─────────────────────────────────────────────────────────

    print("\n📊 Resumo do levantamento:")
    print(f"   Tabelas:    {len(abas.get('1 - Tabelas', []))}")
    print(f"   Colunas:    {len(abas.get('2 - Colunas', []))}")
    print(f"   Queries:    {len(abas.get('5 - Queries', []))}")

    inv = abas.get("6 - Inventário Forms/Reports", pd.DataFrame())
    if "Tipo" in inv.columns:
        for tipo, qtd in inv["Tipo"].value_counts().items():
            print(f"   {tipo}s: {qtd}")

    if WIN32_DISPONIVEL:
        forms_det = abas.get("7 - Formulários (detalhes)", pd.DataFrame())
        if "Objeto" in forms_det.columns:
            print(f"   Controles de formulários: {len(forms_det)}")
        vba = abas.get("9 - Módulos VBA", pd.DataFrame())
        if "Módulo" in vba.columns:
            total_linhas = vba["Linhas"].sum() if "Linhas" in vba.columns else 0
            print(f"   Módulos VBA: {len(vba)} ({total_linhas} linhas de código)")

    print(f"\n✅ Excel: {saida}")
    if WIN32_DISPONIVEL:
        print(f"✅ VBA:   {pasta_vba}")
    print("\nPróximo passo: compartilhe o Excel e os arquivos VBA para gerarmos os models Django.")


if __name__ == "__main__":
    main()
