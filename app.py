import streamlit as st 
st.set_page_config(layout="wide")
import pandas as pd
import sqlite3
from datetime import date
import io
from openpyxl.styles import Alignment, PatternFill, Font
from openpyxl.utils import get_column_letter

EXCEL_PATH = "Movimentações.xlsx"
DB_PATH = "transacoes.db"

def get_columns(sheet_name):
    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name, header=0)
    colunas = [c for c in df.columns if not str(c).startswith("Unnamed") and not str(c).startswith("Column")]
    return colunas

def salvar_transacao(tipo, respostas):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    colunas_sql = ", ".join([f'"{k}" TEXT' for k in respostas.keys()])
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS "{tipo}" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {colunas_sql}
        )
    ''')
    campos = ", ".join([f'"{k}"' for k in respostas.keys()])
    valores = tuple(str(v) for v in respostas.values())
    placeholders = ", ".join(["?"] * len(respostas))
    cursor.execute(f'''
        INSERT INTO "{tipo}" ({campos}) VALUES ({placeholders})
    ''', valores)
    conn.commit()
    conn.close()

def consultar_transacoes(tipo):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f'SELECT * FROM "{tipo}"', conn)
    conn.close()
    return df

def exportar_todas_aba_excel(abas):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for aba in abas:
            try:
                df = consultar_transacoes(aba)
                df.to_excel(writer, sheet_name=aba[:31], index=False)
            except Exception:
                continue
        writer.book.active = 0  # Primeira aba ativa

        # Formatação openpyxl
        for aba in abas:
            if aba[:31] in writer.book.sheetnames:
                ws = writer.book[aba[:31]]
                max_row = ws.max_row
                max_col = ws.max_column

                ws.sheet_view.showGridLines = False
                # Autoajustar largura
                for col in range(1, max_col + 1):
                    max_length = 0
                    col_letter = get_column_letter(col)
                    for cell in ws[col_letter]:
                        try:
                            val = str(cell.value)
                        except:
                            val = ""
                        if val is None:
                            val = ""
                        max_length = max(max_length, len(val))
                    ws.column_dimensions[col_letter].width = max(10, min(max_length + 2, 40))
                ws.auto_filter.ref = ws.dimensions
                for i, row in enumerate(ws.iter_rows(min_row=2, max_row=max_row, max_col=max_col), start=2):
                    fill = PatternFill("solid", fgColor="F6F7F9") if i % 2 == 0 else PatternFill("solid", fgColor="FFFFFF")
                    for cell in row:
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                        cell.fill = fill
                # Cabeçalho azul claro, fonte preta e negrito
                for cell in ws[1]:
                    cell.fill = PatternFill("solid", fgColor="99CCFF")
                    cell.font = Font(color="000000", bold=True)
                    cell.alignment = Alignment(horizontal="center", vertical="center")
    output.seek(0)
    return output

excel_file = pd.ExcelFile(EXCEL_PATH)
abas = excel_file.sheet_names

st.title("Confirmação de Transações")

tipo = st.selectbox("Selecione o tipo de transação:", abas)
campos = get_columns(tipo)
tem_quantidade = any(c.lower() == "quantidade" for c in campos)
tem_preco = any("preço" in c.lower() for c in campos)
tem_financeiro = any("financeiro" in c.lower() for c in campos)

with st.form(key="formulario_transacao"):
    st.subheader(f"Preencha os dados de '{tipo}' (estilo planilha)")
    respostas = {}
    if len(campos) == 0:
        st.warning("Nenhum campo encontrado para esta aba. Verifique a planilha.")
    else:
        col_widths = [2 if "Data" in campo or len(campo) > 14 else 1 for campo in campos]
        cols = st.columns(col_widths)
        quant_input = preco_input = None
        for idx, (col, campo) in enumerate(zip(cols, campos)):
            campo_lower = campo.lower()
            if "data" in campo_lower:
                respostas[campo] = col.date_input(campo, value=date.today())
            elif campo_lower == "quantidade":
                quant_input = col.number_input(campo, min_value=0.0, step=1.0, format="%.2f")
                respostas[campo] = quant_input
            elif "preço" in campo_lower:
                preco_input = col.number_input(campo, min_value=0.0, step=0.01, format="%.2f")
                respostas[campo] = preco_input
            elif "financeiro" in campo_lower:
                if tem_quantidade and tem_preco:
                    financeiro = (quant_input or 0) * (preco_input or 0)
                    respostas[campo] = financeiro
                    col.text_input(campo, value=f"{financeiro:,.2f}", disabled=True, key=campo)
                else:
                    respostas[campo] = col.text_input(campo, placeholder="Digite aqui", key=campo)
            else:
                respostas[campo] = col.text_input(campo, placeholder="Digite aqui", key=campo)
    submit = st.form_submit_button("Confirmar")

if submit and len(campos) > 0:
    salvar_transacao(tipo, respostas)
    st.success("Transação registrada com sucesso!")
    st.write("Resumo dos dados preenchidos:")
    st.table(pd.DataFrame([respostas]))

st.subheader(f"Transações já registradas para: {tipo}")
try:
    df_transacoes = consultar_transacoes(tipo)
    st.dataframe(df_transacoes)
except Exception:
    a = True

st.markdown("### Download geral de todas as transações")
if st.button("Baixar todas as transações formatadas (.xlsx)"):
    excel_export = exportar_todas_aba_excel(abas)
    st.download_button(
        label="Clique aqui para baixar",
        data=excel_export,
        file_name="todas_transacoes_formatadas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.caption("Exportação completa: uma aba por tipo, formatação profissional, filtros e zebra. Se quiser ainda mais customização, só avisar!")
