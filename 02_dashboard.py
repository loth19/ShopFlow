# Etape 1) Imports
from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st
from typing import cast
import requests
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter
import numpy as np


# Etape 2) Configuration de la page Streamlit
st.set_page_config(
    page_title="ShopFlow Dashboard",
    page_icon="📊",
    layout="wide",
)


# Etape 3) Le style sera injecte apres le choix du theme
# Etape 4) Trouver le bon fichier SQLite
BASE_DIR = Path(__file__).resolve().parent
DB_CANDIDATES = [
    BASE_DIR / "data" / "shopflow.db",
    BASE_DIR / "data" / "ShopFlow.db",
]


def get_db_path() -> Path:
    for db_path in DB_CANDIDATES:
        if db_path.exists():
            return db_path
    raise FileNotFoundError("Base SQLite introuvable: data/shopflow.db ou data/ShopFlow.db")


# Etape 5) Charger les donnees (mise en cache pour performance)
@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, float]:
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)

    try:
        commandes = pd.read_sql_query("SELECT * FROM commandes", connection)
        produits = pd.read_sql_query("SELECT * FROM produit", connection)
        clients = pd.read_sql_query("SELECT * FROM client", connection)

        # Devise par defaut (si table exchange_rates absente)
        eur_to_usd = 1.08

        # Si la table existe, on prend le dernier taux EUR -> USD
        try:
            taux_df = pd.read_sql_query(
                """
                SELECT rate
                FROM exchange_rates
                WHERE base = 'EUR' AND target = 'USD'
                ORDER BY rate_date DESC
                LIMIT 1
                """,
                connection,
            )
            if not taux_df.empty:
                eur_to_usd = float(taux_df.loc[0, "rate"])
        except Exception:
            pass

        return commandes, produits, clients, eur_to_usd
    finally:
        connection.close()


# Etape 6) Fonctions simples de preparation

def prepare_base_table(commandes: pd.DataFrame, produits: pd.DataFrame, clients: pd.DataFrame) -> pd.DataFrame:
    # On garde seulement les commandes completees pour les KPI revenue
    base: pd.DataFrame = commandes.loc[commandes["status"] == "completed"].copy()

    # Harmoniser les dates et mois
    base["date_commande"] = pd.to_datetime(base["date_commande"], errors="coerce")
    base["mois"] = pd.to_datetime(base["date_commande"], errors="coerce").dt.to_period("M").astype(str)

    # Jointure avec produits
    produits_min = cast(pd.DataFrame, produits[["id", "name", "category"]].copy())
    produits_min = produits_min.rename({"id": "produit_ref_id", "name": "product_name", "category": "categorie"}, axis=1)
    base = base.merge(produits_min, left_on="produit_id", right_on="produit_ref_id", how="left")

    # Jointure avec clients
    clients_min = cast(pd.DataFrame, clients[["id", "name"]].copy())
    clients_min = clients_min.rename({"id": "client_ref_id", "name": "client_name"}, axis=1)
    base = base.merge(clients_min, left_on="client_id", right_on="client_ref_id", how="left")

    return base


def format_currency(value: float, devise: str) -> str:
    symbole = "EUR" if devise == "EUR" else "USD"
    return f"{value:,.2f} {symbole}".replace(",", " ")


