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
| `as400_source_df` | DataFrame origine post `prepara_colonne_as400` + `raggruppa_articoli` (usato dalla verifica di coerenza AS400) |

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
- `tab_conferme(prod_df)` — entry point del tab
- Selectbox gerarchici (5 livelli: MACRO_SISTEMA → SISTEMA → C1 → C2 → ARTICOLO)
- Anteprima immagine componente
- Applica a riga singola o in blocco
- Editor dati con filtri GRUPPO/TIP.COM
- Bottone "🔄 Aggiorna AS400 da Database Produzione" (mapping + regole di business, vedi sotto) e verifica coerenza

### `modules/Funzione_conferme_moduli.py`
Logica business:
- Costruzione dizionari filtrati per selectbox gerarchici
- `prepara_colonne_as400(prod_df)` — calcola XLSNOT1/2, XLSALTZ, XLSLRGH e le varianti condizionali XLSVR01/02/03, XLSOP03 in base a pattern sul codice ARTICOLO
- `raggruppa_articoli(df)` — raggruppa e somma le righe per vetri `RJL*MQ` e profili `5GJL*` (chiave: FLR + ARTICOLO + ...)
- `carica_listino_prezzi(path)` / `calcola_prezzi_as400(df, start_row, listino_df)` — recupero prezzo unitario (`XLSPRZO`) da `data/Listino per conferme.xlsx`
- `importa_as400(...)` / `verifica_as400(...)` — trasferimento mapping 1:1 verso il template e verifica coerenza importazione AS400

### `modules/Rainbow_text.py`
- Utility per rendering testo con gradiente arcobaleno in Streamlit (uso estetico)

---

## Struttura dati

### Colonne del database di produzione (25 colonne)

```
FAMIGLIA, GRUPPO, ARTICOLO, DESCRIZIONE, TIP.COM, HND, A.N., HGT, L.TOT.,
L.1, L.2, L.3, N01, N02, N03, TIPO, FINITURA, POSIZIONE VETRO, N.PROSPETTO, OFX,
FLR, N.CARTIGLIO, Q.TA, MQ, ML
```

**Calcoli automatici:**
- `MQ = (HGT × L.TOT.) / 1_000_000` (solo vetri/pannelli)
- `ML = L.TOT. / 1000` (solo profili)
- Misure arrotondate al più vicino 0.5mm
- Valori 0 sostituiti con `"."` come placeholder

**Gruppi componenti riconosciuti:** VETRI, PANNELLI, HA, HB, TR, P, VP, HAP, HIP (e varianti)

### File dati master (`data/`)

**`Articoli.xlsx`** — dizionario gerarchico articoli:
- Colonne chiave: `MACRO_SISTEMA`, `SISTEMA`, `C1`, `C2`, `CONCAT_3`
- `NEUTRO_CONFERME` — codice neutro associato all'articolo
- `ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE` — descrizione
- `IMMAGINE_NOME_FILE` — path relativo immagine in `images/`

**`Tracciato_import_as400.xlsx`** — template vuoto con le colonne AS400 richieste (47 colonne).

**`Listino per conferme.xlsx`** — listino prezzi per il calcolo di `XLSPRZO`:
- `CONCAT_3` — codice articolo/chiave di match (univoco)
- `UNIT` — unità di misura (`ML`, `MQ`, `N.`)
- ultima colonna — prezzo unitario (`€_UNIT`, rinominato internamente `PREZZO_UNITARIO` per evitare problemi di encoding)

### Mapping AS400 (in `Funzione_conferme_layout.py`)

Mapping 1:1 (`mapping_singolo`), incluse le colonne calcolate in `prepara_colonne_as400`:
```python
{
    "ARTICOLO": "XLSCDAR",
    "HND": "XLSOP02",
    "XLSALTZ": "XLSALTZ",
    "XLSLRGH": "XLSLRGH",
    "FINITURA": "XLSOP01",
    "POSIZIONE VETRO ": "XLSNOT3",
    "N01": "XLSNOT4",
    "Q.TA": "XLSQTOR",
    "XLSNOT1": "XLSNOT1",
    "XLSNOT2": "XLSNOT2",
    "TIP.COM": "XLSTXDS1",
    "XLSVR01": "XLSVR01",
    "XLSVR02": "XLSVR02",
    "XLSVR03": "XLSVR03",
    "XLSOP03": "XLSOP03",
}
```

Valori fissi (`mapping_fisso`):
```python
{
    "XLSCBXB1": "012",
    "XLSCBXB2": "P25",
}
```

### Regole di business AS400 (dettagliate in `Regole conferme.txt`)

Applicate in sequenza dal bottone "🔄 Aggiorna AS400 da Database Produzione" (`Funzione_conferme_layout.py`), prima del mapping verso il template:

1. **Varianti condizionali** (`prepara_colonne_as400`) — in base a pattern sul codice `ARTICOLO` (`*` = jolly a carattere singolo, es. `5*0P` = `5`+1 char+`0P`):
   - `RJL*` → `XLSVR01 = "5FV"` (default altrimenti `"5FP"`)
   - `5*0P`, `5**V`, `5**HAP`, `5**VP` → `XLSVR02 = "5HN"`
   - `5*0P` → `XLSVR03 = "5FV"`; `5**HA`, `5**HB`, `5**TR` → `XLSVR03 = "5LB"` e `XLSOP03 = "L3100"`

2. **Raggruppamento e somma** (`raggruppa_articoli`) — le righe non incluse nei due gruppi restano invariate (1:1):
   - Vetri `RJL*MQ`: MQ per riga = `(XLSLRGH × XLSALTZ) / 1_000_000`, righe raggruppate per `FLR + ARTICOLO + XLSVR01 + FINITURA` sommando in `Q.TA`
   - Profili `5GJL*`: righe raggruppate per `FLR + ARTICOLO + XLSALTZ` sommando `Q.TA`
   - Le dimensioni non incluse nella chiave (`XLSALTZ`/`XLSLRGH`) vengono svuotate nella riga risultante

3. **Prezzo unitario** (`carica_listino_prezzi` + `calcola_prezzi_as400`), da `data/Listino per conferme.xlsx`:
   - Articoli `RJL*`: match esatto su `CONCAT_3` con chiave `"{XLSCDAR} {XLSOP01}"`
   - Altri articoli: match di prefisso più specifico (`XLSCDAR` inizia con `CONCAT_3`, si sceglie il `CONCAT_3` più lungo in caso di più match)
   - `UNIT == "ML"` → `XLSPRZO = prezzo_listino × max(XLSLRGH/1000, 0.5)`; altrimenti (`MQ`, `N.`) → `XLSPRZO = prezzo_listino`
   - Articoli senza corrispondenza: `XLSPRZO` resta vuoto, elenco mostrato in un `st.warning` in-app

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
5. Cliccare "🔄 Aggiorna AS400 da Database Produzione" → verificare varianti (XLSVR01/02/03, XLSOP03), raggruppamenti (righe `RJL*MQ` e `5GJL*` sommate per FLR+ARTICOLO+...) e prezzo (`XLSPRZO`) coerenti con `Regole conferme.txt`, ed eventuale avviso articoli senza prezzo
6. Esportare `AS400_elaborato.xlsx` → verificare colonne e valori fissi

---

## Dipendenze

```
streamlit
pandas
numpy
openpyxl
plotly
```
