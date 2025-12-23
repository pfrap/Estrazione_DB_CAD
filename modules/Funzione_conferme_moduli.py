import pandas as pd
import streamlit as st

ARTICOLI_XLSX_PATH = "data/Articoli.xlsx"

def df_to_nested_dict(path: str = ARTICOLI_XLSX_PATH) -> dict:
    """Carica Articoli.xlsx e crea dizionario annidato per le selectbox."""
    df = pd.read_excel(path, dtype=str)

    key_cols = ["MACRO_SISTEMA", "SISTEMA", "C1", "C2", "CONCAT_3"]
    value_cols = ["NEUTRO_CONFERME", "ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE", "IMMAGINE_NOME_FILE"]

    nested = {}
    for _, row in df.iterrows():
        d = nested
        for k in key_cols[:-1]:
            d = d.setdefault(row.get(k, ""), {})
        d[row.get(key_cols[-1], "")] = {c: row.get(c, "") for c in value_cols}
    return nested


def aggiorna_articoli(prod_df: pd.DataFrame) -> pd.DataFrame:
    """Per GRUPPO che inizia con H o TR: ARTICOLO = ARTICOLO[:-2] + TIP.COM."""
    df = prod_df.copy()

    required = {"GRUPPO", "ARTICOLO", "TIP.COM"}
    if not required.issubset(df.columns):
        st.error("Colonne richieste mancanti: GRUPPO, ARTICOLO, TIP.COM.")
        return prod_df

    mask = df["GRUPPO"].astype(str).str.startswith(("H", "TR"), na=False)
    if not mask.any():
        st.warning("Nessuna riga con GRUPPO che inizia per H o TR.")
        return prod_df

    articolo = df.loc[mask, "ARTICOLO"].astype(str)
    tipcom = df.loc[mask, "TIP.COM"].astype(str)

    # Se articolo ha almeno 2 caratteri: sostituisce le ultime 2
    df.loc[mask, "ARTICOLO"] = articolo.str.slice(0, -2).fillna("") + tipcom

    st.success(f"Aggiornate {int(mask.sum())} righe della colonna ARTICOLO (GRUPPO: H*, TR*).")
    return df


def importa_as400(
    df_origine: pd.DataFrame,
    df_template: pd.DataFrame,
    mapping_orig_to_dest: dict,
    start_row: int = 2,
    mapping_fisso: dict | None = None,
) -> pd.DataFrame:
    """
    Copia colonne da df_origine in df_template usando un mapping semplice.
    mapping_orig_to_dest: { 'ARTICOLO': 'XLSCDAR', ... }
    """
    df_out = df_template.copy().reset_index(drop=True)
    df_src = df_origine.reset_index(drop=True)

    needed_len = start_row + len(df_src)
    if len(df_out) < needed_len:
        extra = pd.DataFrame("", index=range(needed_len - len(df_out)), columns=df_out.columns)
        df_out = pd.concat([df_out, extra], ignore_index=True)

    for col_src, col_dst in mapping_orig_to_dest.items():
        if col_src not in df_src.columns:
            st.warning(f"Colonna origine non trovata: {col_src}")
            continue
        if col_dst not in df_out.columns:
            st.warning(f"Colonna destinazione non trovata: {col_dst}")
            continue

        values = df_src[col_src].astype(str).fillna(" ").map(lambda x: x.strip())
        df_out.loc[start_row:start_row + len(df_src) - 1, col_dst] = values.values

    if mapping_fisso:
        for col_dst, val in mapping_fisso.items():
            if col_dst in df_out.columns:
                df_out.loc[start_row:start_row + len(df_src) - 1, col_dst] = val
            else:
                st.warning(f"Colonna destinazione per valore fisso non trovata: {col_dst}")

    return df_out


def verifica_as400(
    df_origine: pd.DataFrame,
    df_destinazione: pd.DataFrame,
    mapping_orig_to_dest: dict,
    start_row: int = 2,
) -> pd.DataFrame:
    """Controlla che ogni valore origine sia riportato nella colonna AS400 corrispondente."""
    df_src = df_origine.reset_index(drop=True)
    df_dst = df_destinazione.reset_index(drop=True)

    errori = []
    n = len(df_src)

    for i in range(n):
        for col_src, col_dst in mapping_orig_to_dest.items():
            if col_src not in df_src.columns or col_dst not in df_dst.columns:
                continue

            v_src = df_src.at[i, col_src]
            v_dst = df_dst.at[start_row + i, col_dst] if (start_row + i) < len(df_dst) else ""

            v_src = "" if pd.isna(v_src) else str(v_src).strip()
            v_dst = "" if pd.isna(v_dst) else str(v_dst).strip()

            if v_src and v_src != ".":
                if v_src not in v_dst:
                    errori.append({
                        "riga_produzione": i,
                        "riga_as400": start_row + i,
                        "col_origine": col_src,
                        "valore_origine": v_src,
                        "col_dest": col_dst,
                        "valore_dest": v_dst,
                    })

    return pd.DataFrame(errori)