def inject_theme_css(theme: str) -> None:
    """Injecte un style complet et exclusif pour le theme choisi."""
    if theme == "Sombre":
        st.markdown(
            """
            <style>
            .stApp {
                background:
                    radial-gradient(1000px 320px at 10% -5%, rgba(37, 99, 235, 0.30), transparent 60%),
                    radial-gradient(1000px 320px at 90% -10%, rgba(20, 184, 166, 0.18), transparent 60%),
                    #0b1220;
                color: #e5e7eb;
            }
            header[data-testid="stHeader"] { background: rgba(11, 18, 32, 0.72); backdrop-filter: blur(6px); }
            .block-container { max-width: 1200px; padding-top: 3.2rem; padding-bottom: 1.2rem; }
            .hero-wrap { margin-top: 0.75rem; margin-bottom: 1.2rem; padding: 1.05rem 1.25rem; border-radius: 18px; background: linear-gradient(135deg, #1d4ed8 0%, #0ea5e9 55%, #06b6d4 100%); box-shadow: 0 10px 30px rgba(0,0,0,0.35); color: #ffffff; }
            .hero-kicker { display: inline-block; font-size: 0.76rem; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 700; background: rgba(255, 255, 255, 0.18); border: 1px solid rgba(255, 255, 255, 0.35); border-radius: 999px; padding: 0.2rem 0.65rem; margin-bottom: 0.55rem; }
            .main-title { font-size: 2.15rem; font-weight: 700; line-height: 1.18; margin-bottom: 0.2rem; }
            .subtitle { color: rgba(255, 255, 255, 0.95); margin-bottom: 0.1rem; font-size: 1rem; }
            [data-testid="stSidebar"] { background: #111827; border-right: 1px solid #1f2937; }
            [data-testid="stMetric"] { background: #0f172a; border: 1px solid #1f2937; border-radius: 14px; padding: 0.65rem 0.8rem; box-shadow: 0 4px 16px rgba(0,0,0,0.25); }
            [data-testid="stDataFrame"] { background: #0f172a; border: 1px solid #1f2937; border-radius: 12px; padding: 0.35rem; }
            @media (max-width: 900px) { .block-container { padding-top: 2.5rem; } .main-title { font-size: 1.65rem; } .subtitle { font-size: 0.92rem; } }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            .stApp {
                background:
                    radial-gradient(1200px 320px at 8% -5%, rgba(14, 165, 233, 0.20), transparent 60%),
                    radial-gradient(1200px 320px at 92% -10%, rgba(20, 184, 166, 0.16), transparent 60%),
                    #f6f8fc;
                color: #0f172a;
            }
            header[data-testid="stHeader"] { background: rgba(246, 248, 252, 0.72); backdrop-filter: blur(6px); }
            .block-container { max-width: 1200px; padding-top: 3.2rem; padding-bottom: 1.2rem; }
            .hero-wrap { margin-top: 0.75rem; margin-bottom: 1.2rem; padding: 1.05rem 1.25rem; border-radius: 18px; background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 55%, #14b8a6 100%); box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); color: #ffffff; }
            .hero-kicker { display: inline-block; font-size: 0.76rem; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 700; background: rgba(255, 255, 255, 0.18); border: 1px solid rgba(255, 255, 255, 0.35); border-radius: 999px; padding: 0.2rem 0.65rem; margin-bottom: 0.55rem; }
            .main-title { font-size: 2.15rem; font-weight: 700; line-height: 1.18; margin-bottom: 0.2rem; }
            .subtitle { color: rgba(255, 255, 255, 0.95); margin-bottom: 0.1rem; font-size: 1rem; }
            [data-testid="stSidebar"] { background: linear-gradient(180deg, #f8fbff 0%, #f1f5f9 100%); border-right: 1px solid #e2e8f0; }
            [data-testid="stMetric"] { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 0.65rem 0.8rem; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04); }
            [data-testid="stDataFrame"] { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 0.35rem; }
            @media (max-width: 900px) { .block-container { padding-top: 2.5rem; } .main-title { font-size: 1.65rem; } .subtitle { font-size: 0.92rem; } }
            </style>
            """,
            unsafe_allow_html=True,
        )


