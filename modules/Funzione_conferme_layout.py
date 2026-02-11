import streamlit as st
import io
import pandas as pd

from modules.Funzione_conferme_moduli import *
from modules.Funzioni_caricamento_file import carica_xlsx

def _init_state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

def tab_conferme(prod_df: pd.DataFrame):
    """Tab 4: codifica articoli + generazione import AS400."""

    # ======================
    # Dizionario articoli (MACRO → SISTEMA → C1 → C2 → CONCAT_3)
    # ======================
    nested_dict = df_to_nested_dict()

    # ======================
    # Stato: DB produzione editabile
    # ======================

    _init_state("prod_df_edit", prod_df.copy())

    # garantisce colonne minime (FAMIGLIA e ARTICOLO vengono create se mancano)
    for col in ["FAMIGLIA", "ARTICOLO"]:
        if col not in st.session_state["prod_df_edit"].columns:
            st.session_state["prod_df_edit"][col] = ""

    ordine_colonne = [
        "FAMIGLIA","GRUPPO","ARTICOLO","TIP.COM","HND","A.N.","HGT","L.TOT.","L.1","L.2","L.3","N01","TIPO","FINITURA",
        "POSIZIONE VETRO ","N.PROSPETTO","OFX","FLR","N.CARTIGLIO","Q.TA","MQ","ML"
    ]
    df_edit = st.session_state["prod_df_edit"].reindex(columns=ordine_colonne).copy()

    # ======================
    # UI filtri + selezione dizionario
    # ======================
    col1, col2, col3 = st.columns([0.4, 0.2, 0.4], gap="small")

    with col1:
        st.subheader("Filtri database produzione")
        
        # Nuovi filtri nell'ordine richiesto
        famiglia_filter = st.text_input("Filtra per FAMIGLIA (regex fullmatch):", value="", key="filtro_famiglia")
        gruppo_filter = st.text_input("Filtra per GRUPPO (regex fullmatch):", value="", key="filtro_gruppo")
        articolo_filter = st.text_input("Filtra per ARTICOLO (regex fullmatch):", value="", key="filtro_articolo")
        tipcom_filter = st.text_input("Filtra per TIP.COM (regex fullmatch):", value="", key="filtro_tipcom")

        def filtra_df(df: pd.DataFrame) -> pd.DataFrame:
            out = df
            # Applicazione sequenziale dei filtri
            if famiglia_filter:
                out = out[out["FAMIGLIA"].astype(str).str.fullmatch(famiglia_filter, case=False, na=False)]
            if gruppo_filter:
                out = out[out["GRUPPO"].astype(str).str.fullmatch(gruppo_filter, case=False, na=False)]
            if articolo_filter:
                out = out[out["ARTICOLO"].astype(str).str.fullmatch(articolo_filter, case=False, na=False)]
            if tipcom_filter:
                out = out[out["TIP.COM"].astype(str).str.fullmatch(tipcom_filter, case=False, na=False)]
            return out

        filtered_df = filtra_df(df_edit)
        st.caption(f"Righe filtrate: {len(filtered_df)} / {len(df_edit)}")

        st.subheader("Seleziona articolo da dizionario")
        col_d1, col_d2, col_d3, col_d4, col_d5 = st.columns(5)

        with col_d1:
            filtro_macro = st.selectbox("MACRO_SISTEMA", [""] + sorted(nested_dict.keys()))
        with col_d2:
            macro_dict = nested_dict.get(filtro_macro, {}) if filtro_macro else {}
            filtro_sistema = st.selectbox("SISTEMA", [""] + sorted(macro_dict.keys()))
        with col_d3:
            c1_dict = macro_dict.get(filtro_sistema, {}) if filtro_sistema else {}
            filtro_c1 = st.selectbox("C1", [""] + sorted(c1_dict.keys()))
        with col_d4:
            c2_dict = c1_dict.get(filtro_c1, {}) if filtro_c1 else {}
            filtro_c2 = st.selectbox("C2", [""] + sorted(c2_dict.keys()))
        with col_d5:
            articoli_dict = c2_dict.get(filtro_c2, {}) if filtro_c2 else {}
            articoli_validi = list(articoli_dict.keys())
            concat3_scelto = st.selectbox("ARTICOLO", [""] + articoli_validi)

    # ======================
    # Anteprima articolo
    # ======================
    with col2:
        st.subheader("Anteprima articolo")

        if concat3_scelto:
            valori = articoli_dict.get(concat3_scelto, {})
            img = valori.get("IMMAGINE_NOME_FILE")
            if img:
                try:
                    st.image(img, caption=f"Anteprima: {concat3_scelto}", use_container_width=True)
                    st.markdown(
                        """
                        <style>
                        [data-testid="stImage"] img { height: 300px !important; object-fit: contain; }
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )
                except Exception:
                    st.warning(f"Immagine non trovata: {img}")
            else:
                st.info("Nessuna immagine disponibile per questo articolo.")

            descr = valori.get("ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE", "N/D")
            neutro = valori.get("NEUTRO_CONFERME", "N/D")
            st.markdown(f"**Descrizione:** {descr}  \n**Codice neutro conferme:** {neutro}")

    # ======================
    # Applica batch + editor + export
    # ======================
    with col3:
        st.subheader("Database produzione")
        edited_df = st.data_editor(
            filtered_df,
            use_container_width=True,
            height=500,
        )
    with col1:
        col_p1, col_p2, col_p3 = st.columns(3)

        with col_p1:
            if st.button("📦 Applica alle righe filtrate", key="batch_apply"):
                if filtered_df.empty or not concat3_scelto:
                    st.warning("Nessuna riga filtrata o articolo non selezionato.")
                else:
                    valori = articoli_dict.get(concat3_scelto, {})
                    neutro = valori.get("NEUTRO_CONFERME", "")
                    # aggiorna sul df_edit (stesse index)
                    df_edit.loc[filtered_df.index, "FAMIGLIA"] = filtro_sistema
                    df_edit.loc[filtered_df.index, "ARTICOLO"] = neutro
                    st.session_state["prod_df_edit"] = df_edit
                    st.success(f"Aggiornate {len(filtered_df)} righe.")
                    st.rerun()

        # scrive le modifiche nel db completo
        df_edit.loc[edited_df.index, edited_df.columns] = edited_df
        st.session_state["prod_df_edit"] = df_edit

        # export excel (sempre, con numerici corretti)
        df_to_export = df_edit.copy()
        numeric_cols = ["A.N.", "HGT", "L.TOT.", "L.1", "L.2", "L.3", "Q.TA", "MQ", "ML"]
        for c in numeric_cols:
            if c in df_to_export.columns:
                df_to_export[c] = pd.to_numeric(df_to_export[c], errors="coerce")

        out = io.BytesIO()
        df_to_export.to_excel(out, index=False)
        out.seek(0)

        with col_p2:
            if st.button("⚙️ Aggiorna articoli (H/TR)"):
                st.session_state["prod_df_edit"] = aggiorna_articoli(st.session_state["prod_df_edit"])
                st.rerun()

        with col_p3:
            st.download_button(
                label="📤 Esporta Excel finale",
                data=out,
                file_name="Estrazione_DB_CAD_edit.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # ======================
    # AS400: import semplice 1:1 (niente concatenazioni)
    # ======================
    st.divider()
    st.subheader("Elaborazione import AS400 (mapping semplice)")
    st.caption("Nota: ora l'AS400 è 1:1. Se ti servono campi concatenati, conviene crearli nel DB produzione come colonne dedicate.")

    # Template (immutabile) + versione editabile
    if "import_as400_template" not in st.session_state:
        st.session_state["import_as400_template"] = carica_xlsx("data/Tracciato_import_as400.xlsx")

    _init_state("import_as400", st.session_state["import_as400_template"].copy())

    # Mapping semplice (origine -> colonna AS400)
    mapping_singolo = {
        "ARTICOLO":"XLSCDAR",
        "HND":"XLSOP02",
        "XLSALTZ":"XLSALTZ",
        "XLSLRGH":"XLSLRGH",
        "FINITURA":"XLSOP01",
        "POSIZIONE VETRO ":"XLSNOT3",
        "Q.TA":"XLSQTOR",
        "XLSNOT1":"XLSNOT1",
        "XLSNOT2":"XLSNOT2",
    }

    mapping_fisso = {
        "XLSCBXB1": "012",
        "XLSCBXB2": "P25",
        "XLSVR01": "5FP",
        "XLSVR02": "5HN",
        "XLSVR03": "5LB",
    }

    colb1a, colb1b, _ = st.columns([0.25, 0.25, 0.5], gap="small")

    with colb1a:
        if st.button("🔄 Aggiorna AS400 da Database Produzione"):
            df_origine=prepara_colonne_as400(st.session_state["prod_df_edit"])

            st.session_state["import_as400"] = importa_as400(
                df_origine,
                df_template=st.session_state["import_as400_template"],
                mapping_orig_to_dest=mapping_singolo,
                start_row=2,
                mapping_fisso=mapping_fisso,
            )
            st.success("Dati import AS400 aggiornati.")
            st.rerun()

    # Verifica coerenza (solo colonne mappate)
    errori = verifica_as400(
        df_origine=st.session_state["prod_df_edit"],
        df_destinazione=st.session_state["import_as400"],
        mapping_orig_to_dest=mapping_singolo,
        start_row=2,
    )

    if not errori.empty:
        st.error(f"⚠️ Trovate {len(errori)} incongruenze nel trasferimento")
        st.dataframe(errori, use_container_width=True)
    else:
        st.success("✅ Coerenza OK sulle colonne trasferite")

    # Editor AS400
    edited_as400 = st.data_editor(
        st.session_state["import_as400"],
        use_container_width=True,
        num_rows="dynamic",
        key="editor_as400",
        height=600,
    )
    st.session_state["import_as400"] = edited_as400

    with colb1b:
        out_as400 = io.BytesIO()
        edited_as400.to_excel(out_as400, index=False)
        out_as400.seek(0)
        st.download_button(
            label="📤 Esporta AS400 elaborato",
            data=out_as400,
            file_name="AS400_elaborato.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )