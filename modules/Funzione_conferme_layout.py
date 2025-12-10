import streamlit as st
import io
from modules.Funzione_conferme_moduli import *
from modules.Funzioni_caricamento_file import *

import pandas as pd

def tab_conferme(prod_df):
    cont_a=st.container()
    cont_b=st.container()

    with cont_a:
        # ======================
        # Import dizionario annidato (MACRO_SISTEMA → SISTEMA → C1 → C2 → CONCAT_3)
        # ======================
        nested_dict = df_to_nested_dict()
        
        # --- Inizializzazione stato ---
        if "prod_df_edit" not in st.session_state:
            st.session_state["prod_df_edit"] = prod_df.copy()
            for col in ["FAMIGLIA", "ARTICOLO"]:
                if col not in st.session_state["prod_df_edit"].columns:
                    st.session_state["prod_df_edit"][col] = ""
        ordine_colonne=["FAMIGLIA","ARTICOLO","GRUPPO","TIP.COM","HND","A.N.","HGT","L.TOT.","L.1","L.2","L.3","N01","TIPO","FINITURA","POSIZIONE VETRO ","N.PROSPETTO","OFX",
                        "FLR","N.CARTIGLIO","Q.TA","MQ","ML"]
        prod_df_edit = st.session_state["prod_df_edit"][ordine_colonne]

        # ======================
        # Filtri DataFrame (visualizzazione)
        # ======================

        col1, col2, col3 = st.columns([0.4,0.2,0.4],gap="small")
        with col1:
            st.subheader("Filtri database produzione")            
            gruppo_filter = st.text_input("Filtra per GRUPPO:", value="", key="filtro_gruppo")
            tipcom_filter = st.text_input("Filtra per TIP.COM:", value="", key="filtro_tipcom")
            
            # Funzione riutilizzabile per applicare filtri
            def filtra_df(df):
                if gruppo_filter:
                    df = df[df["GRUPPO"].astype(str).str.fullmatch(gruppo_filter, case=False, na=False)]
                if tipcom_filter:
                    df = df[df["TIP.COM"].astype(str).str.fullmatch(tipcom_filter, case=False, na=False)]
                return df

            filtered_df = filtra_df(prod_df_edit.copy())
            st.write(f"Righe filtrate: {len(filtered_df)} / {len(prod_df_edit)}")

        # ======================
        # Filtri Dizionario (batch update)
        # ======================
        with col1:
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
                articoli_validi = list(articoli_dict.keys())  # chiavi = CONCAT_3
                concat3_scelto = st.selectbox("ARTICOLO", [""] + articoli_validi)

            col_p1, col_p2, col_p3 = st.columns(3)


        # ======================
        # ANTEPRIMA IMMAGINE (immediata)
        # ======================
        with col2:
            st.subheader("Anteprima articolo")
        if concat3_scelto:
            valori = articoli_dict.get(concat3_scelto)
            if valori and valori.get("IMMAGINE_NOME_FILE"):
                percorso_img = f"{valori['IMMAGINE_NOME_FILE']}"
                try:
                    with col2:
                        st.image(
                            percorso_img,
                            caption=f"Anteprima: {concat3_scelto}",
                            use_container_width=True,
                        )
                        # Forza altezza via CSS
                        st.markdown(
                            """
                            <style>
                            [data-testid="stImage"] img {
                                height: 300px !important;
                                object-fit: contain;
                            }
                            </style>
                            """,
                            unsafe_allow_html=True,
                        )
                        # Mostra descrizione e codice neutro conferme
                        descrizione = valori.get("ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE", "N/D")
                        neutro_conferme = valori.get("NEUTRO_CONFERME", "N/D")
                        st.markdown(f"**Descrizione:** {descrizione}  \n**Codice neutro conferme:** {neutro_conferme}")

                except Exception:
                    st.warning(f"Immagine non trovata: {percorso_img}")
            else:
                st.info("Nessuna immagine disponibile per questo articolo.")
        with col3:        
            # ======================
            # Applica batch update
            # ======================
            with col_p1:
                if st.button("📦 Applica alle righe filtrate", key="batch_apply"):
                    if filtered_df.empty or not concat3_scelto:
                        st.warning("Nessuna riga filtrata o articolo non selezionato")
                    else:
                        valori = articoli_dict.get(concat3_scelto)
                        if valori:
                            prod_df_edit.loc[filtered_df.index, "FAMIGLIA"] = filtro_sistema
                            prod_df_edit.loc[filtered_df.index, "ARTICOLO"] = valori["NEUTRO_CONFERME"]

                            # Aggiorna stato e forza refresh a video
                            st.session_state["prod_df_edit"] = prod_df_edit

                            st.success(
                                f"Aggiornate {len(filtered_df)} righe con "
                                f"Famiglia='{filtro_sistema}' e Articolo='{valori['NEUTRO_CONFERME']}'"
                            )
                            
                            st.rerun()  # Forza aggiornamento del DataFrame mostrato

            # ======================
            # Data editor (modifica manuale)
            # ======================
            st.subheader("Database produzione")
            edited_df = st.data_editor(
                filtered_df,
                use_container_width=True,
                height=500,
            )

            # Aggiorna stato con modifiche manuali (più efficiente del loop)
            st.session_state["prod_df_edit"].update(edited_df)
            filtered_df = prod_df_edit.loc[filtered_df.index].copy()  # copia sicura

            # ======================
            # Esporta dati (un solo pulsante)
            # ======================
            df_to_export = edited_df.copy()

            # ======================
            # Definizione colonne numeriche
            # ======================
            numeric_cols = [
                "A.N.", "HGT", "L.TOT.", "L.1", "L.2", "L.3", "Q.TA", "MQ", "ML"]
            for col in numeric_cols:
                if col in df_to_export.columns:
                    df_to_export[col] = pd.to_numeric(df_to_export[col], errors="coerce")
                    
            # Crea il buffer per Excel
            output = io.BytesIO()
            df_to_export.to_excel(output, index=False)  # mantiene numeri, date, formattazione
            output.seek(0)
            with col_p2:
                if st.button("⚙️ Aggiorna articoli (H/TR)"):
                    st.session_state["prod_df_edit"] = aggiorna_articoli(st.session_state["prod_df_edit"])
                    st.success("Articoli aggiornati correttamente (H/TR).")
                    st.rerun()  # 🔁 forza il refresh immediato del data editor

            with col_p3:
                # Pulsante di download
                st.download_button(
                    label="📤 Esporta Excel finale",
                    data=output,
                    file_name="Estrazione_DB_CAD_edit.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

    with cont_b:
        st.subheader("Elaborazione import AS400")
        cont_b1=st.container()
        cont_b2=st.container()
        with cont_b1:
            colb1a, colb1b,colb1c = st.columns([0.2,0.2,0.6],gap="small")
        with cont_b1:
            # Template iniziale (immutabile)
            if "import_as400_template" not in st.session_state:
                st.session_state["import_as400_template"] = carica_xlsx("data/Tracciato_import_as400.xlsx")

            # DF editabile dagli utenti
            if "import_as400" not in st.session_state:
                st.session_state["import_as400"] = st.session_state["import_as400_template"].copy()

            mapping_singolo = {
                "ARTICOLO":"XLSCDAR",
                "HND":"XLSOP02",
                "A.N.":"XLSALTZ",
                "HGT":"XLSALTZ",
                "L.TOT.":"XLSLRGH",
                "FINITURA":"XLSOP01",
                "POSIZIONE VETRO ":"XLSNOT4",
                "Q.TA":"XLSQTOR"
            }

            mapping_concat = {
                "XLSNOT2":["L1=:L.1","L2=:L.2","L3=:L.3"],
                "XLSNOT1":["EL :N.PROSPETTO","OFX :OFX","FLR :FLR","DRW :N.CARTIGLIO"]
            }
            
            mapping_fisso = {
                "XLSCBXB1": "012",
                "XLSCBXB2": "P25",
                "XLSVR01": "5FP",
                "XLSVR02": "5HN",
                "XLSVR03": "5LB"
            }
            column_config={
                    "XLSNRREV":None,
                    "XLSIDPN":None,
                    "XLSDSPNO":None,
                    "XLSIDST":None,
                    "XLSDSSTN":None,
                    "XLSIDCM":None,
                    "XLSCDCMP":None,
                    "XLSCCMP":None,
                    "XLSQCMP":None,
                    "XLSNRG0":None,
                    "XLSNRG1":None,
                    "LIBERO COMMERCIALE":None,
                    "LIBERO COMMERCIALE.1":None,
                    "LIBERO COMMERCIALE.2":None,
                    "XLSCBTST":None,
                    "XLSTXTST":None,
                    "XLSCVRS":None,
                    "XLSTDAR":None,
                    "XLSPSC1":None,
                    "XLSPSC2":None,
                    "XLSAGRZ":None,
                    "XLSRGA0":None,
                    "XLSDTPC":None,
                    "XLSTXDS1":None,
                }
            with colb1a:
                # 🔄 BOTTONE PER GENERARE AS400 DA PRODUZIONE
                if st.button("🔄 Aggiorna AS400 da Database Produzione"):
                    st.session_state["import_as400"] = trasferisci_dati(
                    df_origine=st.session_state["prod_df_edit"],
                    df_destinazione=st.session_state["import_as400_template"].copy(),
                    mapping_singolo=mapping_singolo,
                    mapping_concat=mapping_concat,
                    start_row=2,
                    sep_concat="/",  # esempio di separatore
                    mapping_fisso=mapping_fisso
                )
                    st.success("Dati import AS400 aggiornati.")
                    st.rerun()
        with cont_b2:
            # Editor modificabile
            edited_import_as400 = st.data_editor(
                st.session_state["import_as400"],
                use_container_width=True,
                column_config=column_config,
                num_rows="dynamic",
                key="editor_as400",
                height=600
            )
            st.session_state["import_as400"] = edited_import_as400

        with colb1b:
            # ======================
            # 📤 Pulsante Esportazione
            # ======================
            output_as400 = io.BytesIO()
            edited_import_as400.to_excel(output_as400, index=False)
            output_as400.seek(0)

            st.download_button(
                label="📤 Esporta AS400 elaborato",
                data=output_as400,
                file_name="AS400_elaborato.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    with cont_b1:
        st.write("Ricordarsi di editare variante 5LB, e controllare numeri conferme dopo aver esportato!")