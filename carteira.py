
def tela_carteira():
    import requests
    import pandas as pd
    from datetime import date
    import streamlit as st
    import streamlit as st
    import requests
    import pandas as pd
    from datetime import date
    import io
    import sqlite3
    from openpyxl.styles import Alignment, PatternFill, Font
    from openpyxl.utils import get_column_letter
    from transacoes import tela_transacoes
    # ========== CONFIGURAÇÕES ==========
    st.set_page_config(layout="wide")
    BASE_URL_API = "https://longview.bluedeck.com.br/api"
    CLIENT_ID = "46745f1ee8a39550799966aeac655589.access"
    CLIENT_SECRET = "7c8c1802b0f4c9ac4ebe57eee3eb84f4ed87a2eb6a25a5b3afe335474708ce11"
    EXCEL_PATH = "Movimentações.xlsx"
    DB_PATH = "transacoes.db"
    CARTEIRAS = {
        257: "PEPENERO FIM",
        275: "FILIPINA FIM",
        307: "PARMIGIANO FIM",
        308: "HARPYJA FIM",
        1313: "SL_01_ON",
        1362: "TL_01_ON",
        1489: "Medici"
        
    }
    MAPA_RENOMEACAO_ATIVOS = {
        "instrument_symbol": "Ticker",
        "instrument_id": "Ticker ID",
        "instrument_type": "Tipo do Ticker",
        "instrument_name": "Nome",
        "position_overview_id": "ID Posição",
        "book_name": "Book",
        "available_quantity": "Quantidade Disponível",
        "borrowed_quantity": "Quantidade Tomada",
        "collateral_quantity": "Quantidade em Garantia",
        "currency_exchange_rate": "Câmbio",
        "price": "Preço",
        "exposure_value": "Valor de Exposição",
        "pct_asset_value": "Exposição %",
        "pct_net_asset_value": "VL Financeiro %",
        "asset_value": "Vl. Financeiro",
        "last_asset_value": "Vl. Financeiro D-1",
        "duration": "Duração",
        "rate": "Taxa",
        "accrued_interest": "Juros Acumulados",
        "price_date": "Dt. Início",
        "last_price": "Preço D-1",
        "last_exposure_value": "Valor de Exposição D-1",
        "attribution.portfolio_beta.financial_value": "PnL Beta",
        "attribution_portfolio_beta_percentage": "Repetido_attribution_portfolio_beta_percentage",
        "attribution_portfolio_beta_financial": "Repetido_attribution_portfolio_beta_financial",
        "attribution.portfolio_beta.percentage_value": "PnL % Beta",
        "attribution.total.financial_value": "PnL Total",
        "attribution.total.percentage_value": "PnL % Total",
        "attribution_total_financial": "Repetido_attribution_total_financial",
        "attribution_total_percentage": "Repetido_attribution_total_percentage",
        "attribution.currency.financial_value": "PnL Moeda",
        "attribution.currency.percentage_value": "PnL % Moeda",
        "attribution_currency_financial": "Repetido_attribution_currency_financial",
        "attribution_currency_percentage": "Repetido_attribution_currency_percentage",
        "quantity": "Quantidade",
        "unsettled_quantity": "Quantidade não liquidada",
        "delta_price": "Preço %",
        "price_information_type_id": "Repetido_price_information_type_id",
        "overview_date": "Repetido_overview_date",
        "original_currency_id": "ID da moeda original",
        "lent_quantity": "Quantidade Doada",
        "lent_position_percentage": "Posição Doada %",
        "exposure_unit_value": "Preço Exposição",
        "currency_exchange_rate_date": "Câmbio (Data)",
        "currency_exchange_rate_instrument_id": "Câmbio (ID)",
        "book_id": "Book ID",
        "average_term": "Prazo Médio",
        "attribution.total_hedged.percentage_value": "Repetido_attribution.total_hedged.percentage_value",
        "attribution.total_hedged.financial_value": "Repetido_attribution.total_hedged.financial_value",
        "corp_actions_adj_factor": "Fator de Ajuste por Eventos Societários",
        "attribution.corp_actions.financial_value": "PnL Eventos Societários",
        "attribution.corp_actions.percentage_value": "PnL % Eventos Societários",
        "attribution.par_price.financial_value": "PnL Preço de Paridade",
        "attribution.par_price.percentage_value": "PnL % Preço de Paridade",
        "lending_unsettled_quantity": "Quantidade a Liquidar (Empréstimo)",
        "total_investment": "Investimento Total",
        "account_id": "Repetido_account_id",
        "account_name": "Repetido_account_name",
        "accrued_interest_admin_id": "Repetido_accrued_interest_admin_id",
        "accrued_interest_contract_id": "Repetido_accrued_interest_contract_id",
        "accrued_interest_date": "Repetido_accrued_interest_date",
        "accrued_interest_portfolio_id": "Repetido_accrued_interest_portfolio_id",
        "acquisition_rate": "Repetido_acquisition_rate",
        "adtv": "Repetido_adtv",
        "sector_name": "Setor",
        "sector_id": "Setor ID",
        "issuer_name": "Emissor",
        "issuer_id": "Emissor ID"
    }
    ORDEM_COLUNAS = [
        "Ticker",
        "Nome",
        "Tipo do Ticker",
        "Quantidade",
        "Preço",
        "Vl. Financeiro",
        # ...adicione mais se desejar...
    ]

    st.title("Carteira - Ativos")
    carteira_nome = st.selectbox(
        "Selecione a carteira",
        options=list(CARTEIRAS.values()),
        key="carteira_select"
    )
    carteira_id = [k for k, v in CARTEIRAS.items() if v == carteira_nome]
    data_hoje = date.today()

    if carteira_id:
        payload = {
            "start_date": str(data_hoje),
            "end_date": str(data_hoje),
            "instrument_position_aggregation": 3,
            "portfolio_ids": carteira_id
        }
        try:
            r = requests.post(
                f"{BASE_URL_API}/portfolio_position/positions/get",
                json=payload,
                headers=st.session_state.headers
            )
            r.raise_for_status()
            resultado = r.json()
            dados = resultado.get("objects", {})

            registros = []
            for item in dados.values():
                if isinstance(item, list):
                    registros.extend(item)
                else:
                    registros.append(item)

            df = pd.json_normalize(registros)
            df_ativos = pd.DataFrame()
            if "instrument_positions" in df.columns:
                lista_ativos = []
                for lista in df["instrument_positions"]:
                    if isinstance(lista, list) and lista:
                        df_tmp = pd.json_normalize(lista)
                        lista_ativos.append(df_tmp)
                if lista_ativos:
                    df_ativos = pd.concat(lista_ativos, ignore_index=True)

            if not df_ativos.empty:
                df_ativos = df_ativos.dropna(axis=1, how="all")
                df_ativos = df_ativos.rename(columns=MAPA_RENOMEACAO_ATIVOS)
                df_ativos = df_ativos[[col for col in df_ativos.columns if "repetido" not in col.lower()]]
                colunas_ordenadas = [col for col in ORDEM_COLUNAS if col in df_ativos.columns]
                colunas_restantes = [col for col in df_ativos.columns if col not in colunas_ordenadas]
                ordem_final = colunas_ordenadas + colunas_restantes
                df_ativos = df_ativos[ordem_final]

                # ------- CORREÇÃO: só formata colunas realmente numéricas -------
                for col in df_ativos.columns:
                    col_convertida = pd.to_numeric(df_ativos[col], errors="coerce")
                    if col_convertida.notnull().any():
                        df_ativos[col] = col_convertida.round(2).map(lambda x: "{:,.2f}".format(x) if pd.notnull(x) else "")
                # ---------------------------------------------------------------

                # Exibir todas as linhas
                pd.set_option('display.max_rows', len(df_ativos))

                # === Destaque vermelho para valores negativos ===
                def highlight_negative(val):
                    try:
                        val_float = float(str(val).replace(",", "").replace(" ", ""))
                        if val_float < 0:
                            return "color: red;"
                    except:
                        pass
                    return ""

                # Só aplica nas colunas numéricas
                colunas_numericas = [
                    col for col in df_ativos.columns
                    if pd.to_numeric(df_ativos[col].str.replace(",", "").str.replace(" ", ""), errors="coerce").notnull().any()
                ]

                df_styled = df_ativos.style.applymap(
                    highlight_negative,
                    subset=colunas_numericas
                )

                st.dataframe(df_styled, use_container_width=True)

            else:
                st.info("Nenhum ativo encontrado para a carteira e data informada.")
        except Exception as e:
            st.error(f"Erro ao buscar dados: {e}")
    else:
        st.info("Selecione uma carteira para visualizar os ativos.")