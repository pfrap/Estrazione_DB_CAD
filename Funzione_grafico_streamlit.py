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
    #df_filtrato['GRUPPO'].astype(str) + ' - ' +
    df_filtrato['TIP.COM'].astype(str) + ' - ' +
    df_filtrato['HND'].astype(str))
    
    #Concatenazione per TIPCOM
    df_filtrato['Label_TIPCOM'] = (
    df_filtrato['GRUPPO'].astype(str) + ' - ' +
    df_filtrato['TIP.COM'].astype(str))
   
    # Raggruppamento dataframe
    grouped = (
        df_filtrato
        .groupby(['OFX', "GRUPPO","TIP.COM","A.N.","HND"])["Q.TA"].sum()
        .reset_index())
    grouped_HND = (
            df_filtrato
            .groupby(['OFX', "GRUPPO","TIP.COM","HND"])["Q.TA"].sum()
            .reset_index())
    grouped_AN = (df_filtrato.groupby(["OFX","GRUPPO","TIP.COM","A.N."])["Q.TA"].sum()
                  .reset_index())
    
    
    # Altezza in UI streamlit dei grafici
    Altezza_grafici=400

    # Colonne
    col1, col2=st.columns(2)
    with col1:
        # Grafico per confronto AN
        fig = px.bar(
        grouped_AN[~grouped_AN["GRUPPO"].str.contains("HAP")],
        x='OFX',
        y='Q.TA',
        #facet_col="OFX",
        color="A.N.",
        barmode='group',
        text='A.N.',
        title="Verifica Asse N sul piano",
        hover_name=None,
        hover_data={"GRUPPO":True,"TIP.COM":True,"A.N.":True,"Q.TA":False}
        )
        fig.update_traces()
        fig.update_layout(height=Altezza_grafici)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.dataframe(grouped)
    
    # Grafico per confronto HND
    fig = px.bar(
    grouped_HND,
    x='OFX',
    y='Q.TA',
    #facet_col="OFX",
    color="HND",
    barmode='group',
    text='HND',
    title="Verifica HND sul piano",
    hover_name=None,
    hover_data={"GRUPPO":True,"TIP.COM":True,"Q.TA":False}
    )
    fig.update_traces()
    fig.update_layout(height=Altezza_grafici)
    st.plotly_chart(fig, use_container_width=True)