def fetch_api_json(base_url: str, endpoint: str) -> dict | list:
    url = f"{base_url.rstrip('/')}{endpoint}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def parse_revenue_payload(revenue_payload: dict) -> tuple[float, pd.DataFrame, pd.DataFrame, float | None]:
    """Normalise la reponse API pour supporter ancien et nouveau formats."""
    total_stats = cast(dict, revenue_payload.get("total_stats", {}))

    revenue_total = float(
        revenue_payload.get("revenue_total", total_stats.get("revenue_total", 0.0)) or 0.0
    )
    panier_moyen_api = revenue_payload.get("panier_moyen", total_stats.get("panier_moyen"))
    panier_moyen = float(panier_moyen_api) if panier_moyen_api is not None else None

    revenue_month = pd.DataFrame(revenue_payload.get("revenue_par_mois", []))
    revenue_cat = pd.DataFrame(revenue_payload.get("revenue_par_categorie", []))

    if not revenue_month.empty:
        revenue_month = revenue_month.rename(
            columns={"revenue_eur": "total_affiche", "revenue": "total_affiche", "total_eur": "total_affiche"}
        )
        if "mois" not in revenue_month.columns and "month" in revenue_month.columns:
            revenue_month = revenue_month.rename(columns={"month": "mois"})
        if "total_affiche" in revenue_month.columns:
            revenue_month["total_affiche"] = pd.to_numeric(revenue_month["total_affiche"], errors="coerce")
        revenue_month = revenue_month.dropna(subset=["total_affiche"]).sort_values(by="mois")

    if not revenue_cat.empty:
        revenue_cat = revenue_cat.rename(
            columns={"category": "categorie", "revenue_eur": "total_affiche", "revenue": "total_affiche", "total_eur": "total_affiche"}
        )
        if "total_affiche" in revenue_cat.columns:
            revenue_cat["total_affiche"] = pd.to_numeric(revenue_cat["total_affiche"], errors="coerce")
        revenue_cat = revenue_cat.dropna(subset=["total_affiche"]).sort_values(by="total_affiche", ascending=False)

    return revenue_total, revenue_month, revenue_cat, panier_moyen


st.markdown('<div style="height:0.35rem"></div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="hero-wrap">
        <div class="hero-kicker">Retail Analytics</div>
        <div class="main-title">📊 ShopFlow Dashboard</div>
        <div class="subtitle">Suivi des KPI business en temps reel: revenue, tendance mensuelle et meilleurs clients.</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<div style="color:#334155; font-size:0.98rem; margin:0.1rem 0 0.8rem 0;">Version interactive avec source SQLite et option bonus API FastAPI.</div>',
    unsafe_allow_html=True,
)


# Etape 9) Filtres utilisateur
with st.sidebar:
    st.header("Filtres")

    selected_theme = st.selectbox("Affichage", options=["Clair", "Sombre"], index=0)

    selected_source = st.radio("Source des donnees", options=["SQLite", "API"], index=0)
    api_base_url = st.text_input("URL API (bonus)", value="http://127.0.0.1:8000")
    top_limit = st.slider("Top N", min_value=5, max_value=20, value=10, step=1)

    selected_devise = st.selectbox("Devise", options=["EUR", "USD"], index=0)

inject_theme_css(selected_theme)

show_details_table = False
final_table = pd.DataFrame()

if selected_theme == "Sombre":
    plt.style.use("dark_background")
    chart_face = "#0f172a"
    grid_color = "#334155"
    text_color = "#e5e7eb"
    month_line = "#60a5fa"
    cat_colors = ["#14b8a6", "#0ea5e9", "#2563eb", "#8b5cf6", "#f59e0b", "#ef4444"]
    top_color = "#60a5fa"
else:
    plt.style.use("seaborn-v0_8-whitegrid")
    chart_face = "#ffffff"
    grid_color = "#e2e8f0"
    text_color = "#0f172a"
    month_line = "#2563eb"
    cat_colors = ["#14b8a6", "#0ea5e9", "#2563eb", "#8b5cf6", "#f59e0b", "#ef4444"]
    top_color = "#2563eb"


