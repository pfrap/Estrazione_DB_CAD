# CLAUDE.md — Guida al progetto per Claude Code

## Panoramica

**Codifica pareti / Estrazione DB CAD** è un'app **Streamlit** per elaborare export CSV da AutoCAD di componenti edilizi (vetri, pannelli, profili) e generare file di importazione per il sistema ERP **AS400** di MOLTENI&C.

- Entry point: `App.py`
- Framework: Streamlit (layout wide, titolo "Codifica pareti")
- Ambiente: Conda env `dati` su Windows (Miniconda 3)
- Avvio: `Avvia_app.bat` oppure `streamlit run App.py`

---

## Architettura

```
App.py  (orchestratore)
  ├── Tab 1 "Riassunto progetto"   → caricamento file + grafici
  ├── Tab 2 "Comparazione DB"      → confronto grezzo vs. elaborato
  ├── Tab 3 "Verifiche macro"      → controllo ML, porte, OFX
  └── Tab 4 "Codifica articoli"    → dizionario, AS400
```

### Session state chiave

| Chiave | Contenuto |
|---|---|
| `nome_file_caricato` | Nome file attualmente caricato (rileva cambio file) |
| `prod_df_edit` | DataFrame con codifiche utente (persistente tra tab) |
| `import_as400` | DataFrame per export AS400 |
| `import_as400_template` | Template colonne AS400 vuoto |
| `editor_as400` | Stato editor AS400 |
| `filtro_gruppo` | Filtro attivo per GRUPPO |
| `filtro_tipcom` | Filtro attivo per TIP.COM |

Reset mirato tramite `reset_state_for_new_file()` al cambio file (non usare `st.session_state.clear()`).

---

## Moduli — ruolo di ciascun file

### `modules/Funzioni_caricamento_file.py`
- `carica_csv(file)` — legge CSV grezzo AutoCAD, restituisce DataFrame
- `carica_xlsx(file)` — legge XLSX già elaborato, restituisce DataFrame

### `modules/Funzione_elaborazione_csv.py`
Pipeline di normalizzazione dati:
- `funzione_dati(df)` — per CSV grezzo: normalizza → calcola → garantisce colonne → finalizza
- `funzione_dati_xlsx(df)` — per XLSX già elaborato (pipeline semplificata)
- `_normalizza_colonne(df)` — filtra VETRI/PANNELLI/Profili, mappa nomi colonna varianti
- `_calcola_misure(df)` — arrotonda a 0.5mm, calcola MQ e ML
- `_garantisci_colonne(df)` — assicura che tutte le 25 colonne attese esistano
- `_finalizza(df)` — ordina per GRUPPO/TIP.COM/A.N./HGT/L.TOT./L.1, sostituisce 0 con "."

### `modules/Grafico_recap.py`
Grafici per Tab 1:
- Treemap e sunburst: composizione gerarchica progetto
- Grafici a barre: quantità per piano (FLR) e gruppo (GRUPPO)

### `modules/Grafico_verifiche.py`
Grafici per Tab 3:
- `grafico_ofx_multipli(prod_df)` — verifica ML per ufficio/piano
- Controlli A.N. (numero asse porte) e HND (maniglie)

### `modules/Funzione_conferme_layout.py`
UI completa Tab 4 "Codifica articoli":
- `tab_conferme(prod_df, articoli_df, as400_template)` — entry point del tab
- Selectbox gerarchici (5 livelli: MACRO_SISTEMA → SISTEMA → C1 → C2 → ARTICOLO)
- Anteprima immagine componente
- Applica a riga singola o in blocco
- Editor dati con filtri GRUPPO/TIP.COM
- Generazione e verifica AS400

### `modules/Funzione_conferme_moduli.py`
Logica business:
- Costruzione dizionari filtrati per selectbox gerarchici
- `prepara_colonne_as400(prod_df, template)` — mapping campi verso AS400
- Funzioni di verifica accuratezza importazione AS400

### `modules/Rainbow_text.py`
- Utility per rendering testo con gradiente arcobaleno in Streamlit (uso estetico)

---

## Struttura dati

### Colonne del database di produzione (25 colonne)

