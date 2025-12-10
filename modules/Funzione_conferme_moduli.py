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

def trasferisci_dati(
    df_origine,
    df_destinazione,
    mapping_singolo=None,
    mapping_concat=None,
    start_row=3,      # riga da cui cominciare a scrivere (0-based → 3 = riga 4)
    sep_concat="",    # separatore tra colonne concatenate
    mapping_fisso=None  # dizionario colonna: valore fisso
):
    df_dest = df_destinazione.copy()
    n_orig = len(df_origine)

    # 1️⃣ Assicura che df_dest abbia abbastanza righe
    if len(df_dest) < start_row + n_orig:
        righe_mancanti = (start_row + n_orig) - len(df_dest)
        df_extra = pd.DataFrame("", index=range(righe_mancanti), columns=df_dest.columns)
        df_dest = pd.concat([df_dest, df_extra], ignore_index=True)

    # 2️⃣ Scrittura colonne singole (skip valori vuoti, ".", NaN)
    if mapping_singolo:
        for col_orig, col_dest in mapping_singolo.items():
            if col_orig in df_origine.columns and col_dest in df_dest.columns:
                valori = df_origine[col_orig].astype(str).fillna("")
                mask = pd.notna(df_origine[col_orig]) & (valori != "") & (valori != ".")
                df_dest.loc[start_row:start_row+n_orig-1, col_dest] = [
                    v if m else df_dest.loc[i, col_dest]
                    for i, (v, m) in enumerate(zip(valori, mask), start=start_row)
                ]
            else:
                st.warning(f"Colonna non trovata: {col_orig} → {col_dest}")

    # 3️⃣ Scrittura colonne concatenate (skip valori vuoti, ".", NaN)
# 3️⃣ Scrittura colonne concatenate (skip valori vuoti, ".", NaN)
    if mapping_concat:
        for col_dest, lista in mapping_concat.items():

            risultati = []  # risultato finale per ogni riga

            for idx in range(n_orig):

                pezzi_validi = []  # pezzi non vuoti per la riga corrente

                for c in lista:

                    # TEXT: valore fisso
                    if isinstance(c, str) and c.startswith("TEXT:"):
                        valore = c.replace("TEXT:", "")

                    # prefisso:colonna
                    elif isinstance(c, str) and ":" in c:
                        prefisso, col = c.split(":", 1)
                        if col in df_origine.columns:
                            v = df_origine.loc[idx, col]
                            if pd.notna(v) and str(v) not in ("", "."):
                                valore = prefisso + str(v)
                            else:
                                valore = ""
                        else:
                            valore = ""

                    # colonna normale
                    else:
                        if c in df_origine.columns:
                            v = df_origine.loc[idx, c]
                            if pd.notna(v) and str(v) not in ("", "."):
                                valore = str(v)
                            else:
                                valore = ""
                        else:
                            valore = ""

                    # aggiungi solo se valido
                    if valore != "":
                        pezzi_validi.append(valore)

                # unisci SOLO i pezzi validi con separatore (es: " - ")
                risultati.append(sep_concat.join(pezzi_validi))

            # scrivi i valori nel dataframe destinazione
            df_dest.loc[start_row:start_row+n_orig-1, col_dest] = risultati

    # 4️⃣ Scrittura colonne con valore fisso
    if mapping_fisso:
        for col, val in mapping_fisso.items():
            if col in df_dest.columns:
                df_dest.loc[start_row:start_row+n_orig-1, col] = val
            else:
                st.warning(f"Colonna destinazione per valore fisso non trovata: {col}")

    return df_dest

