import streamlit as st


def add_starfield_background() -> None:
    """Add a subtle animated starfield backdrop to the Streamlit app."""
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at top left, #1c2a4d 0%, #09111e 45%, #03050d 100%);
            position: relative;
            overflow: hidden;
        }
        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 0;
            background-image:
                radial-gradient(2px 2px at 20px 30px, rgba(255,255,255,0.9), transparent),
                radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.7), transparent),
                radial-gradient(1px 1px at 90px 40px, rgba(255,255,255,0.8), transparent),
                radial-gradient(1px 1px at 130px 80px, rgba(255,255,255,0.6), transparent),
                radial-gradient(2px 2px at 160px 30px, rgba(255,255,255,0.8), transparent);
            background-repeat: repeat;
            background-size: 200px 200px;
            opacity: 0.55;
            animation: drift 35s linear infinite;
        }
        .stApp > * {
            position: relative;
            z-index: 1;
        }
        @keyframes drift {
            from { transform: translateY(0); }
            to { transform: translateY(-200px); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
