import pandas as pd

 # Creazione colonna GRUPPO
def funzione_dati(df):
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

# Metri quadri di vetro
    mask = df["GRUPPO"].str.contains("VETRI|VETRO", na=False)
    df.loc[mask, "MQ"] = (
        (pd.to_numeric(df.loc[mask, "HGT"], errors="coerce") *
        pd.to_numeric(df.loc[mask, "L.TOT."], errors="coerce"))/1000000
    )
    # Colonne desiderate e creazione se mancanti
    desired_columns = ['GRUPPO', 'TIP.COM', 'HND', 'A.N.', 'HGT', 'L.TOT.', 'L.1', 'L.2', 'L.3',
                       'N01', 'TIPO', 'FINITURA', 'POSIZIONE VETRO ', 'N.PROSPETTO', 'OFX',
                       'FLR', 'N.CARTIGLIO', 'Q.TA', "MQ"]
    
    for col in desired_columns:
        if col not in df.columns:
            df[col] = "."
    prod_df = df.loc[:, desired_columns]

    # Ordina righe
    prod_df.sort_values(by=["GRUPPO", "TIP.COM", "A.N.", "HGT", "L.TOT.", "L.1"], inplace=True)
    return prod_df