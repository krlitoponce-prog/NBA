import streamlit as st
import requests
import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# --- 1. CONFIGURACIÓN Y BASE DE DATOS ---
st.set_page_config(page_title="NBA AI PREDICTOR V10.5 FINAL", layout="wide", page_icon="🏀")

def init_db():
    conn = sqlite3.connect('nba_historial.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS predicciones 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, equipo_l TEXT, equipo_v TEXT,
                  pred_total REAL, casino_total REAL, real_total REAL DEFAULT NULL)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. BASES DE DATOS MAESTRAS COMPLETAS (30 EQUIPOS) ---
TEAM_SKILLS = {
    "Celtics": [10, 8, 8, 8], "Thunder": [9, 8, 7, 10], "Nuggets": [8, 10, 9, 7],
    "Cavaliers": [8, 9, 8, 7], "Timberwolves": [7, 9, 10, 7], "Knicks": [8, 8, 9, 6],
    "Mavericks": [10, 7, 7, 8], "Suns": [9, 7, 7, 7], "Pacers": [9, 7, 6, 10],
    "Lakers": [7, 9, 8, 8], "Warriors": [10, 6, 7, 9], "Kings": [8, 8, 7, 9],
    "Magic": [6, 9, 8, 7], "76ers": [8, 8, 8, 7], "Pelicans": [7, 8, 8, 7],
    "Heat": [7, 8, 7, 6], "Rockets": [7, 9, 9, 8], "Clippers": [8, 8, 7, 7],
    "Grizzlies": [7, 8, 8, 8], "Bulls": [7, 7, 7, 8], "Hawks": [8, 7, 7, 9],
    "Nets": [7, 7, 6, 8], "Raptors": [7, 7, 7, 8], "Jazz": [8, 7, 8, 9],
    "Spurs": [7, 8, 7, 8], "Hornets": [7, 6, 7, 8], "Trail Blazers": [6, 7, 7, 7],
    "Pistons": [6, 7, 8, 7], "Wizards": [7, 6, 6, 9], "Bucks": [9, 8, 8, 7]
}

ADVANCED_STATS_FALLBACK = {
    "Celtics": [123.5, 110.5], "Thunder": [119.5, 110.0], "Nuggets": [118.0, 112.0],
    "76ers": [116.5, 113.5], "Cavaliers": [117.2, 110.2], "Lakers": [116.0, 115.0],
    "Warriors": [117.5, 115.8], "Knicks": [118.0, 111.5], "Mavericks": [118.8, 115.2],
    "Bucks": [117.0, 116.2], "Timberwolves": [114.5, 108.2], "Suns": [117.8, 116.0],
    "Pacers": [121.5, 120.0], "Kings": [116.8, 115.5], "Heat": [114.0, 111.8],
    "Magic": [111.5, 109.5], "Clippers": [115.5, 114.0], "Rockets": [113.8, 112.5],
    "Pelicans": [115.0, 113.8], "Hawks": [118.5, 121.2], "Grizzlies": [113.0, 112.8],
    "Bulls": [114.2, 116.5], "Nets": [112.5, 116.8], "Raptors": [113.2, 118.0],
    "Jazz": [115.8, 120.5], "Spurs": [111.0, 115.2], "Hornets": [110.2, 119.5],
    "Pistons": [109.5, 118.0], "Wizards": [111.8, 122.5], "Trail Blazers": [110.0, 117.5]
}

