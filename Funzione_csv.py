import pandas as pd
def carica_csv(file):
    df = pd.read_csv(file,error_bad_lines=False, encoding="utf-8", engine="python")

    # Rinomina colonne se presenti
    if "Nome" in df.columns:
        df.rename(columns={"Nome": "Name", "Conteggio": "Count"}, inplace=True)
    return df