import streamlit as st
import pandas as pd
import io

from modules.Funzioni_caricamento_file import carica_csv, carica_xlsx
from modules.Funzione_elaborazione_csv import funzione_dati, funzione_dati_xlsx
from modules.Grafico_verifiche import grafico_ofx_multipli
from modules.Grafico_recap import grafico_treemap
from modules.Funzione_conferme_layout import tab_conferme


st.set_page_config(layout="wide", page_title="Codifica pareti", page_icon="🚀")
st.title("Codifica pareti")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Riassunto progetto", "Comparazione DB", "Verifiche macro", "Codifica articoli"]
)

def reset_state_for_new_file(file_name: str):
    """Reset mirato: evita st.session_state.clear() (troppo distruttivo)."""
    keys_to_reset = [
        "prod_df_edit",
        "import_as400",
        "import_as400_template",
        "editor_as400",
        "filtro_gruppo",
        "filtro_tipcom",
    ]
    for k in keys_to_reset:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state["nome_file_caricato"] = file_name

# -----------------------------
# TAB 1: upload + recap
# -----------------------------
with tab1:
    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            st.header("Carica il file")
            tab1a, tab1b = st.tabs(["Carica CSV", "Carica XLSX"])

            with tab1a:
                uploaded_csv = st.file_uploader(
                    "Carica file CSV estratto da Autocad senza elaborazioni (grezzo). Dopo elaborazione puoi scaricare Excel.",
                    type=["csv"],
                    key="uploader_csv",
                )

            with tab1b:
                uploaded_xlsx = st.file_uploader(
                    "Carica file excel già elaborato.",
                    type=["xlsx"],
                    key="uploader_xlsx",
                )

            prod_df = None
            df_originale = None

            if uploaded_csv is not None:
                df_originale = carica_csv(uploaded_csv)
                prod_df = funzione_dati(df_originale)
                file_name = uploaded_csv.name

                if st.session_state.get("nome_file_caricato") != file_name:
                    reset_state_for_new_file(file_name)

            if uploaded_xlsx is not None:
                df_excel = carica_xlsx(uploaded_xlsx)
                prod_df = funzione_dati_xlsx(df_excel)
                file_name = uploaded_xlsx.name

                if st.session_state.get("nome_file_caricato") != file_name:
                    reset_state_for_new_file(file_name)

            # Download Excel elaborato SOLO se upload CSV (per XLSX è già elaborato)
            if uploaded_csv is not None and prod_df is not None:
                output = io.BytesIO()
                prod_df.to_excel(output, index=False)
                output.seek(0)
                _, subcol2 = st.columns([3, 1])
                with subcol2:
                    st.download_button(
                        label="Scarica Excel elaborato",
                        data=output,
                        file_name="Estrazione_DB_CAD.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

# -----------------------------
# TAB 2/3/4: mostrati solo se c'è un DB
# -----------------------------
if prod_df is not None:
    # TAB 1 col2: recap + treemap
    with tab1:
        with col2:
            st.header("Riassunto componenti progetto")
            grouped_df = (
                prod_df.groupby(["FLR", "FAMIGLIA", "GRUPPO", "ARTICOLO"], dropna=False)[["Q.TA", "MQ", "ML"]]
                .sum(numeric_only=False)
                .reset_index()
            )
            st.dataframe(grouped_df, height=470)

        with col1:
            grouped_df_tot = (
                prod_df.groupby(["FLR", "FAMIGLIA", "GRUPPO", "ARTICOLO", "TIP.COM"])[["Q.TA"]]
                .sum()
                .reset_index()
            )
            grafico_treemap(grouped_df_tot)

    # TAB 3
    with tab3:
        grafico_ofx_multipli(prod_df)

    # TAB 4
    with tab4:
        tab_conferme(prod_df)

    # TAB 2 (comparazione) solo se hai un CSV con originale
    if df_originale is not None:
        with tab2:
            with st.container():
                col3, col4 = st.columns(2)
                with col3:
                    st.subheader("Dati originali")
                    st.dataframe(df_originale)
                with col4:
                    st.subheader("Dati elaborati")
                    st.dataframe(prod_df)
else:
    with tab4:
        st.info("Carica un CSV o un XLSX nel Tab 'Riassunto progetto' per procedere con la codifica articoli.")
