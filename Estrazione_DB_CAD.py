import streamlit as st
import pandas as pd
import io
from modules.Funzione_csv import carica_csv
from modules.Funzione_dati import funzione_dati
from modules.Funzione_grafico_streamlit import grafico_ofx_multipli
from modules.Funzione_grafico_recap import *

st.set_page_config(
    layout="wide",
    page_title="Elaborazione CSV pareti",
    page_icon="🚀")
st.title("Elaborazione CSV estratto da Autocad")

tab1, tab2, tab3 = st.tabs(["Riassunto progetto", "Comparazione DB", "Verifiche macro"])
with tab1:
    with st.container():
        # Layout a colonne
        col1, col2 = st.columns(2)
        with col1:
            st.header("Carica il file")
            uploaded_file = st.file_uploader("Carica file CSV estratto da Autocad senza elaborazioni (grezzo), dopo elaborazione puoi scaricare Excel.", type=["csv"])
            ### FUNZIONE
            if uploaded_file is not None:
                df=carica_csv(uploaded_file)
                prod_df=funzione_dati(df)
            ### FINE FUNZIONE  
            # Esporta in Excel in memoria
                output = io.BytesIO()
                prod_df.to_excel(output, index=False)
                output.seek(0)
                subcol1, subcol2 = st.columns([3,1])  # Nested columns
                with subcol2:
                    st.download_button(
                        label="Scarica Excel elaborato",
                        data=output,
                        file_name="Estrazione_DB_CAD.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")   
        with col2:
            st.header("Riassunto componenti progetto")
            if uploaded_file is not None:
                grouped_df=prod_df.groupby(["FLR","GRUPPO"], dropna=False)[["Q.TA","MQ","ML"]].sum(numeric_only=False).reset_index()
                st.dataframe(grouped_df, height=470)        
        with col1:
            if uploaded_file is not None:
                grouped_df_tot=(prod_df.groupby(["FLR","GRUPPO", "TIP.COM"])
                [["Q.TA"]].sum().reset_index())
                grafico_treemap(grouped_df_tot)
if uploaded_file is not None:
    with tab2:
        with st.container():
            # Layout a colonne
            col3, col4 = st.columns(2)

            with col3:
                st.subheader("Dati originali")
                st.dataframe(df)
            with col4:
                st.subheader("Dati elaborati")
                st.dataframe(prod_df)

    with tab3:
        grafico_ofx_multipli(prod_df,chart_key="ofx_chart_1")
