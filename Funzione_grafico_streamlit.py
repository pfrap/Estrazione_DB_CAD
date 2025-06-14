import streamlit as st
import pandas as pd
import plotly.express as px

def grafico_ofx_multipli(df):
    # Filtro su elementi porta
    gruppi_target = ['P', 'VP', 'HAP']
    df = df[df['GRUPPO'].isin(gruppi_target)]

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
    
    #Concatenazione per A.N.
    df_filtrato['Label_AN'] = (
    df_filtrato['GRUPPO'].astype(str) + ' - ' +
    df_filtrato['A.N.'].astype(str))
    
    #Concatenazione per HND
    df_filtrato['Label_HND'] = (
    df_filtrato['GRUPPO'].astype(str) + ' - ' +
    df_filtrato['HND'].astype(str))
    
    #Concatenazione per TIPCOM
    df_filtrato['Label_TIPCOM'] = (
    df_filtrato['GRUPPO'].astype(str) + ' - ' +
    df_filtrato['TIP.COM'].astype(str))
   
    # Raggruppamento
    grouped = (
        df_filtrato
        .groupby(['FLR', 'OFX', "GRUPPO","TIP.COM","A.N.","HND", "Label_AN","Label_HND"])
        .size()
        .reset_index(name='Q.TA')
    )
    
    # Altezza in UI streamlit dei grafici
    Altezza_grafici=350

    # Grafico per confronto AN
    fig = px.bar(
    grouped[~grouped["GRUPPO"].str.contains("HAP")],
    x='OFX',
    y='Q.TA',
    facet_col="FLR",
    color="Label_AN",
    barmode='group',
    text='Q.TA',
    title="Verifica Asse N",
    hover_name=None,
    hover_data={"GRUPPO":True,"A.N.":True,"HND":False, "FLR":False,"Label_AN":False,"OFX":False,"Q.TA":False}
    )
    fig.update_traces()
    fig.update_layout(height=Altezza_grafici)
    st.plotly_chart(fig, use_container_width=True)

    # Grafico per confronto HND
    fig = px.bar(
    grouped,
    x='OFX',
    y='Q.TA',
    facet_col="FLR",
    color="Label_HND",
    barmode='group',
    text='Q.TA',
    title="Verifica HND",
    hover_name=None,
    hover_data={"GRUPPO":True,"A.N.":False,"HND":True, "FLR":False,"Label_HND":False,"OFX":False,"Q.TA":False}
    )
    fig.update_traces()
    fig.update_layout(height=Altezza_grafici)
    st.plotly_chart(fig, use_container_width=True)
    
    # Dataframe per verifiche
    st.dataframe(grouped[['FLR', 'OFX', "GRUPPO","TIP.COM","A.N.","HND", "Q.TA"]])