TEAM_QUARTER_DNA = {
    "Celtics": [0.27, 0.26, 0.24, 0.23], "Thunder": [0.26, 0.26, 0.25, 0.23],
    "Nuggets": [0.25, 0.25, 0.26, 0.24], "76ers": [0.26, 0.25, 0.24, 0.25],
    "Cavaliers": [0.26, 0.26, 0.24, 0.24], "Lakers": [0.24, 0.25, 0.24, 0.27],
    "Warriors": [0.23, 0.24, 0.30, 0.23], "Knicks": [0.25, 0.25, 0.26, 0.24],
    "Mavericks": [0.24, 0.24, 0.25, 0.27], "Bucks": [0.24, 0.25, 0.23, 0.28],
    "Timberwolves": [0.25, 0.26, 0.24, 0.25], "Suns": [0.25, 0.25, 0.25, 0.25],
    "Pacers": [0.28, 0.27, 0.24, 0.21], "Kings": [0.27, 0.26, 0.24, 0.23],
    "Heat": [0.23, 0.24, 0.25, 0.28], "Magic": [0.24, 0.25, 0.26, 0.25],
    "Clippers": [0.25, 0.25, 0.25, 0.25], "Rockets": [0.24, 0.24, 0.26, 0.26],
    "Pelicans": [0.25, 0.26, 0.24, 0.25], "Hawks": [0.27, 0.26, 0.24, 0.23],
    "Grizzlies": [0.24, 0.24, 0.25, 0.27], "Bulls": [0.25, 0.24, 0.24, 0.27],
    "Nets": [0.24, 0.24, 0.24, 0.28], "Raptors": [0.25, 0.25, 0.25, 0.25],
    "Jazz": [0.23, 0.24, 0.26, 0.27], "Spurs": [0.24, 0.24, 0.25, 0.27],
    "Hornets": [0.26, 0.24, 0.24, 0.26], "Pistons": [0.24, 0.24, 0.24, 0.28],
    "Wizards": [0.26, 0.25, 0.23, 0.26], "Trail Blazers": [0.24, 0.24, 0.25, 0.27]
}

STARS_DB = {
    "tatum": 0.12, "jokic": 0.12, "doncic": 0.12, "james": 0.10, "curry": 0.10,
    "embiid": 0.12, "antetokounmpo": 0.12, "davis": 0.10, "durant": 0.10,
    "booker": 0.09, "gilgeous": 0.11, "brunson": 0.10, "wembanayama": 0.09, "haliburton": 0.08
}