# Etape 10) Branche 1: mode SQLite (principal)
if selected_source == "SQLite":
    try:
        commandes_df, produits_df, clients_df, eur_to_usd_rate = load_data()
    except Exception as exc:
        st.error(f"Impossible de charger la base de donnees: {exc}")
        st.stop()

    base_df: pd.DataFrame = prepare_base_table(commandes_df, produits_df, clients_df)

    categories = sorted([c for c in base_df["categorie"].dropna().unique().tolist()])
    with st.sidebar:
        selected_categories = st.multiselect("Categorie", options=categories, default=categories)

    mois_list = sorted([m for m in base_df["mois"].dropna().unique().tolist()])
    with st.sidebar:
        selected_month = st.selectbox("Mois", options=["Tous"] + mois_list, index=0)

    filtered_df: pd.DataFrame = base_df.copy()

    if selected_categories:
        filtered_df = filtered_df.loc[filtered_df["categorie"].isin(selected_categories)].copy()

    if selected_month != "Tous":
        filtered_df = filtered_df.loc[filtered_df["mois"] == selected_month].copy()

    if filtered_df.empty:
        st.warning("Aucune donnee disponible avec ces filtres.")
        st.stop()

    if selected_devise == "USD":
        filtered_df["total_affiche"] = filtered_df["total_eur"] * eur_to_usd_rate
    else:
        filtered_df["total_affiche"] = filtered_df["total_eur"]

    filtered_df = cast(pd.DataFrame, filtered_df)

    total_affiche_series = cast(pd.Series, filtered_df["total_affiche"])
    id_series = cast(pd.Series, filtered_df["id"])
    client_id_series = cast(pd.Series, filtered_df["client_id"])

    revenue_total = float(total_affiche_series.sum())
    nb_commandes = int(id_series.nunique())
    panier_moyen = revenue_total / nb_commandes if nb_commandes > 0 else 0.0
    clients_actifs = int(client_id_series.nunique())

    revenue_month = cast(pd.DataFrame, filtered_df.groupby("mois", as_index=False)["total_affiche"].sum())
    revenue_month = revenue_month.sort_values(by="mois")

    revenue_cat = cast(pd.DataFrame, filtered_df.groupby("categorie", as_index=False)["total_affiche"].sum())
    revenue_cat = revenue_cat.sort_values(by="total_affiche", ascending=False)

    top_customers = cast(pd.DataFrame, filtered_df.groupby("client_name", as_index=False)["total_affiche"].sum())
    top_customers = top_customers.sort_values(by="total_affiche", ascending=False).head(top_limit)

    col1, col2, col3 = st.columns(3)
    col1.metric("Revenue total", format_currency(revenue_total, selected_devise))
    col2.metric("Panier moyen", format_currency(panier_moyen, selected_devise))
    col3.metric("Clients actifs", f"{clients_actifs}")

    columns_to_show = [
        "id",
        "date_commande",
        "mois",
        "client_id",
        "client_name",
        "produit_id",
        "product_name",
        "categorie",
        "total_affiche",
    ]
    final_table = cast(pd.DataFrame, filtered_df[columns_to_show])
    show_details_table = True

