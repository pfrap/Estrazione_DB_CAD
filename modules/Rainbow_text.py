import streamlit as st

def rainbow_text(text, tag="h3"):
    """
    Visualizza testo con effetto arcobaleno in Streamlit.

    Parametri:
    - text (str): il testo da visualizzare
    - tag (str): il tag HTML da usare (es. "h1", "h3", "p")
    """
    st.markdown(
        f"""
        <{tag}>
            <span style="
                background: linear-gradient(to right, red, orange, yellow, green, blue, indigo, violet);
                -webkit-background-clip: text;
                color: transparent;
                font-weight: bold;
            ">
                {text}
            </span>
        </{tag}>
        """,
        unsafe_allow_html=True
    )
