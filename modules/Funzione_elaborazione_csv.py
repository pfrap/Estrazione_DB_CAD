import pandas as pd

# Colonne finali attese nell'app (se mancano vengono create)
COLONNE_BASE = [
    "FAMIGLIA","GRUPPO","ARTICOLO","DESCRIZIONE","TIP.COM","HND","A.N.","HGT","L.TOT.","L.1","L.2","L.3",
    "N01","N02","N03","TIPO","FINITURA","POSIZIONE VETRO ","N.PROS","OFX","FLR","N.CART","Q.TA","MQ","ML"
]

def _safe_round_half(series: pd.Series) -> pd.Series:
    """Arrotonda ai 0.5 (es: 123.2 -> 123.0, 123.3 -> 123.5)."""
    s = pd.to_numeric(series, errors="coerce")
    return (s / 0.5).round() * 0.5

def _normalizza_colonne(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Filtra solo elementi utili
    if "Name" in df.columns:
        mask = df["Name"].astype(str).str.contains("VETRI|PANNELLI|Profili", case=False, na=False)
        df = df[mask].copy()

        # Gruppo base
        df.loc[df["Name"].astype(str).str.contains("VETRI", case=False, na=False), "GRUPPO"] = "VETRI"
        df.loc[df["Name"].astype(str).str.contains("PANNELLI", case=False, na=False), "GRUPPO"] = "PANNELLI"

    # Eccezione porte (TIPO contiene 'T')
    if "TIPO" in df.columns:
        df.loc[df["TIPO"].astype(str).str.contains("T", na=False), "GRUPPO"] = "VETRI PORTE"

    # Colonne duplicate da export diversi
    if "L.TOT.1" in df.columns and "L.TOT." in df.columns:
        df["L.TOT."] = df["L.TOT."].where(df["L.TOT."].notna(), df["L.TOT.1"])
    if "H." in df.columns and "HGT" in df.columns:
        df["HGT"] = df["HGT"].where(df["HGT"].notna(), df["H."])
    if "N.FLOOR" in df.columns and "FLR" in df.columns:
        df["FLR"] = df["FLR"].where(df["FLR"].notna(), df["N.FLOOR"])
    if "N.OFFICE" in df.columns and "OFX" in df.columns:
        df["OFX"] = df["OFX"].where(df["OFX"].notna(), df["N.OFFICE"])
    if "NOTE" in df.columns and "N01" in df.columns:
        df["N01"] = df["N01"].where(df["N01"].notna(), df["NOTE"])

    # NOTE-1 / NOTE-2
    df = df.rename(columns={"NOTE-1": "N02", "NOTE-2": "N03"})

    # Normalizzazione nomi colonne N.PROSPETTO → N.PROS, N.CARTIGLIO → N.CART
    df = df.rename(columns={"N.PROSPETTO": "N.PROS", "N.CARTIGLIO": "N.CART"})

    # Count -> Q.TA
    if "Count" in df.columns:
        df = df.rename(columns={"Count": "Q.TA"})

    return df

def _calcola_misure(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Arrotondamenti L.1/2/3 e principali
    for col in ["L.1", "L.2", "L.3"]:
        if col in df.columns:
            df[col] = _safe_round_half(df[col])

    for col in ["L.TOT.", "HGT", "A.N."]:
        if col in df.columns:
            df[col] = _safe_round_half(df[col])

    # MQ vetri
    if {"HGT","L.TOT.","GRUPPO"}.issubset(df.columns):
        mask = df["GRUPPO"].astype(str).str.contains("VETRI|VETRO|PA|TE|PANNELLO", na=False)
        df.loc[mask, "MQ"] = (
            pd.to_numeric(df.loc[mask, "HGT"], errors="coerce") *
            pd.to_numeric(df.loc[mask, "L.TOT."], errors="coerce")
        ) / 1_000_000

    # ML profili
    if {"L.TOT.","GRUPPO"}.issubset(df.columns):
        mask = df["GRUPPO"].astype(str).str.contains("HA|HB|TR|HI|P|VETRI|VETRO", na=False)
        df.loc[mask, "ML"] = pd.to_numeric(df.loc[mask, "L.TOT."], errors="coerce") / 1000

    return df

def _garantisci_colonne(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in COLONNE_BASE:
        if col not in df.columns:
            df[col] = pd.NA
    return df

def _finalizza(df: pd.DataFrame, sort_cols) -> pd.DataFrame:
    df = df.copy()
    df = df.loc[:, COLONNE_BASE]

    # Ordinamento stabile
    df = df.sort_values(by=sort_cols, kind="mergesort")

    # Normalizza GRUPPO
    df["GRUPPO"] = df["GRUPPO"].astype(str).str.strip()

    # Nell'app si usa spesso '.' come placeholder: lo mettiamo SOLO alla fine
    df = df.fillna(".")

    # Per compatibilità: quando numerici erano 0 mettevate '.'
    for col in ["L.TOT.", "HGT", "A.N."]:
        if col in df.columns:
            df.loc[df[col].astype(str) == "0.0", col] = "."
            df.loc[df[col].astype(str) == "0", col] = "."

    return df

def funzione_dati(df: pd.DataFrame) -> pd.DataFrame:
    """Elabora il CSV grezzo da Autocad e restituisce il DB produzione."""
    df = _normalizza_colonne(df)
    df = _calcola_misure(df)
    df = _garantisci_colonne(df)
    return _finalizza(df, sort_cols=["GRUPPO", "TIP.COM", "A.N.", "HGT", "L.TOT.", "L.1"])

def funzione_dati_xlsx(df: pd.DataFrame) -> pd.DataFrame:
    """Elabora un DB già in Excel (già quasi pronto) e ricalcola misure."""
    df = _calcola_misure(df)
    df = _garantisci_colonne(df)
    return _finalizza(df, sort_cols=["FAMIGLIA","ARTICOLO","DESCRIZIONE","GRUPPO","TIP.COM","A.N.","HGT","L.TOT.","L.1"])
