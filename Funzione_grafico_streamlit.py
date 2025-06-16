import streamlit as st
import pandas as pd
import plotly.express as px

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
    gruppi_target_ml = ['HA', 'HB', 'TR', "P"]
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
    with col1:
        _="""st.dataframe(grouped_ml)
        ml_HA=grouped_ml.loc[grouped_ml["GRUPPO"]=="HA", "ML"].values[0]
        ml_TR=grouped_ml.loc[grouped_ml["GRUPPO"]=="TR", "ML"].values[0]

        st.write(f"**L'HA misura {ml_HA}**")
        st.write(f"**Il TR misura {ml_TR}**")
        st.write(f"**TR+HA {ml_TR+ml_HA}**")
Implementare ulteriormente il sommario di verifica ml
"""

        # Grafico per confronto AN
        fig = px.bar(
        grouped_AN_porte[~grouped_AN_porte["GRUPPO"].str.contains("HAP")],
        x='OFX',
        y='Q.TA',
        #facet_col="OFX",
        color="A.N.",
        barmode='group',
        text='A.N.',
        title="Verifica Asse N porte",
        hover_name=None,
        hover_data={"GRUPPO":True,"TIP.COM":True,"A.N.":True,"Q.TA":False}
        )
        fig.update_traces()
        fig.update_layout(height=Altezza_grafici)
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.dataframe(grouped_porte)
    
    # Grafico per confronto HND
    fig = px.bar(
    grouped_HND,
    x='OFX',
    y='Q.TA',
    #facet_col="OFX",
    color="HND",
    barmode='group',
    text='HND',
    title="Verifica HND porte",
    hover_name=None,
    hover_data={"GRUPPO":True,"TIP.COM":True,"Q.TA":False}
    )
    fig.update_traces()
    fig.update_layout(height=Altezza_grafici)
    st.plotly_chart(fig, use_container_width=True)
