import pandas as pd
import streamlit as st

def df_to_nested_dict():
    """
    Trasforma un DataFrame Excel in un dizionario annidato:
    MACRO_SISTEMA → SISTEMA → C1 → C2 → CONCAT_3 → { valori }
    """
    df = pd.read_excel("data/Articoli.xlsx", dtype=str)

    key_columns = ["MACRO_SISTEMA", "SISTEMA", "C1", "C2", "CONCAT_3"]
    value_columns = [
        "NEUTRO_CONFERME",
        "ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE",
        "IMMAGINE_NOME_FILE",
    ]
    
    nested_dict = {}
    for _, row in df.iterrows():
        d = nested_dict
        for k in key_columns[:-1]:
            d = d.setdefault(row[k], {})
        d[row[key_columns[-1]]] = row[value_columns].to_dict()
    return nested_dict

import pandas as pd
import streamlit as st

def aggiorna_articoli(prod_df):
    """
    Filtra righe dove GRUPPO inizia con H o TR,
    e modifica la colonna ARTICOLO rimuovendo le ultime due cifre
    e concatenando TIP.COM al posto loro.
    """
    df = prod_df.copy()

    if not {"GRUPPO", "ARTICOLO", "TIP.COM"}.issubset(df.columns):
        st.error("Colonne richieste mancanti nel DataFrame (serve GRUPPO, ARTICOLO, TIP.COM).")
        return prod_df

    # Filtra righe che iniziano con H o TR
    mask = df["GRUPPO"].astype(str).str.startswith(("H", "TR"), na=False)
    df_filtrato = df[mask].copy()

    if df_filtrato.empty:
        st.warning("Nessuna riga trovata con GRUPPO che inizia per H o TR.")
        return prod_df

    modifiche = 0
    for idx, row in df_filtrato.iterrows():
        articolo = str(row["ARTICOLO"])
        tipcom = str(row["TIP.COM"])

        if len(articolo) >= 2:
            nuovo_articolo = articolo[:-2] + tipcom
        else:
            nuovo_articolo = articolo + tipcom  # fallback

        df.at[idx, "ARTICOLO"] = nuovo_articolo
        modifiche += 1

    st.success(f"Aggiornate {modifiche} righe della colonna ARTICOLO (GRUPPO: H*, TR*).")
    return df
