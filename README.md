# Codifica pareti — Estrazione DB CAD

Applicazione web per elaborare export CSV da **AutoCAD** contenenti componenti edilizi (vetri, pannelli, profili), normalizzare i dati in un database di produzione e generare file di importazione per il sistema ERP **AS400**.

Sviluppata per uso interno MOLTENI&C.

---

## Funzionalità principali

| Scheda | Descrizione |
|---|---|
| **Riassunto progetto** | Caricamento file, grafici treemap/sunburst, riepilogo componenti per piano e famiglia |
| **Comparazione DB** | Confronto affiancato tra dati grezzi e database elaborato |
| **Verifiche macro** | Controllo metri lineari (ML), numero assi porte (A.N.), maniglie (HND), uffici (OFX) |
| **Codifica articoli** | Associazione articoli dal dizionario gerarchico, anteprima immagini, export AS400 |

---

## Prerequisiti

- **Miniconda 3** installato in `C:\Users\<utente>\AppData\Local\miniconda3`
- Ambiente Conda `dati` configurato
- Dipendenze Python (vedi [requirements.txt](requirements.txt)):
  - `streamlit`
  - `pandas`
  - `numpy`
  - `openpyxl`
  - `plotly`

### Creare l'ambiente Conda (prima installazione)

```bash
conda create -n dati python=3.11
conda activate dati
pip install -r requirements.txt
```

---

## Avvio

### Metodo rapido (Windows)
Doppio click su **`Avvia_app.bat`** — attiva automaticamente l'ambiente `dati` e lancia Streamlit.

### Metodo manuale
```bash
conda activate dati
streamlit run App.py
```

L'app è disponibile su `http://localhost:8501`.

---

## Workflow d'uso

```
1. Carica file
   ├── CSV grezzo da AutoCAD  →  elaborazione automatica
   └── XLSX già elaborato     →  caricamento diretto

2. Riassunto progetto
   └── Verifica composizione componenti (treemap, grafici per piano/famiglia)

3. Comparazione DB
   └── Confronta dati originali vs. database normalizzato

4. Verifiche macro
   └── Controlla ML, porte (A.N., HND), uffici (OFX)

5. Codifica articoli
   ├── Seleziona articoli dal dizionario gerarchico
   ├── Anteprima immagine componente
   ├── Applica in blocco a più righe
   └── Esporta AS400

6. Download file output
   ├── Estrazione_DB_CAD.xlsx       (DB elaborato)
   ├── Estrazione_DB_CAD_edit.xlsx  (DB con codifiche utente)
   └── AS400_elaborato.xlsx         (file pronto per importazione ERP)
```

---

## Struttura del progetto

```
Estrazione_DB_CAD/
├── App.py                              # Entry point — orchestratore UI e sessione
├── Avvia_app.bat                       # Launcher Windows
├── requirements.txt                    # Dipendenze Python
├── data/
│   ├── Articoli.xlsx                  # Dizionario gerarchico articoli (dati master)
│   └── Tracciato_import_as400.xlsx    # Template colonne AS400
├── images/                            # Anteprime componenti (540+ PNG)
└── modules/
    ├── Funzioni_caricamento_file.py   # Caricamento CSV/XLSX
    ├── Funzione_elaborazione_csv.py   # Normalizzazione e calcolo misure
    ├── Funzione_conferme_layout.py    # UI scheda "Codifica articoli"
    ├── Funzione_conferme_moduli.py    # Logica dizionario e mapping AS400
    ├── Grafico_recap.py               # Grafici riepilogo (treemap, barre)
    ├── Grafico_verifiche.py           # Grafici verifiche macro
    └── Rainbow_text.py                # Utility testo colorato
```

---

## Formato dati in input

### CSV da AutoCAD
File grezzo esportato direttamente da AutoCAD. L'app normalizza automaticamente i nomi colonna e filtra i gruppi componenti pertinenti.

### XLSX già elaborato
File Excel precedentemente processato dall'app stessa (formato `Estrazione_DB_CAD.xlsx`).

### Colonne principali del database elaborato

| Colonna | Significato |
|---|---|
| `FAMIGLIA` | Famiglia prodotto |
| `GRUPPO` | Gruppo componente (VETRI, PANNELLI, HA, HB, TR, P, VP, HAP…) |
| `ARTICOLO` | Codice articolo neutro |
| `TIP.COM` | Tipo componente |
| `HND` | Tipo maniglia porte |
| `A.N.` | Numero asse porta |
| `HGT` | Altezza (mm) |
| `L.TOT.` | Lunghezza totale (mm) |
| `MQ` | Metri quadri (calcolati per vetri: HGT × L.TOT. / 1.000.000) |
| `ML` | Metri lineari (calcolati per profili: L.TOT. / 1000) |
| `OFX` | Codice ufficio/piano |
| `FLR` | Piano |
| `Q.TA` | Quantità |

---

## Dizionario articoli (Articoli.xlsx)

Struttura gerarchica a 5 livelli per la codifica:

```
MACRO_SISTEMA
  └── SISTEMA
        └── C1
              └── C2
                    └── CONCAT_3  (codice articolo completo)
```

Ogni voce include:
- `NEUTRO_CONFERME` — codice neutro di conferma
- `ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE` — descrizione componente
- `IMMAGINE_NOME_FILE` — path dell'anteprima in `images/`

---

## Mapping AS400

La scheda "Codifica articoli" genera un file di importazione AS400 con mapping diretto (1:1) dai campi del database:

| Campo DB | Campo AS400 |
|---|---|
| `ARTICOLO` | `XLSCDAR` |
| `HND` | `XLSOP02` |
| `FINITURA` | `XLSOP01` |
| `POSIZIONE VETRO` | `XLSNOT3` |
| `Q.TA` | `XLSQTOR` |

Valori fissi aggiunti automaticamente: `XLSCBXB1=012`, `XLSCBXB2=P25`, `XLSVR01=5FP`, `XLSVR02=5HN`, `XLSVR03=5LB`.
