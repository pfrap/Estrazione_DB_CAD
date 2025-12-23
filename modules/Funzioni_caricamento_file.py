import pandas as pd

def carica_csv(file) -> pd.DataFrame:
    """Carica un CSV in DataFrame e normalizza i nomi colonna più comuni."""
    df = pd.read_csv(file)

    # Normalizzazione nomi colonna (alcuni export usano italiano)
    rename_map = {}
    if "Nome" in df.columns:
        rename_map["Nome"] = "Name"
    if "Conteggio" in df.columns:
        rename_map["Conteggio"] = "Count"
    if rename_map:
        df = df.rename(columns=rename_map)

    return df


def carica_xlsx(file) -> pd.DataFrame:
    """Carica un Excel in DataFrame."""
    return pd.read_excel(file)