# Etape 11) Branche 2: mode API (bonus)
else:
    eur_to_usd_rate = 1.08

    try:
        revenue_payload = cast(dict, fetch_api_json(api_base_url, "/stats/revenue"))
        top_customers_payload = cast(list, fetch_api_json(api_base_url, f"/stats/top-customers?limit={top_limit}"))
    except Exception as exc:
        st.warning(f"API indisponible ({exc}). Bascule automatique sur SQLite.")
        selected_source = "SQLite"
        commandes_df, produits_df, clients_df, eur_to_usd_rate = load_data()
        base_df = prepare_base_table(commandes_df, produits_df, clients_df)
        filtered_df = base_df.copy()
        if selected_devise == "USD":
            filtered_df["total_affiche"] = filtered_df["total_eur"] * eur_to_usd_rate
        else:
            filtered_df["total_affiche"] = filtered_df["total_eur"]
        revenue_total = float(cast(pd.Series, filtered_df["total_affiche"]).sum())
        nb_commandes = int(cast(pd.Series, filtered_df["id"]).nunique())
        panier_moyen = revenue_total / nb_commandes if nb_commandes > 0 else 0.0
        clients_actifs = int(cast(pd.Series, filtered_df["client_id"]).nunique())
        revenue_month = cast(pd.DataFrame, filtered_df.groupby("mois", as_index=False)["total_affiche"].sum()).sort_values(by="mois")
        revenue_cat = cast(pd.DataFrame, filtered_df.groupby("categorie", as_index=False)["total_affiche"].sum()).sort_values(by="total_affiche", ascending=False)
        top_customers = cast(pd.DataFrame, filtered_df.groupby("client_name", as_index=False)["total_affiche"].sum()).sort_values(by="total_affiche", ascending=False).head(top_limit)
        col1, col2, col3 = st.columns(3)
        col1.metric("Revenue total", format_currency(revenue_total, selected_devise))
        col2.metric("Panier moyen", format_currency(panier_moyen, selected_devise))
        col3.metric("Clients actifs", f"{clients_actifs}")
        show_details_table = False
    else:
        revenue_total, revenue_month, revenue_cat, panier_moyen_api = parse_revenue_payload(revenue_payload)
        top_customers = pd.DataFrame(top_customers_payload)

        if not top_customers.empty:
            top_customers = top_customers.rename(columns={"client_name": "client_name", "depense_totale_eur": "total_affiche"}).sort_values(by="total_affiche", ascending=False)

        if "categorie" not in revenue_cat.columns and "category" in revenue_cat.columns:
            revenue_cat = revenue_cat.rename(columns={"category": "categorie"})
        if "client_name" not in top_customers.columns and "client_id" in top_customers.columns:
            top_customers["client_name"] = top_customers["client_id"].astype(str)

        if selected_devise == "USD":
            revenue_total = revenue_total * eur_to_usd_rate
            if not revenue_month.empty:
                revenue_month["total_affiche"] = revenue_month["total_affiche"] * eur_to_usd_rate
            if not revenue_cat.empty:
                revenue_cat["total_affiche"] = revenue_cat["total_affiche"] * eur_to_usd_rate
            if not top_customers.empty:
                top_customers["total_affiche"] = top_customers["total_affiche"] * eur_to_usd_rate

        panier_moyen = panier_moyen_api if panier_moyen_api is not None else 0.0
        if panier_moyen_api is None and not top_customers.empty:
            top_series = cast(pd.Series, top_customers["total_affiche"])
            panier_moyen = float(top_series.mean())
        clients_actifs = len(top_customers)

        # Si l'API ne renvoie pas les series attendues, fallback automatique sur SQLite
        if revenue_month.empty or revenue_cat.empty:
            st.warning("Donnees API incompletes. Bascule automatique sur SQLite.")
            commandes_df, produits_df, clients_df, eur_to_usd_rate = load_data()
            base_df = prepare_base_table(commandes_df, produits_df, clients_df)
            filtered_df = base_df.copy()
            if selected_devise == "USD":
                filtered_df["total_affiche"] = filtered_df["total_eur"] * eur_to_usd_rate
            else:
                filtered_df["total_affiche"] = filtered_df["total_eur"]

            revenue_total = float(cast(pd.Series, filtered_df["total_affiche"]).sum())
            nb_commandes = int(cast(pd.Series, filtered_df["id"]).nunique())
            panier_moyen = revenue_total / nb_commandes if nb_commandes > 0 else 0.0
            clients_actifs = int(cast(pd.Series, filtered_df["client_id"]).nunique())
            revenue_month = cast(pd.DataFrame, filtered_df.groupby("mois", as_index=False)["total_affiche"].sum()).sort_values(by="mois")
            revenue_cat = cast(pd.DataFrame, filtered_df.groupby("categorie", as_index=False)["total_affiche"].sum()).sort_values(by="total_affiche", ascending=False)
            top_customers = cast(pd.DataFrame, filtered_df.groupby("client_name", as_index=False)["total_affiche"].sum()).sort_values(by="total_affiche", ascending=False).head(top_limit)

        col1, col2, col3 = st.columns(3)
        col1.metric("Revenue total", format_currency(revenue_total, selected_devise))
        col2.metric("Depense moyenne (top)", format_currency(panier_moyen, selected_devise))
        col3.metric("Clients top affiches", f"{clients_actifs}")

        show_details_table = False

