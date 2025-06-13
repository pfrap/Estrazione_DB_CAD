import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")
st.title("Estrazione DB CAD da CSV Autocad")

# Layout a colonne
col1, col2 = st.columns(2)

with col1:
    st.header("Carica il file")
    uploaded_file = st.file_uploader("Carica il file CSV esportato da Autocad", type=["csv"])
with col2:
    st.header("Info")
    st.write("Carica file CSV estratto da Autocad senza elaborazioni (grezzo), dopo elaborazione puoi scaricare Excel.")

### FUNZIONE    
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Rinomina colonne se presenti
    if "Nome" in df.columns:
        df.rename(columns={"Nome": "Name", "Conteggio": "Count"}, inplace=True)

    # Creazione colonna GRUPPO
    df.loc[df["Name"] == "2015-ETICHETTE VETRI", "GRUPPO"] = "VETRI"
    if "TIPO" in df.columns:
        df.loc[df["TIPO"].str.contains("T", na=False), "GRUPPO"] = "VETRI PORTE"
    if "L.TOT.1" in df.columns and "L.TOT." in df.columns:
        df.loc[df["L.TOT."].isnull(), "L.TOT."] = df["L.TOT.1"]

    # Arrotondamenti
    for col in ["L.1", "L.2", "L.3"]:
        if col in df.columns:
            df[col] = round(df[col] / 0.5) * 0.5

    if "L.TOT." in df.columns:
        df["L.TOT."].fillna(0, inplace=True)
        df["L.TOT."] = (round(df["L.TOT."] / 0.5) * 0.5).astype(float)

    if "HGT" in df.columns:
        df["HGT"].fillna(0, inplace=True)
        df["HGT"] = round(df["HGT"]).astype(int)

    if "A.N." in df.columns:
        df["A.N."].fillna(0, inplace=True)
        df["A.N."] = round(df["A.N."]).astype(int)

    # Rinomina colonne
    if "Count" in df.columns:
        df.rename(columns={"Count": "Q.TA"}, inplace=True)

    # Sostituisci valori vuoti
    df.fillna(".", inplace=True)

    if "L.TOT." in df.columns:
        df.loc[df["L.TOT."] == 0, "L.TOT."] = "."
    if "HGT" in df.columns:
        df.loc[df["HGT"] == 0, "HGT"] = "."
    if "A.N." in df.columns:
        df.loc[df["A.N."] == 0, "A.N."] = "."

    # Colonne desiderate e creazione se mancanti
    desired_columns = ['GRUPPO', 'TIP.COM', 'HND', 'A.N.', 'HGT', 'L.TOT.', 'L.1', 'L.2', 'L.3',
                       'N01', 'TIPO', 'FINITURA', 'POSIZIONE VETRO ', 'N.PROSPETTO', 'OFX',
                       'FLR', 'N.CARTIGLIO', 'Q.TA']
    
    for col in desired_columns:
        if col not in df.columns:
            df[col] = "."
    prod_df = df.loc[:, desired_columns]

    # Ordina righe
    prod_df.sort_values(by=["GRUPPO", "TIP.COM", "A.N.", "HGT", "L.TOT.", "L.1"], inplace=True)

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
    with col2:
        st.header("Riassunto componenti progetto")
        grouped_df=prod_df.groupby(["GRUPPO"], dropna=False)["Q.TA"].sum().reset_index()
        st.dataframe(grouped_df)
    
    st.markdown("---")
    st.subheader("Dati originali")
    st.dataframe(df)

    st.subheader("Dati elaborati")
    st.dataframe(prod_df)
    
    st.markdown("---")

### VERIFICHE PRE-PRODUZIONE
    col3, col4, col5 = st.columns(3)
    prod_df["GRUPPO"] = prod_df["GRUPPO"].astype(str).str.strip()

    with col3:
        st.subheader("Pivot per verifica porte")
        filtered_df = prod_df[prod_df["GRUPPO"].isin(["P", "HAP", "VP"])]
        pivot_ofx_doors = pd.pivot_table(
            filtered_df,
            values="Q.TA",
            index=["FLR", "N.PROSPETTO", "OFX", "GRUPPO", "TIP.COM", "A.N.", "HND"],
            aggfunc="sum")
        pivot_ofx_doors = pivot_ofx_doors.reset_index()  # Fondamentale per Streamlit
        pivot_ofx_doors = pivot_ofx_doors.astype(str).replace("nan", "")  # Rende tutto stringa, evita errori
    
        st.dataframe(pivot_ofx_doors)

    with col4:
        st.subheader("Pivot per verifica assi N e quantità pezzi")
        grouped_ofx_an = prod_df[prod_df["GRUPPO"].isin(["P", "VP"])]
        grouped_ofx_an = pd.pivot_table(
            filtered_df,
            values="Q.TA",
            index=["FLR", "N.PROSPETTO", "OFX", "GRUPPO", "A.N."],
            aggfunc="sum")
        grouped_ofx_an
