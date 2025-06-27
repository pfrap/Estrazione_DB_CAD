import streamlit as st
import pandas as pd
import plotly.express as px
from modules.Funzione_rainbow import *
import numpy as np

def grafico_ofx_multipli(df):
    
    if df.empty:
        st.warning("❗Nessun dato con GRUPPO in ['P', 'VP', 'HAP'].")
        return
    
    # Selezione singola FLR
    flr_disponibili = sorted(df['FLR'].dropna().unique())
    selezione_flr = st.selectbox("Seleziona un FLR", flr_disponibili)

    df = df[df['FLR'] == selezione_flr]

    # Selezione multipla OFX (filtrati sui FLR scelti)
    ofx_disponibili = sorted(df['OFX'].dropna().unique())
    selezione_ofx = st.multiselect("Seleziona OFX", ofx_disponibili, default=ofx_disponibili)

    if not selezione_ofx:
        st.info("👈 Seleziona almeno un OFX per visualizzare il grafico.")
        return

    df_filtrato = df[df['OFX'].isin(selezione_ofx)]

    #Concatenazione per TIPCOM
    df_filtrato['Label_TIPCOM'] = (
    df_filtrato['GRUPPO'].astype(str) + ' - ' +
    df_filtrato['TIP.COM'].astype(str))

    ############## DB FILTRATO IN BASE A PIANO E UFFICIO ##############
    
    ############## ORA PROSEGUIRE FILTRI IN BASE A COMPONENTI ##############
    # DATAFRAME DI PARTENZA: df_filtrato
    
    # Filtro su elementi metri lineari
    gruppi_target_ml = ['HA','HA2','HA3','HAP','HB','HB2','HB3', 'TR','TR2', "P"]
    df_filtrato_ml=df_filtrato[df_filtrato['GRUPPO'].isin(gruppi_target_ml)]
    # Raggruppamento dataframe per controllo metri lineari di parete
    grouped_ml= (
        df_filtrato_ml
        .groupby(["GRUPPO"])["ML"].sum()
        .reset_index())

    # Filtro su elementi porta
    gruppi_target = ['P', 'VP', 'HAP']
    df_filtrato_porte = df_filtrato[df_filtrato['GRUPPO'].isin(gruppi_target)]
    # Raggruppamento dataframe per controllo su porte per ufficio
    grouped_porte = (
        df_filtrato_porte
        .groupby(['OFX', "GRUPPO","TIP.COM","A.N.","HND"])["Q.TA"].sum()
        .reset_index())
    grouped_HND = ( 
            df_filtrato_porte
            .groupby(['OFX', "GRUPPO","TIP.COM","HND"])["Q.TA"].sum()
            .reset_index())
    grouped_AN_porte = (df_filtrato_porte.groupby(["OFX","GRUPPO","TIP.COM","A.N."])["Q.TA"].sum()
                  .reset_index())

    ############## INIZIO SCRITTURA DEL LAYOUT EFFETTIVO ##############

    # Altezza in UI streamlit dei grafici
    Altezza_grafici=400

    col1, col2=st.columns(2)
    def safe_extract_ml(df, gruppo):
                try:
                    return round(df.loc[df["GRUPPO"] == gruppo, "ML"].values[0], 2)
                except IndexError:
                    return 0
    with col1:
                
        ml_HA1=safe_extract_ml(grouped_ml, "HA")
        ml_HA2=safe_extract_ml(grouped_ml, "HA2")
        ml_HA3=safe_extract_ml(grouped_ml, "HA3")
        ml_TR1=safe_extract_ml(grouped_ml, "TR")
        ml_TR2=safe_extract_ml(grouped_ml, "TR2")
        ml_HAP=safe_extract_ml(grouped_ml, "HAP")
        ml_HB1=safe_extract_ml(grouped_ml, "HB")
        ml_HB2=safe_extract_ml(grouped_ml, "HB2")
        ml_HB3=safe_extract_ml(grouped_ml, "HB3")

        ml_HA=ml_HA1+ml_HA2+ml_HA3
        ml_HB=ml_HB1+ml_HB2+ml_HB3
        ml_TR=ml_TR1+ml_TR2

        ml_P=safe_extract_ml(grouped_ml, "P")
        
        rainbow_text(f"HA+HAP: {ml_HA+ml_HAP} ≈ TR {ml_TR} ≈ HB+P: {ml_HB+ml_P}", tag="h2")
        st.write("La somma di HA e HAP deve dare circa la lunghezza del TR e circa la somma di HB e L Porte.")

    with col2:

        filtri_includi = ['TR', 'HA', 'HB', "P"]
        pattern_includi = '|'.join(filtri_includi)

        filtri_escludi = ['VETRI',"VP"]
        pattern_escludi = '|'.join(filtri_escludi)

        df_filtrato_orizzontali = df[
            df['GRUPPO'].str.contains(pattern_includi, na=False) & 
            ~df['GRUPPO'].str.contains(pattern_escludi, na=False)
        ]
        
        # Raggruppa e somma
        grouped_df = (
            df_filtrato_orizzontali
            .groupby(["FLR", "GRUPPO"], dropna=False)[["Q.TA", "ML"]]
            .sum(numeric_only=False)
            .reset_index()
        )
        st.subheader("Riassunto metri lineari di parete")
        st.dataframe(grouped_df, height=350)

    st.header("Verifica Asse N porte")
    col3, col4=st.columns(2)

    with col3:
    
        # Grafico per confronto AN
        #st.subheader("Verifica Asse N porte")
        fig = px.bar(
        grouped_AN_porte[~grouped_AN_porte["GRUPPO"].str.contains("HAP")],
        x='OFX',
        y='Q.TA',
        #facet_col="OFX",
        color="A.N.",
        barmode='group',
        text='A.N.',
        hover_name=None,
        hover_data={"GRUPPO":True,"TIP.COM":True,"A.N.":True,"Q.TA":False}
        )
        fig.update_traces()
        fig.update_layout(height=Altezza_grafici)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.dataframe(grouped_porte, height=520)
        # Grafico per confronto HND
    st.header("Verifica HND porte")
    fig = px.bar(
    grouped_HND,
    x='OFX',
    y='Q.TA',
    #facet_col="OFX",
    color="HND",
    barmode='group',
    text='HND',
    hover_name=None,
    hover_data={"GRUPPO":True,"TIP.COM":True,"Q.TA":False}
    )
    fig.update_traces()
    fig.update_layout(height=Altezza_grafici)

    if isinstance(selezione_ofx, (list, tuple, np.ndarray)):
        key_plot = f"grafico_hnd_{selezione_flr}_{'_'.join(map(str, selezione_ofx))}"
    elif selezione_ofx is not None:
        key_plot = f"grafico_hnd_{selezione_flr}_{str(selezione_ofx)}"
    else:
        key_plot = f"grafico_hnd_{selezione_flr}_none"

    st.plotly_chart(fig, use_container_width=True, key=key_plot)