# Etape 12) Graphique 1 - Revenue par mois (trend)
if revenue_month.empty:
    st.info("Aucune donnee revenue par mois a afficher.")
    st.stop()

revenue_month = revenue_month.copy()
revenue_month["mois"] = revenue_month["mois"].astype(str)
revenue_month["total_affiche"] = pd.to_numeric(revenue_month["total_affiche"], errors="coerce")
revenue_month = revenue_month.dropna(subset=["total_affiche"]).sort_values(by="mois")

fig_month, ax_month = plt.subplots(figsize=(8.8, 4.8))
fig_month.patch.set_facecolor(chart_face)
ax_month.set_facecolor(chart_face)
ax_month.plot(
    revenue_month["mois"],
    revenue_month["total_affiche"],
    marker="o",
    linewidth=2.8,
    color=month_line,
)
ax_month.fill_between(
    revenue_month["mois"],
    revenue_month["total_affiche"],
    color=month_line,
    alpha=0.12,
)
ax_month.set_title("Revenue par mois", fontsize=13, fontweight="bold", color=text_color)
ax_month.set_xlabel("Mois", color=text_color)
ax_month.set_ylabel(f"Revenue ({selected_devise})", color=text_color)
ax_month.grid(axis="y", linestyle="--", alpha=0.25, color=grid_color)
ax_month.spines["top"].set_visible(False)
ax_month.spines["right"].set_visible(False)
ax_month.tick_params(axis="x", rotation=35, colors=text_color)
ax_month.tick_params(axis="y", colors=text_color)

for x_val, y_val in zip(revenue_month["mois"], revenue_month["total_affiche"]):
    ax_month.annotate(
        f"{y_val:,.0f}".replace(",", " "),
        (x_val, y_val),
        ha="center",
        va="bottom",
        fontsize=8,
        color=text_color,
        xytext=(0, 5),
        textcoords="offset points",
    )

fig_month.tight_layout()


# Etape 13) Graphique 2 - Revenue par categorie
if "categorie" in revenue_cat.columns:
    revenue_cat["categorie"] = revenue_cat["categorie"].fillna("Inconnue").astype(str)
if "total_affiche" in revenue_cat.columns:
    revenue_cat["total_affiche"] = pd.to_numeric(revenue_cat["total_affiche"], errors="coerce")
revenue_cat = revenue_cat.dropna(subset=["total_affiche"])
revenue_cat = revenue_cat.loc[revenue_cat["total_affiche"] > 0].copy()

if revenue_cat.empty:
    st.info("Aucune donnee revenue par categorie a afficher.")
    st.stop()

revenue_cat = revenue_cat.sort_values(by="total_affiche", ascending=False)
fig_cat, ax_cat = plt.subplots(figsize=(8.5, 4.8))
fig_cat.patch.set_facecolor(chart_face)
ax_cat.set_facecolor(chart_face)
bars_cat = ax_cat.bar(
    revenue_cat["categorie"].astype(str),
    revenue_cat["total_affiche"],
    color=cat_colors[: len(revenue_cat)],
    edgecolor=text_color,
    linewidth=0.6,
)
ax_cat.set_title("Revenue par categorie", fontsize=13, fontweight="bold", color=text_color)
ax_cat.set_xlabel("Categorie", color=text_color)
ax_cat.set_ylabel(f"Revenue ({selected_devise})", color=text_color)
ax_cat.grid(axis="y", linestyle="--", alpha=0.25, color=grid_color)
ax_cat.spines["top"].set_visible(False)
ax_cat.spines["right"].set_visible(False)
ax_cat.tick_params(axis="x", rotation=25, colors=text_color)
ax_cat.tick_params(axis="y", colors=text_color)

