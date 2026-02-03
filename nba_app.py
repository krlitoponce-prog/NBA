import streamlit as st
import requests
import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# --- 1. CONFIGURACIÓN Y BASE DE DATOS ---
st.set_page_config(page_title="NBA AI PREDICTOR V10.5", layout="wide", page_icon="🏀")

def init_db():
    conn = sqlite3.connect('nba_historial.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS predicciones 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, equipo_l TEXT, equipo_v TEXT,
                  pred_total REAL, casino_total REAL, real_total REAL DEFAULT NULL)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. BASES DE DATOS MAESTRAS ---
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
    team: [115.0, 112.0] for team in TEAM_SKILLS.keys() # Simplificado para el ejemplo, usa tus valores previos
}
# (Nota: Mantener tus valores exactos de ADVANCED_STATS_FALLBACK y TEAM_QUARTER_DNA del código anterior)
TEAM_QUARTER_DNA = {
    "Celtics": [0.27, 0.26, 0.24, 0.23], "Lakers": [0.24, 0.25, 0.24, 0.27], # ... (mantener resto)
}

STARS_DB = {"tatum": 0.12, "jokic": 0.12, "doncic": 0.12, "james": 0.10, "curry": 0.10}

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
    linea_total = st.number_input("Línea Total Puntos", value=220.5)
    handicap_local = st.number_input("Hándicap Local", value=-4.5)
    
    st.header("🔋 Fatiga (B2B)")
    b2b_l = st.toggle("Local jugó ayer")
    b2b_v = st.toggle("Visita jugó ayer (+Castigo)")

# --- 5. CUERPO PRINCIPAL ---
st.title("🏀 NBA AI PREDICTOR: AUTO-ADJUST V10.5")

inj_db = get_espn_injuries()
with st.expander("🚑 REPORTE DE BAJAS E IMPACTO (CLIC PARA ABRIR)"):
    st.write(inj_db)

col1, col2 = st.columns(2)

with col1:
    st.subheader("EQUIPO LOCAL")
    l_team = st.selectbox("Seleccionar Local", sorted(TEAM_SKILLS.keys()), key="l_s")
    st.caption("Racha: 🔥 On Fire (8-2)") # Simulado
    
    pen_l, list_l = calculate_injury_penalty(l_team, inj_db)
    st.error(f"Impacto Bajas: -{round(pen_l*100, 1)}% Potencial")
    for p in list_l: st.caption(p)
    
    venganza_l = st.checkbox("🔥 Factor Venganza Local")

with col2:
    st.subheader("EQUIPO VISITANTE")
    v_team = st.selectbox("Seleccionar Visitante", sorted(TEAM_SKILLS.keys()), key="v_s")
    st.caption("Racha: 📉 Negativa (3-7)") # Simulado
    
    pen_v, list_v = calculate_injury_penalty(v_team, inj_db)
    st.error(f"Impacto Bajas: -{round(pen_v*100, 1)}% Potencial")
    for p in list_v: st.caption(p)
    
    venganza_v = st.checkbox("🔥 Factor Venganza Visita")

if st.button("🚀 EJECUTAR SIMULACIÓN IA", type="primary"):
    # Lógica de cálculo
    base_l = 115.0 # Fallback
    base_v = 112.0
    
    # Aplicar modificadores
    ref_mod = 1.04 if "Over" in ref_trend else (0.96 if "Under" in ref_trend else 1.0)
    fatiga_l = 0.96 if b2b_l else 1.0
    fatiga_v = 0.95 if b2b_v else 1.0
    veng_l = 2.5 if venganza_l else 0
    veng_v = 2.0 if venganza_v else 0
    
    res_l = (base_l * (1 - pen_l) * fatiga_l) + veng_l + 2.5
    res_v = (base_v * (1 - pen_v) * fatiga_v) + veng_v
    
    total_puntos = round((res_l + res_v) * ref_mod, 1)
    spread_real = round(res_l - res_v, 1)

    # --- ZONA DE MÉTRICAS (V9.0 STYLE) ---
    st.divider()
    m_col1, m_col2, m_col3 = st.columns([2, 1, 1])
    
    with m_col1:
        color_win = "green" if res_l > res_v else "red"
        st.markdown(f"### {l_team} {int(res_l)} - {int(res_v)} {v_team}")
        st.markdown(f"🏆 GANA {'LOCAL' if res_l > res_v else 'VISITA'} por {abs(spread_real)} pts")

    with m_col2:
        diff_total = round(total_puntos - linea_total, 1)
        st.metric("TOTAL PUNTOS", total_puntos, f"{diff_total} vs Casino")
        st.caption(f"PROYECCIÓN: {'OVER' if diff_total > 0 else 'UNDER'}")

    with m_col3:
        diff_spread = round(spread_real - (handicap_local * -1), 1)
        st.metric("SPREAD REAL", spread_real, f"{diff_spread} Valor")

    # --- DESGLOSE POR CUARTOS ---
    st.subheader("🗓️ Desglose por Cuartos")
    dna_l = TEAM_QUARTER_DNA.get(l_team, [0.25, 0.25, 0.25, 0.25])
    dna_v = TEAM_QUARTER_DNA.get(v_team, [0.25, 0.25, 0.25, 0.25])
    
    df_cuartos = pd.DataFrame({
        "Equipo": [l_team, v_team],
        "Q1": [round(res_l * dna_l[0], 1), round(res_v * dna_v[0], 1)],
        "Q2": [round(res_l * dna_l[1], 1), round(res_v * dna_v[1], 1)],
        "Q3": [round(res_l * dna_l[2], 1), round(res_v * dna_v[2], 1)],
        "Q4": [round(res_l * dna_l[3], 1), round(res_v * dna_v[3], 1)],
        "FINAL": [round(res_l, 1), round(res_v, 1)]
    })
    st.table(df_cuartos)

    # Guardar en Historial
    conn = sqlite3.connect('nba_historial.db')
    c = conn.cursor()
    c.execute("INSERT INTO predicciones (fecha, equipo_l, equipo_v, pred_total, casino_total) VALUES (?,?,?,?,?)",
              (datetime.now().strftime("%Y-%m-%d"), l_team, v_team, total_puntos, linea_total))
    conn.commit()
    conn.close()

st.caption("V10.5 Pro: IA optimizada con factores de fatiga y venganza de la V9.0.")