# --- Backward compatibility (se qualche file usa ancora i nomi vecchi) ---

def trasferisci_dati(df_origine, df_destinazione, mapping_singolo=None, mapping_concat=None,
                    start_row=3, sep_concat="", mapping_fisso=None):
    """Wrapper compatibilità: ignora mapping_concat (rifattorizzato)."""
    if mapping_concat:
        st.info("Nota: mapping_concat non è più usato. Aggiorna il tracciato AS400 per avere colonne 1:1.")
    return importa_as400(
        df_origine=df_origine,
        df_template=df_destinazione,
        mapping_orig_to_dest=mapping_singolo or {},
        start_row=start_row,
        mapping_fisso=mapping_fisso
    )

def check_coerenza_trasferimento(df_origine, df_destinazione, start_row, mapping_check):
    return verifica_as400(df_origine, df_destinazione, mapping_check, start_row=start_row)

def build_mapping_check(mapping_singolo=None, mapping_concat=None):
    # ora è banale: coincide col mapping singolo
    return dict(mapping_singolo or {})

import pandas as pd

import pandas as pd


def prepara_colonne_as400(prod_df):
    """
    Prende il DataFrame di produzione (prod_df_edit) e:
    1) Crea XLSNOT1 e XLSNOT2 con concatenazioni
    2) Crea XLSALTZ e XLSLRGH secondo le regole date
    3) Ritorna un nuovo DataFrame
    """

    df = prod_df.copy()

    # -------------------------------------------------
    # 1) XLSNOT1 e XLSNOT2 (inizializzazione)
    # -------------------------------------------------
    df["XLSNOT1"] = ""
    df["XLSNOT2"] = ""

    # -------------------------------------------------
    # 2) XLSALTZ e XLSLRGH (inizializzazione)
    # -------------------------------------------------
    df["XLSALTZ"] = ""
    df["XLSLRGH"] = ""

    # -------------------------------------------------
    # Loop riga per riga (CHIARO E LEGGIBILE)
    # -------------------------------------------------
    for idx, row in df.iterrows():

        # ---------- XLSNOT1 ----------
        parts_not1 = []

        val = row.get("N.PROSPETTO")
        if pd.notna(val) and str(val).strip() not in ("", ".", "0", "0.0"):
            parts_not1.append(f"EL: {val}")

        val = row.get("OFX")
        if pd.notna(val) and str(val).strip() not in ("", ".", "0", "0.0"):
            parts_not1.append(f"OFX: {val}")

        val = row.get("FLR")
        if pd.notna(val) and str(val).strip() not in ("", ".", "0", "0.0"):
            parts_not1.append(f"FLR: {val}")

        val = row.get("N.CARTIGLIO")
        if pd.notna(val) and str(val).strip() not in ("", ".", "0", "0.0"):
            parts_not1.append(f"DRW: {val}")

        df.at[idx, "XLSNOT1"] = "/".join(parts_not1)

        # ---------- XLSNOT2 ----------
        parts_not2 = []

        val = row.get("L.1")
        if pd.notna(val) and str(val).strip() not in ("", ".", "0", "0.0"):
            parts_not2.append(f"L1={val}")

        val = row.get("L.2")
        if pd.notna(val) and str(val).strip() not in ("", ".", "0", "0.0"):
            parts_not2.append(f"L2={val}")

        val = row.get("L.3")
        if pd.notna(val) and str(val).strip() not in ("", ".", "0", "0.0"):
            parts_not2.append(f"L3={val}")

        df.at[idx, "XLSNOT2"] = "/".join(parts_not2)

        # ---------- XLSALTZ ----------
        altz_val = ""

        val = row.get("A.N.")
        num = pd.to_numeric(val, errors="coerce")
        if pd.notna(num) and num != 0:
            altz_val = num
        else:
            val = row.get("HGT")
            num = pd.to_numeric(val, errors="coerce")
            if pd.notna(num) and num != 0:
                altz_val = num

        df.at[idx, "XLSALTZ"] = altz_val

        # ---------- XLSLRGH ----------
        val = row.get("L.TOT.")
        num = pd.to_numeric(val, errors="coerce")
        if pd.notna(num):
            df.at[idx, "XLSLRGH"] = num
        else:
            df.at[idx, "XLSLRGH"] = ""

    return df
