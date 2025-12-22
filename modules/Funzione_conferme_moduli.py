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
    start_row=3,        # riga da cui cominciare a scrivere (0-based)
    sep_concat="",      # separatore tra pezzi concatenati
    mapping_fisso=None  # dizionario colonna: valore fisso
):
    df_dest = df_destinazione.copy()

    # >>> FONDAMENTALE: lavoriamo per POSIZIONE, non per label dell'indice
    df_src = df_origine.reset_index(drop=True).copy()
    n_orig = len(df_src)

    # 1) Assicura che df_dest abbia abbastanza righe
    needed_len = start_row + n_orig
    if len(df_dest) < needed_len:
        righe_mancanti = needed_len - len(df_dest)
        df_extra = pd.DataFrame("", index=range(righe_mancanti), columns=df_dest.columns)
        df_dest = pd.concat([df_dest, df_extra], ignore_index=True)

    # helper: valore valido?
    def is_valid(x) -> bool:
        if pd.isna(x):
            return False
        s = str(x).strip()
        return s not in ("", ".")

    # 2) MAPPING SINGOLO (coerente per riga)
    if mapping_singolo:
        for col_orig, col_dest in mapping_singolo.items():
            if col_orig not in df_src.columns:
                st.warning(f"Colonna origine non trovata: {col_orig}")
                continue
            if col_dest not in df_dest.columns:
                st.warning(f"Colonna destinazione non trovata: {col_dest}")
                continue

            src_col = df_src[col_orig]
            dest_slice = []

            for i in range(n_orig):
                v = src_col.iat[i]
                # se non valido, non sovrascrivere (lascia il template)
                if is_valid(v):
                    dest_slice.append(str(v).strip())
                else:
                    dest_slice.append(df_dest.at[start_row + i, col_dest])

            df_dest.loc[start_row:start_row + n_orig - 1, col_dest] = dest_slice

    # 3) MAPPING CONCAT (coerente per riga, separatore SOLO tra valori validi)
    if mapping_concat:
        for col_dest, lista in mapping_concat.items():
            if col_dest not in df_dest.columns:
                st.warning(f"Colonna destinazione concat non trovata: {col_dest}")
                continue

            risultati = []

            for i in range(n_orig):
                pezzi_validi = []

                for token in lista:
                    # testo fisso
                    if isinstance(token, str) and token.startswith("TEXT:"):
                        txt = token.replace("TEXT:", "")
                        if txt != "":
                            pezzi_validi.append(txt)
                        continue

                    # prefisso:colonna (attenzione: questa sintassi entra anche per "OFX:OFX")
                    if isinstance(token, str) and ":" in token:
                        prefisso, col_name = token.split(":", 1)
                        col_name = col_name.strip()
                        if col_name in df_src.columns:
                            v = df_src[col_name].iat[i]   # <<< POSIZIONALE
                            if is_valid(v):
                                pezzi_validi.append(f"{prefisso}{str(v).strip()}")
                        else:
                            st.warning(f"Colonna per concatenazione non trovata: {col_name}")
                        continue

                    # colonna normale
                    if token in df_src.columns:
                        v = df_src[token].iat[i]        # <<< POSIZIONALE
                        if is_valid(v):
                            pezzi_validi.append(str(v).strip())
                    else:
                        st.warning(f"Colonna per concatenazione non trovata: {token}")

                risultati.append(sep_concat.join(pezzi_validi))

            df_dest.loc[start_row:start_row + n_orig - 1, col_dest] = risultati

    # 4) VALORI FISSI (su tutte le righe generate)
    if mapping_fisso:
        for col, val in mapping_fisso.items():
            if col in df_dest.columns:
                df_dest.loc[start_row:start_row + n_orig - 1, col] = val
            else:
                st.warning(f"Colonna destinazione per valore fisso non trovata: {col}")

    return df_dest

def check_coerenza_trasferimento(
    df_origine,
    df_destinazione,
    start_row,
    mapping_check
):
    """
    mapping_check = {
        "ARTICOLO": "XLSCDAR",
        "N01": "XLSNOT3",
        ...
    }
    """
    df_src = df_origine.reset_index(drop=True)
    df_dst = df_destinazione.reset_index(drop=True)

    errori = []

    n = len(df_src)

    for i in range(n):
        r_src = df_src.iloc[i]
        r_dst = df_dst.iloc[start_row + i]

        for col_src, col_dst in mapping_check.items():
            v_src = r_src.get(col_src)
            v_dst = r_dst.get(col_dst)

            # normalizzazione
            v_src = "" if pd.isna(v_src) else str(v_src).strip()
            v_dst = "" if pd.isna(v_dst) else str(v_dst).strip()

            if v_src != "" and v_src != ".":
                if v_src not in v_dst:
                    errori.append({
                        "riga_produzione": i,
                        "riga_as400": start_row + i,
                        "col_origine": col_src,
                        "valore_origine": v_src,
                        "col_dest": col_dst,
                        "valore_dest": v_dst
                    })

    return pd.DataFrame(errori)

def build_mapping_check(mapping_singolo=None, mapping_concat=None):
    """
    Ritorna un mapping {col_origine: col_dest}
    SOLO per le colonne effettivamente trasferite.
    """
    mapping_check = {}

    # colonne singole
    if mapping_singolo:
        for col_orig, col_dest in mapping_singolo.items():
            mapping_check[col_orig] = col_dest

    # colonne concatenate
    if mapping_concat:
        for col_dest, lista in mapping_concat.items():
            for token in lista:
                if isinstance(token, str) and ":" in token:
                    _, col_orig = token.split(":", 1)
                    mapping_check[col_orig.strip()] = col_dest
                elif isinstance(token, str) and token.startswith("TEXT:"):
                    # testo fisso → non va controllato
                    continue

    return mapping_check
