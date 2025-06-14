import streamlit as st
import pandas as pd
import io
from Funzione_csv import carica_csv
from Funzione_dati import funzione_dati
from Funzione_grafico_streamlit import grafico_ofx_multipli

st.set_page_config(layout="wide")
st.title("Elaborazione CSV estratto da Autocad")

tab1, tab2, tab3 = st.tabs(["Riassunto progetto", "Comparazione DB", "Verifiche macro"])
with tab1:
    with st.container():
        # Layout a colonne
        col1, col2 = st.columns(2)
        with col1:
            st.header("Carica il file")
            uploaded_file = st.file_uploader("Carica file CSV estratto da Autocad senza elaborazioni (grezzo), dopo elaborazione puoi scaricare Excel.", type=["csv"])
        with col2:
            st.header("Overview")

### FUNZIONE
if uploaded_file is not None:
    df=carica_csv(uploaded_file)
    prod_df=funzione_dati(df)
### FINE FUNZIONE
    
    # Esporta in Excel in memoria
    output = io.BytesIO()
    prod_df.to_excel(output, index=False)
    output.seek(0)

    with col1:
        subcol1, subcol2 = st.columns([3,1])  # Nested columns
        with subcol2:
            st.download_button(
                label="Scarica Excel elaborato",
                data=output,
                file_name="Estrazione_DB_CAD.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")    

    with col1:
        st.header("Riassunto componenti progetto")
        grouped_df=prod_df.groupby(["FLR","GRUPPO"], dropna=False)[["Q.TA","MQ","ML"]].sum(numeric_only=False).reset_index()
        st.dataframe(grouped_df)
          
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
    ### VERIFICHE PRE-PRODUZIONE
        _="""col6, col7 = st.columns(2)

        with col6:
            st.subheader("Pivot per verifica assi N e quantità pezzi")
            grouped_ofx_an_filtered = prod_df[prod_df["GRUPPO"].isin(["P", "VP"])]
            grouped_ofx_an = pd.pivot_table(
                grouped_ofx_an_filtered,
                values="Q.TA",
                index=["FLR", "N.PROSPETTO", "OFX", "GRUPPO", "A.N."],
                aggfunc="sum")
            grouped_ofx_an = grouped_ofx_an.reset_index()  # Fondamentale per Streamlit
            grouped_ofx_an = grouped_ofx_an.astype(str).replace("nan", "")  # Rende tutto stringa, evita errori
            st.dataframe(grouped_ofx_an)
            
        with col7:
            st.subheader("Pivot per verifica tipi e mani")
            grouped_ofx_mani_filtered = prod_df[prod_df["GRUPPO"].isin(["P", "HAP", "VP"])]
            grouped_ofx_mani = pd.pivot_table(
                grouped_ofx_mani_filtered,
                values="Q.TA",
                index=["FLR", "N.PROSPETTO", "OFX", "GRUPPO","TIP.COM","HND"],
                aggfunc="sum")
            grouped_ofx_mani = grouped_ofx_mani.reset_index()  # Fondamentale per Streamlit
            grouped_ofx_mani = grouped_ofx_mani.astype(str).replace("nan", "")  # Rende tutto stringa, evita errori
            st.dataframe(grouped_ofx_mani)"""
    #grafico_streamlit(prod_df)
        grafico_ofx_multipli(prod_df)