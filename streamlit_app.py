import json
from pathlib import Path
import re
import streamlit as st
import pandas as pd
import glob
import matplotlib.pyplot as plt


# ------------------------
#  Your custom functions
# ------------------------
def remove_num_end(text):
    if text[-1].isdigit():
        text = text[:-1]
    return text.strip()


def replace_hour(hora):
    # Normaliza horas a en punto o y media
    horas_replace = {
        "09:15": "09:00",
        "09:45": "09:30",
        "10:15": "10:00",
        "10:45": "10:30",
        "11:15": "11:00",
        "11:45": "11:30",
        "12:15": "12:00",
        "12:45": "12:30",
        "13:00": "13:00",
        "20:45": "20:30",
    }
    if hora in horas_replace:
        return horas_replace.get(hora)
    return hora


league_to_name = {
    3089: "Superliga",
    3090: "Premier",
    3091: "LaLiga",
    3092: "Bundesliga",
    3093: "Serie A",
    3101: "Superliga",
    3102: "Premier",
    3103: "LaLiga",
    3104: "Bundesliga",
    3105: "Serie A",
    3106: "Primeira Liga",
}


def extract_dataframe_from_html(path: str) -> pd.DataFrame:
    """Extract dataframe from a single HTML file."""

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Look for 'cat=' pattern in the second line (or anywhere if needed)
    cat_match = re.search(r"cat=(\d+)", lines[1]) if len(lines) > 1 else None
    cat_value = int(cat_match.group(1)) if cat_match else None
    liga = league_to_name.get(cat_value, cat_value)

    dfs_list = pd.read_html(path)
    df = pd.concat(dfs_list, axis=0, ignore_index=True)
    df = df.dropna(subset=["CAMPO"])
    df = df[df["CAMPO"] != "APLAZADO"]

    df["campo_clean"] = df["CAMPO"].apply(lambda x: remove_num_end(x))
    df["campo_clean"] = df["campo_clean"].apply(
        lambda x: x.replace("MOLEDO", "SARDOMA")
    )
    df["HORA"] = df["HORA"].apply(lambda x: replace_hour(x))
    df["liga"] = liga
    return df


def get_all_teams(df: pd.DataFrame):
    """Return list of unique team names from dataframe."""
    teams = list(df["LOCAL"].unique()) + list(df["VISITANTE"].unique())
    teams = list(set(teams))
    return sorted(teams)


def compute_team_stats(df: pd.DataFrame, team: str):
    """Return dataframe filtered by team (placeholder)."""
    return df[df["team"] == team]


def plot_campos_one_team(df, team=None):
    df = df.loc[(df["LOCAL"] == team) | (df["VISITANTE"] == team)]
    campo_counts = df["campo_clean"].value_counts()
    # Plot the most repeated values as a bar chart
    fig, ax = plt.subplots(figsize=(8, 6))
    campo_counts.plot(kind="bar", color="skyblue", ax=ax)

    # Add labels and title
    titulo = "Número de partidos jugados en cada campo de {}".format(team)
    ax.set_title(titulo, fontsize=16)
    ax.set_xlabel("CAMPO", fontsize=12)
    ax.set_ylabel("Frecuencia", fontsize=12)
    plt.tight_layout()
    return fig


def plot_hours_one_league(df, team: str):
    df = df.loc[(df["LOCAL"] == team) | (df["VISITANTE"] == team)]
    df["HORA"] = pd.to_datetime(df["HORA"], format="%H:%M").dt.strftime("%H:%M")
    campo_counts = df["HORA"].value_counts().sort_index()

    # Plot the most repeated values as a bar chart
    fig, ax = plt.subplots(figsize=(8, 6))
    campo_counts.plot(kind="bar", color="skyblue", ax=ax)

    # Añadir etiquetas y título
    titulo = "Número de partidos jugados a cada hora de {}".format(team)
    ax.set_title(titulo, fontsize=16)
    ax.set_xlabel("Hora (redondeando a en punto, y media)", fontsize=9)
    ax.set_ylabel("Frecuencia", fontsize=12)
    plt.tight_layout()
    return fig


def plot_campos_all_leagues(df):
    order = [
        "Primeira Liga",
        "Serie A",
        "Bundesliga",
        "LaLiga",
        "Premier",
        "Superliga",
    ]  # your desired order

    list_dfs = [g for _, g in df.groupby("liga")]
    list_campos_leagues = [list(df["campo_clean"]) for df in list_dfs]
    list_leagues = [list(df["liga"]) for df in list_dfs]
    division_data = []
    for i, stadiums in enumerate(list_campos_leagues):
        for stadium in stadiums:
            division_data.append([stadium, list_leagues[i][0]])

    df = pd.DataFrame(division_data, columns=["CAMPO", "DIVISION"])

    # Count the number of occurrences of each "CAMPO" in each "DIVISION"
    campo_counts = df.groupby(["CAMPO", "DIVISION"]).size().unstack(fill_value=0)
    campo_counts = campo_counts[order]

    fig, ax = plt.subplots(figsize=(8, 6))
    # Plot the data as a grouped bar chart
    ax.legend(title="DIVISION", labels=[c for c in order if c in campo_counts.columns])
    campo_counts.plot(kind="bar", stacked=False, ax=ax)

    # Add labels and title
    ax.set_title("Partidos en cada campo por division", fontsize=16)
    ax.set_xlabel("Campos ", fontsize=12)
    ax.set_ylabel("Frecuencia total", fontsize=12)

    plt.tight_layout()
    return fig


