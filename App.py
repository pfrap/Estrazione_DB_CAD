import streamlit as st
import pandas as pd
import io
from modules.Funzioni_caricamento_file import *
from modules.Funzione_elaborazione_csv import *
from modules.Grafico_verifiche import grafico_ofx_multipli
from modules.Grafico_recap import *
from modules.Funzione_conferme_layout import *

st.set_page_config(
    layout="wide",
    page_title="Codifica pareti",
    page_icon="🚀")
st.title("Codifica pareti")

tab1, tab2, tab3, tab4 = st.tabs(["Riassunto progetto", "Comparazione DB", "Verifiche macro", "Codifica articoli"])
###
### PARTE DI CARICAMENTO FILE E GRAFICO RECAP ###
###
with tab1:
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.header("Carica il file")
            tab1a, tab1b= st.tabs(["Carica CSV", "Carica XLSX"])
            with tab1a:
                uploaded_file = st.file_uploader("Carica file CSV estratto da Autocad senza elaborazioni (grezzo), dopo elaborazione puoi scaricare Excel.", 
                                                 type=["csv"],
                                                 key="uploader_csv")
            with tab1b:
                uploaded_file_xlsx = st.file_uploader("Carica file excel già elaborato.", 
                                                      type=["xlsx"],
                                                      key="uploader_xlsx")

            ### FUNZIONE
            if uploaded_file is not None:
                df = carica_csv(uploaded_file)
                df_originale = df
                prod_df = funzione_dati(df)
                file_name = uploaded_file.name

                # 🔁 Se cambia file, resettiamo il contenuto di tab_conferme
                if ("nome_file_caricato" not in st.session_state or st.session_state["nome_file_caricato"] != file_name):
                    st.session_state.clear()
                    st.session_state["nome_file_caricato"] = file_name
                    uploaded_file_xlsx=None
                    if "prod_df_edit" in st.session_state:
                        del st.session_state["prod_df_edit"]

            ### FUNZIONE EXCEL
            if uploaded_file_xlsx is not None:
                df_excel = carica_xlsx(uploaded_file_xlsx)
                prod_df=funzione_dati_xlsx(df_excel)
                file_name = uploaded_file_xlsx.name

                # 🔁 Se cambia file, resettiamo il contenuto di tab_conferme
                if ("nome_file_caricato" not in st.session_state or st.session_state["nome_file_caricato"] != file_name):
                    st.session_state.clear()
                    st.session_state["nome_file_caricato"] = file_name
                    uploaded_file=None
                    if "prod_df_edit" in st.session_state:
                        del st.session_state["prod_df_edit"]

            ### FINE FUNZIONE  
            # Esporta in Excel in memoria
            if uploaded_file is not None:
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
                    
if uploaded_file is not None or uploaded_file_xlsx is not None:
    with col2:
        st.header("Riassunto componenti progetto")
        grouped_df=prod_df.groupby(["FLR","FAMIGLIA","GRUPPO","ARTICOLO"], dropna=False)[["Q.TA","MQ","ML"]].sum(numeric_only=False).reset_index()
        st.dataframe(grouped_df, height=470)        
    with col1:
        grouped_df_tot=(prod_df.groupby(["FLR","FAMIGLIA","GRUPPO", "ARTICOLO","TIP.COM"])
        [["Q.TA"]].sum().reset_index())

        #Funzione con grafico treemap per resoconto
        grafico_treemap(grouped_df_tot)
                
    ###
    ### PARTE DI CONTROLLO TRAMITE GRAFICI APPOSITI ###
    ###
    with tab3:
        grafico_ofx_multipli(prod_df)

    ###
    ### PARTE DI CODIFICA POST ESTRAZIONE E IMPORT TRACCIATO AS400 ###
    ###
    with tab4:
        tab_conferme(prod_df)
        
if uploaded_file is not None:
    with tab2:
        with st.container():
            col3, col4 = st.columns(2)

            with col3:
                st.subheader("Dati originali")
                st.dataframe(df_originale)
            with col4:
                st.subheader("Dati elaborati")
                st.dataframe(prod_df)

if uploaded_file_xlsx is None and uploaded_file is None:
    with tab4:
        col4a, col4b = st.columns(2)
        with col4a:
            uploaded_file_conf = st.file_uploader("Carica file excel con codici per conferma già elaborati.", 
                                                type=["xlsx"],
                                                    key="uploader_conf")
        if uploaded_file_conf is not None:
            df_excel_conf = pd.read_excel(uploaded_file_conf)
            tab_conferme(df_excel_conf)
