import pandas as pd

# Modifica di prova
# Creazione colonna GRUPPO
def funzione_dati(df):
    df = df[df['Name'].str.contains("VETRI|PANNELLI|Profili", case=False, na=False)]
    df.loc[df['Name'].str.contains('VETRI'), "GRUPPO"] = "VETRI"
    df.loc[df['Name'].str.contains('PANNELLI'), "GRUPPO"] = "PANNELLI"

    if "TIPO" in df.columns:
        df.loc[df["TIPO"].astype(str).str.contains("T", na=False), "GRUPPO"] = "VETRI PORTE"
    if "L.TOT.1" in df.columns and "L.TOT." in df.columns:
        df.loc[df["L.TOT."].isnull(), "L.TOT."] = df["L.TOT.1"]
    if "H." in df.columns and "HGT" in df.columns:
        df.loc[df["HGT"].isnull(), "HGT"] = df["H."]
    if "N.FLOOR" in df.columns and "FLR" in df.columns:
        df.loc[df["FLR"].isnull(), "FLR"] = df["N.FLOOR"]
    if "N.OFFICE" in df.columns and "OFX" in df.columns:
        df.loc[df["OFX"].isnull(), "OFX"] = df["N.OFFICE"]
    if "NOTE" in df.columns and "N01" in df.columns:
        df.loc[df["N01"].isnull(), "N01"] = df["NOTE"]
    
    df.rename(columns={"NOTE-1": "N02", "NOTE-2": "N03"}, inplace=True)

    # Arrotondamenti
    for col in ["L.1", "L.2", "L.3"]:
        if col in df.columns:
            df[col] = round(df[col] / 0.5) * 0.5

    if "L.TOT." in df.columns:
        df["L.TOT."].fillna(0, inplace=True)
        df["L.TOT."] = (round(df["L.TOT."] / 0.5) * 0.5).astype(float)

    if "HGT" in df.columns:
        df["HGT"].fillna(0, inplace=True)
        df["HGT"] = (round(df["HGT"]/ 0.5)*0.5).astype(float)

    if "A.N." in df.columns:
        df["A.N."].fillna(0, inplace=True)
        df["A.N."] = (round(df["A.N."] / 0.5) * 0.5).astype(float)

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
    if "HGT" in df.columns:
        mask = df["GRUPPO"].str.contains("VETRI|VETRO|PA|TE|PANNELLO", na=False)
        df.loc[mask, "MQ"] = (
            (pd.to_numeric(df.loc[mask, "HGT"], errors="coerce") *
            pd.to_numeric(df.loc[mask, "L.TOT."], errors="coerce"))/1000000)
    
    # Metri lineari di profili
    mask = df["GRUPPO"].str.contains("HA|HB|TR|HI|P|VETRI|VETRO", na=False)
    df.loc[mask, "ML"] = pd.to_numeric(df.loc[mask, "L.TOT."], errors="coerce")/1000
    
    # Colonne desiderate e creazione se mancanti
    if "N03" in df.columns:
        desired_columns = ['GRUPPO', 'TIP.COM', 'HND', 'A.N.', 'HGT', 'L.TOT.', 'L.1', 'L.2', 'L.3',
                       'N01','N02','N03', 'TIPO', 'FINITURA', 'POSIZIONE VETRO ', 'N.PROSPETTO', 'OFX',
                       'FLR', 'N.CARTIGLIO', 'Q.TA', "MQ","ML"]
    else:
        desired_columns = ['GRUPPO', 'TIP.COM', 'HND', 'A.N.', 'HGT', 'L.TOT.', 'L.1', 'L.2', 'L.3',
                       'N01', 'TIPO', 'FINITURA', 'POSIZIONE VETRO ', 'N.PROSPETTO', 'OFX',
                       'FLR', 'N.CARTIGLIO', 'Q.TA', "MQ","ML"]
    
    for col in desired_columns:
        if col not in df.columns:
            df[col] = "."
    prod_df = df.loc[:, desired_columns]

    # Ordina righe
    prod_df.sort_values(by=["GRUPPO", "TIP.COM", "A.N.", "HGT", "L.TOT.", "L.1"], inplace=True)
    prod_df["GRUPPO"] = prod_df["GRUPPO"].astype(str).str.strip()
    return prod_df

def funzione_dati_xlsx(df): 
    # Metri quadri di vetro
    if "HGT" in df.columns:
        mask = df["GRUPPO"].str.contains("VETRI|VETRO|PA|TE|PANNELLO", na=False)
        df.loc[mask, "MQ"] = (
            (pd.to_numeric(df.loc[mask, "HGT"], errors="coerce") *
            pd.to_numeric(df.loc[mask, "L.TOT."], errors="coerce"))/1000000)
    
    # Metri lineari di profili
    mask = df["GRUPPO"].str.contains("HA|HB|TR|HI|P|VETRI|VETRO", na=False)
    df.loc[mask, "ML"] = pd.to_numeric(df.loc[mask, "L.TOT."], errors="coerce")/1000
    
    # Colonne desiderate e creazione se mancanti
    if "N03" in df.columns:
        desired_columns = ['GRUPPO', 'TIP.COM', 'HND', 'A.N.', 'HGT', 'L.TOT.', 'L.1', 'L.2', 'L.3',
                       'N01','N02','N03', 'TIPO', 'FINITURA', 'POSIZIONE VETRO ', 'N.PROSPETTO', 'OFX',
                       'FLR', 'N.CARTIGLIO', 'Q.TA', "MQ","ML"]
    else:
        desired_columns = ['GRUPPO', 'TIP.COM', 'HND', 'A.N.', 'HGT', 'L.TOT.', 'L.1', 'L.2', 'L.3',
                       'N01', 'TIPO', 'FINITURA', 'POSIZIONE VETRO ', 'N.PROSPETTO', 'OFX',
                       'FLR', 'N.CARTIGLIO', 'Q.TA', "MQ","ML"]
    
    for col in desired_columns:
        if col not in df.columns:
            df[col] = "."
    prod_df = df.loc[:, desired_columns]

    # Ordina righe
    prod_df.sort_values(by=["GRUPPO", "TIP.COM", "A.N.", "HGT", "L.TOT.", "L.1"], inplace=True)
    prod_df["GRUPPO"] = prod_df["GRUPPO"].astype(str).str.strip()
    return prod_df