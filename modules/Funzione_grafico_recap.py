import plotly.express as px
import streamlit as st
import pandas as pd


def grafico_recap(df):
    fig = px.bar(
        df,
        x="FLR",         # piani
        y="Q.TA",        # quantità
        color="GRUPPO",  # elementi
        title="Composizione del progetto per piano",
        barmode="stack",
        text_auto=True
    )
    fig.update_traces()
    fig.update_layout()
    st.plotly_chart(fig, use_container_width=True)

def grafico_sunburst(df):
    fig = px.sunburst(
        df,
        path=["FLR", "GRUPPO", "TIP.COM"],
        values="Q.TA",  # Quantità da sommare
        color="GRUPPO",  # O anche "Q.TA" per scala continua
        #color_continuous_scale="Viridis",  # puoi usare anche: "Blues", "Plasma", "Cividis", ecc.
        hover_data=["Q.TA"],  # Dati aggiuntivi nei tooltip
        title="Composizione del progetto: Piano → Gruppo → Tipo Componente",
        )
    fig.update_layout(
        margin=dict(t=50, l=25, r=25, b=25)
        )
    st.plotly_chart(fig, use_container_width=True)

def grafico_treemap(df):
    fig = px.treemap(
        df,
        path=["FLR", "GRUPPO", "TIP.COM"],
        values="Q.TA",
        color="GRUPPO",
        #color_continuous_scale="Sunsetdark", #Plasma Agsunset Sunsetdark Inferno
        color_discrete_sequence=px.colors.qualitative.Set2,  # oppure: Set1, Pastel1, Bold, etc.
        hover_data={"Q.TA": True},
        #title="Composizione del progetto"
        )
    fig.update_layout(height=320,margin=dict(t=0, b=0, l=10, r=10))
    st.plotly_chart(fig,use_container_width=True)