def plot_hours_all_leagues(df):
    order = [
        "Primeira Liga",
        "Serie A",
        "Bundesliga",
        "LaLiga",
        "Premier",
        "Superliga",
    ]  # your desired order
    df["liga"] = pd.Categorical(df["liga"], categories=order, ordered=True)

    list_dfs = [g for _, g in df.groupby("liga")]
    list_hours_leagues = [list(df["HORA"]) for df in list_dfs]
    list_leagues = [list(df["liga"]) for df in list_dfs]
    division_data = []
    for i, hours in enumerate(list_hours_leagues):
        for hour in hours:
            division_data.append([hour, list_leagues[i][0]])

    df = pd.DataFrame(division_data, columns=["HORA", "DIVISION"])

    # Count the number of occurrences of each "CAMPO" in each "DIVISION"
    hora_counts = df.groupby(["HORA", "DIVISION"]).size().unstack(fill_value=0)
    hora_counts = hora_counts[order]
    fig, ax = plt.subplots(figsize=(8, 6))

    ax.legend(title="DIVISION", labels=[c for c in order if c in hora_counts.columns])
    hora_counts.plot(kind="bar", stacked=False, ax=ax)

    ax.set_title("Partidos en cada hora por division\n", fontsize=16)
    ax.set_xlabel("Horas (redondeando a en punto, y media)", fontsize=8)
    ax.set_ylabel("Frecuencia total", fontsize=12)

    plt.tight_layout()

    return fig


# ------------------------
#  Load data on startup
# ------------------------
@st.cache_data
def load_base_dataframe(year: int):
    files = glob.glob(f"data/{year}/*.html")
    dfs = [extract_dataframe_from_html(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    return df


st.title("Liga metropolitana ⚽")

# year selector
year = st.selectbox("Selecciona el año:", ["2025/26", "2024/25"], index=0)
if year == "2025/26":
    year = 2025
if year == "2024/25":
    year = 2024

base_df = load_base_dataframe(year)

# ------------------------
#  Persistence helpers
# ------------------------
CHAT_FILE = Path("data/chat/chat_messages.json")


def load_messages():
    if CHAT_FILE.exists():
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_messages(messages):
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


# ------------------------
#  UI
# ------------------------


# ------------------------
#  Sidebar setup
# ------------------------
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        right: 0;
        left: auto;
        border-left: 1px solid #ddd;
    }
    /* Chat scroll area */
    div[data-testid="stSidebarNav"] {display: none;}
    section[data-testid="stSidebar"] > div {
        display: flex;
        flex-direction: column;
        height: 100vh;
    }
    .chat-container {
        flex: 1;
        overflow-y: auto;
        padding-right: 0.5rem;
        margin-bottom: 4rem; /* space for input area */
    }
    .chat-input {
        position: fixed;
        bottom: 1rem;
        right: 1rem;
        width: 260px;
        background-color: white;
        padding: 0.5rem;
        border-top: 1px solid #ddd;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.sidebar.title("💬 Deja tu mensaje de ánimo a tu equipo")

# Load messages into session state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = load_messages()

# Display existing messages
st.sidebar.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in reversed(st.session_state.chat_messages):
    st.sidebar.markdown(f"• {msg}")
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Input form
with st.sidebar.form("chat_form", clear_on_submit=True):
    user_msg = st.text_input("Escribe un mensaje (máx 100):", max_chars=100)
    submitted = st.form_submit_button("Enviar")

    if submitted and user_msg.strip():
        st.session_state.chat_messages.append(user_msg.strip())
        save_messages(st.session_state.chat_messages)


st.markdown(
    "<p style = 'font-size: 13px; color: black; font-weight:bold'>"
    "Datos actualizados hasta el 14/10/2025:"
    "</p>"
    "<p style='font-size: 13px; color: gray;'>"
    "Selecciona un equipo o compara las ligas disponibles:"
    "</p>",
    unsafe_allow_html=True,
)

teams = get_all_teams(base_df)
selected_team = st.selectbox("Escoge tu equipo:", teams)

# put buttons side by side
col1, col2 = st.columns(2)
with col1:
    show_team_btn = st.button("Ver estadísticas del equipo")
with col2:
    show_league_compare_btn = st.button("Ver comparativa entre ligas")

# ------------------------
#  Action
# ------------------------
if show_league_compare_btn:
    fig = plot_campos_all_leagues(base_df)
    st.pyplot(fig)
    fig = plot_hours_all_leagues(base_df)
    st.pyplot(fig)

elif show_team_btn and selected_team:
    fig = plot_campos_one_team(base_df, selected_team)
    st.pyplot(fig)
    fig2 = plot_hours_one_league(base_df, selected_team)
    st.pyplot(fig2)