```
FAMIGLIA, GRUPPO, ARTICOLO, DESCRIZIONE, TIP.COM, HND, A.N., HGT, L.TOT.,
L.1, L.2, L.3, N01, N02, N03, TIPO, FINITURA, POSIZIONE VETRO, N.PROS, OFX,
FLR, N.CART, Q.TA, MQ, ML
```

**Calcoli automatici:**
- `MQ = (HGT × L.TOT.) / 1_000_000` (solo vetri/pannelli)
- `ML = L.TOT. / 1000` (solo profili)
- Misure arrotondate al più vicino 0.5mm
- Valori 0 sostituiti con `"."` come placeholder

**Gruppi componenti riconosciuti:** VETRI, PANNELLI, HA, HB, TR, P, VP, HAP (e varianti)

### File dati master (`data/`)

**`Articoli.xlsx`** — dizionario gerarchico articoli:
- Colonne chiave: `MACRO_SISTEMA`, `SISTEMA`, `C1`, `C2`, `CONCAT_3`
- `NEUTRO_CONFERME` — codice neutro associato all'articolo
- `ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE` — descrizione
- `IMMAGINE_NOME_FILE` — path relativo immagine in `images/`

**`Tracciato_import_as400.xlsx`** — template vuoto con le colonne AS400 richieste.

### Mapping AS400 (in `Funzione_conferme_moduli.py`)

Mapping 1:1 senza concatenazioni:
```python
{
    "ARTICOLO": "XLSCDAR",
    "HND": "XLSOP02",
    "XLSALTZ": "XLSALTZ",
    "XLSLRGH": "XLSLRGH",
    "FINITURA": "XLSOP01",
    "POSIZIONE VETRO": "XLSNOT3",
    "Q.TA": "XLSQTOR",
    "XLSNOT1": "XLSNOT1",
    "XLSNOT2": "XLSNOT2",
}
```

Valori fissi:
```python
{
    "XLSCBXB1": "012",
    "XLSCBXB2": "P25",
    "XLSVR01": "5FP",
    "XLSVR02": "5HN",
    "XLSVR03": "5LB",
}
```

---

## Pattern e convenzioni

### Streamlit
- Usare **session state** per persistere dati tra rerun (non variabili locali)
- Non usare `st.session_state.clear()` — usare reset mirato (vedi `reset_state_for_new_file`)
- Chiavi grafici generate dinamicamente per evitare problemi di re-render
- Layout sempre `wide`

### Pandas
- Il DataFrame principale è `prod_df` (immutabile dopo elaborazione)
- Le modifiche utente vanno su `prod_df_edit` (copia in session state)
- I valori mancanti/zero sono rappresentati come stringa `"."`
- Ordinamento standard: `GRUPPO, TIP.COM, A.N., HGT, L.TOT., L.1`

### Codice
- Funzioni private con prefisso `_` nei moduli di elaborazione
- Nomi variabili e commenti in **italiano**
- Nomi colonne DataFrame in **MAIUSCOLO** (es. `GRUPPO`, `ARTICOLO`)
- Gestione errori con `try/except` e valori di fallback sicuri

---

## File di output

| File | Quando | Contenuto |
|---|---|---|
| `Estrazione_DB_CAD.xlsx` | Dopo upload CSV | DB normalizzato (senza codifiche utente) |
| `Estrazione_DB_CAD_edit.xlsx` | Da Tab 4 | DB con codifiche articoli compilate dall'utente |
| `AS400_elaborato.xlsx` | Da Tab 4 | File pronto per importazione in AS400 |

---

## Come testare

1. Avviare con `Avvia_app.bat` (o `streamlit run App.py` con env `dati` attivo)
2. Caricare un CSV AutoCAD in Tab 1 → verificare che `prod_df` contenga le 25 colonne
3. Navigare in Tab 3 → verificare grafici ML e porte
4. In Tab 4 → selezionare un articolo dal dizionario, verificare anteprima immagine
5. Esportare `AS400_elaborato.xlsx` → verificare colonne e valori fissi

---

## Dipendenze

```
streamlit
pandas
numpy
openpyxl
plotly
```