for bar in bars_cat:
    value = bar.get_height()
    ax_cat.annotate(
        f"{value:,.0f}".replace(",", " "),
        (bar.get_x() + bar.get_width() / 2, value),
        ha="center",
        va="bottom",
        fontsize=8,
        color=text_color,
        xytext=(0, 4),
        textcoords="offset points",
    )

fig_cat.tight_layout()


# Etape 14) Graphique 3 - Top clients
if "client_name" in top_customers.columns:
    top_customers["client_name"] = top_customers["client_name"].fillna("Client inconnu").astype(str)
if "total_affiche" in top_customers.columns:
    top_customers["total_affiche"] = pd.to_numeric(top_customers["total_affiche"], errors="coerce")
top_customers = top_customers.dropna(subset=["total_affiche"]).sort_values(by="total_affiche", ascending=False).head(top_limit)
top_customers = top_customers.loc[top_customers["total_affiche"] > 0].copy()

if top_customers.empty:
    st.info("Aucune donnee top clients a afficher.")
    st.stop()

top_customers = top_customers.sort_values(by="total_affiche", ascending=True)
fig_top, ax_top = plt.subplots(figsize=(8.5, 5.2))
fig_top.patch.set_facecolor(chart_face)
ax_top.set_facecolor(chart_face)

# Couleurs differentes pour chaque client
colors_top = mpl.colormaps["tab20"](np.linspace(0, 1, len(top_customers)))
bars_top = ax_top.barh(
    top_customers["client_name"].astype(str),
    top_customers["total_affiche"],
    color=colors_top,
    edgecolor="#1f2937",
    linewidth=0.6,
)
ax_top.set_title("Top 10 clients par depense", fontsize=13, fontweight="bold", color=text_color)
ax_top.set_xlabel(f"Depense totale ({selected_devise})", color=text_color)
ax_top.set_ylabel("Client", color=text_color)
ax_top.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{x:,.0f}".replace(",", " ")))
ax_top.grid(axis="x", linestyle="--", alpha=0.25, color=grid_color)
ax_top.grid(False, axis="y")
ax_top.spines["top"].set_visible(False)
ax_top.spines["right"].set_visible(False)
ax_top.tick_params(axis="x", colors=text_color)
ax_top.tick_params(axis="y", colors=text_color)

# Espace a droite pour eviter que les valeurs soient coupees
max_top = float(top_customers["total_affiche"].max())
ax_top.set_xlim(0, max_top * 1.16)

label_bg = "#0f172a" if selected_theme == "Sombre" else "white"

for bar in bars_top:
    value = bar.get_width()
    ax_top.annotate(
        f"{value:,.0f}".replace(",", " "),
        (value, bar.get_y() + bar.get_height() / 2),
        ha="left",
        va="center",
        fontsize=8,
        color=text_color,
        xytext=(6, 0),
        textcoords="offset points",
        clip_on=False,
        bbox=dict(facecolor=label_bg, alpha=0.9, edgecolor="none", pad=1.3),
    )

fig_top.tight_layout()


# Etape 15) Affichage des graphiques
left_col, right_col = st.columns(2)
with left_col:
    st.pyplot(fig_month, use_container_width=True)
with right_col:
    st.pyplot(fig_cat, use_container_width=True)

st.pyplot(fig_top, use_container_width=True)


# Etape 16) Tableau de details (uniquement en mode SQLite)
if show_details_table:
    st.subheader("Apercu des donnees filtrees")
    st.dataframe(final_table.sort_values(by="date_commande", ascending=False), width="stretch")
