# Selezione multipla OFX
    ofx_disponibili = sorted(df['OFX'].dropna().unique())
    selezione_ofx = st.multiselect("Seleziona OFX", ofx_disponibili, default=ofx_disponibili[:])


# Selezione multipla FLR
    flr_disponibili = sorted(df['FLR'].dropna().unique())
    selezione_flr = st.multiselect("Seleziona FLR", flr_disponibili, default=flr_disponibili)

    if not selezione_flr:
        st.info("👈 Seleziona almeno un FLR per continuare.")
        return

    df = df[df['FLR'].isin(selezione_flr)]