# --- 3. FUNCIONES ---
@st.cache_data(ttl=600)
def get_espn_injuries():
    try:
        res = requests.get("https://espndeportes.espn.com/basquetbol/nba/lesiones", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        injuries = {}
        for title in soup.find_all('div', class_='Table__Title'):
            team_raw = title.text.strip().lower()
            team_key = "76ers" if "76ers" in team_raw else team_raw.split()[-1].capitalize()
            rows = title.find_parent('div', class_='ResponsiveTable').find_all('tr', class_='Table__TR')
            injuries[team_key] = [r.find_all('td')[0].text.strip() for r in rows[1:]]
        return injuries
    except: return {}

def calculate_injury_penalty(team_nick, injuries_db):
    bajas = injuries_db.get(team_nick, [])
    penalty = 0.0
    detected = []
    for p in bajas:
        is_star = False
        for s, val in STARS_DB.items():
            if s in p.lower():
                penalty += val
                detected.append(f"⭐⭐⭐ {p}")
                is_star = True
                break
        if not is_star:
            penalty += 0.015
            detected.append(f"⭐ {p}")
    return min(0.35, penalty), detected

# --- 4. SIDEBAR (V9.0 STYLE) ---
with st.sidebar:
    st.title("⚙️ CONTROL ROOM V10.5")
    if st.button("🔄 REFRESCAR DATOS API"): st.rerun()
    
    st.info("Betano/Bet365: Integración manual por ahora.")
    
    st.header("🦓 Árbitros")
    ref_trend = st.selectbox("Tendencia", ["Neutral", "Over (Pitan Mucho)", "Under (Dejan Jugar)"])
    
    st.header("💰 Casino (Manual)")
    linea_total_puntos = st.number_input("Línea Total Puntos", value=220.5)
    handicap_local_casino = st.number_input("Hándicap Local", value=-4.5)
    
    st.header("🔋 Fatiga (B2B)")
    b2b_local = st.toggle("Local jugó ayer")
    b2b_visita = st.toggle("Visita jugó ayer (+Castigo)")

# --- 5. CUERPO PRINCIPAL ---
st.title("🏀 NBA AI PRO: V10.5 FINAL")

inj_db = get_espn_injuries()
with st.expander("🚑 REPORTE DE BAJAS E IMPACTO (CLIC PARA ABRIR)"):
    if inj_db:
        st.write(inj_db)
    else:
        st.warning("No se pudieron cargar lesiones. Verifique conexión.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("EQUIPO LOCAL")
    l_team = st.selectbox("Seleccionar Local", sorted(TEAM_SKILLS.keys()), key="local_sel")
    st.caption("Racha: 🔥 On Fire (8-2)")
    
    pen_l, list_l = calculate_injury_penalty(l_team, inj_db)
    st.error(f"Impacto Bajas: -{round(pen_l*100, 1)}% Potencial")
    for p in list_l: st.caption(p)
    
    veng_l_active = st.checkbox("🔥 Factor Venganza Local")

with col2:
    st.subheader("EQUIPO VISITANTE")
    v_team = st.selectbox("Seleccionar Visitante", sorted(TEAM_SKILLS.keys()), key="visita_sel")
    st.caption("Racha: 📉 Negativa (3-7)")
    
    pen_v, list_v = calculate_injury_penalty(v_team, inj_db)
    st.error(f"Impacto Bajas: -{round(pen_v*100, 1)}% Potencial")
    for p in list_v: st.caption(p)
    
    veng_v_active = st.checkbox("🔥 Factor Venganza Visita")

if st.button("🚀 EJECUTAR SIMULACIÓN IA", type="primary"):
    # Parámetros de la Base de Datos
    base_score_l = ADVANCED_STATS_FALLBACK[l_team][0]
    base_score_v = ADVANCED_STATS_FALLBACK[v_team][0]
    
    # Modificadores V9.0
    ref_mod = 1.04 if "Over" in ref_trend else (0.96 if "Under" in ref_trend else 1.0)
    fat_l = 0.96 if b2b_local else 1.0
    fat_v = 0.95 if b2b_visita else 1.0
    veng_l_val = 2.8 if veng_l_active else 0
    veng_v_val = 2.2 if veng_v_active else 0
    
    # Cálculo Final
    final_l = ((base_score_l * (1 - pen_l) * fat_l) + veng_l_val + 2.5) * ref_mod
    final_v = ((base_score_v * (1 - pen_v) * fat_v) + veng_v_val) * ref_mod
    
    total_ia = round(final_l + final_v, 1)
    spread_ia = round(final_l - final_v, 1)

    # --- MÉTRICAS V9.0 ---
    st.divider()
    m1, m2, m3 = st.columns([2, 1, 1])
    
    with m1:
        st.markdown(f"### {l_team} {int(final_l)} - {int(final_v)} {v_team}")
        st.markdown(f"🏆 GANA {'LOCAL' if final_l > final_v else 'VISITA'} por {abs(spread_ia)} pts")

    with m2:
        diff_p = round(total_ia - linea_total_puntos, 1)
        st.metric("TOTAL PUNTOS", total_ia, f"{diff_p} vs Casino")
        st.caption(f"PROYECCIÓN: {'OVER' if diff_p > 0 else 'UNDER'}")

    with m3:
        # Valor del spread contra el hándicap del casino
        val_spread = round(spread_ia + handicap_local_casino, 1)
        st.metric("SPREAD REAL", spread_ia, f"{val_spread} Valor")

    # --- DESGLOSE POR CUARTOS ---
    st.subheader("🗓️ Desglose por Cuartos")
    dna_l = TEAM_QUARTER_DNA.get(l_team, [0.25, 0.25, 0.25, 0.25])
    dna_v = TEAM_QUARTER_DNA.get(v_team, [0.25, 0.25, 0.25, 0.25])
    
    df_q = pd.DataFrame({
        "Equipo": [l_team, v_team],
        "Q1": [round(final_l * dna_l[0], 1), round(final_v * dna_v[0], 1)],
        "Q2": [round(final_l * dna_l[1], 1), round(final_v * dna_v[1], 1)],
        "Q3": [round(final_l * dna_l[2], 1), round(final_v * dna_v[2], 1)],
        "Q4": [round(final_l * dna_l[3], 1), round(final_v * dna_v[3], 1)],
        "TOTAL": [round(final_l, 1), round(final_v, 1)]
    })
    st.table(df_q)

    # Registro en DB
    conn = sqlite3.connect('nba_historial.db')
    c = conn.cursor()
    c.execute("INSERT INTO predicciones (fecha, equipo_l, equipo_v, pred_total, casino_total) VALUES (?,?,?,?,?)",
              (datetime.now().strftime("%Y-%m-%d"), l_team, v_team, total_ia, linea_total_puntos))
    conn.commit()
    conn.close()

st.divider()
st.subheader("🔥 Matchup Heatmap")
h_data = pd.DataFrame({l_team: TEAM_SKILLS[l_team], v_team: TEAM_SKILLS[v_team]}, 
                      index=["Triple", "Pintura", "Rebote", "Ritmo"])
st.bar_chart(h_data)