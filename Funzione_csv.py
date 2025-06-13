import pandas as pd
def carica_csv(file):
    df = pd.read_csv(file)

    # Rinomina colonne se presenti
    if "Nome" in df.columns:
        df.rename(columns={"Nome": "Name", "Conteggio": "Count"}, inplace=True)
    return df