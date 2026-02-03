import streamlit as st
import requests
import pandas as pd
import sqlite3
import altair as alt
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Intentar importar librerías de la NBA
try:
    from nba_api.stats.endpoints import leaguestandings, leaguedashteamstats
    NBA_API_AVAILABLE = True
except:
    NBA_API_AVAILABLE = False

# --- 1. CONFIGURACIÓN Y BASE DE DATOS ---
st.set_page_config(page_title="NBA AI PREDICTOR V10.2", layout="wide", page_icon="🏀")

def init_db():
    conn = sqlite3.connect('nba_historial.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS predicciones 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  fecha TEXT, equipo_l TEXT, equipo_v TEXT,
                  pred_total REAL, casino_total REAL,
                  real_total REAL DEFAULT NULL)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. BASES DE DATOS MAESTRAS (30 EQUIPOS) ---
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
    "Celtics": [123.5, 110.5, 1.12, 4.8, 0.99], "Thunder": [119.5, 110.0, 1.09, 3.8, 1.02],
    "Nuggets": [118.0, 112.0, 1.18, 5.8, 0.97], "76ers": [116.5, 113.5, 1.02, 3.5, 0.98],
    "Cavaliers": [117.2, 110.2, 1.06, 3.8, 0.98], "Lakers": [116.0, 115.0, 1.07, 4.2, 1.03],
    "Warriors": [117.5, 115.8, 1.04, 4.5, 1.02], "Knicks": [118.0, 111.5, 1.05, 4.5, 0.95],
    "Mavericks": [118.8, 115.2, 1.11, 4.0, 0.98], "Bucks": [117.0, 116.2, 0.95, 4.1, 1.01],
    "Timberwolves": [114.5, 108.2, 0.96, 4.0, 0.97], "Suns": [117.8, 116.0, 1.01, 3.8, 0.99],
    "Pacers": [121.5, 120.0, 0.98, 3.6, 1.08], "Kings": [116.8, 115.5, 1.03, 4.2, 1.01],
    "Heat": [114.0, 111.8, 1.08, 4.3, 0.96], "Magic": [111.5, 109.5, 0.96, 3.7, 0.98],
    "Clippers": [115.5, 114.0, 1.03, 3.8, 0.97], "Rockets": [113.8, 112.5, 1.01, 3.6, 1.00],
    "Pelicans": [115.0, 113.8, 0.92, 3.5, 0.99], "Hawks": [118.5, 121.2, 0.95, 3.4, 1.05],
    "Grizzlies": [113.0, 112.8, 1.01, 3.8, 1.01], "Bulls": [114.2, 116.5, 1.04, 3.5, 0.99],
    "Nets": [112.5, 116.8, 0.96, 3.2, 0.99], "Raptors": [113.2, 118.0, 0.94, 3.7, 1.00],
    "Jazz": [115.8, 120.5, 0.98, 4.6, 1.01], "Spurs": [111.0, 115.2, 1.05, 3.6, 1.02],
    "Hornets": [110.2, 119.5, 0.93, 3.2, 1.01], "Pistons": [109.5, 118.0, 0.90, 3.1, 0.99],
    "Wizards": [111.8, 122.5, 0.91, 3.0, 1.04], "Trail Blazers": [110.0, 117.5, 0.93, 3.8, 0.98]
}

STARS_DB = {
    "tatum": [22.5, 18.5, 29.5], "jokic": [31.5, 25.0, 32.1], "doncic": [28.1, 23.5, 35.8], 
    "james": [23.0, 19.0, 28.5], "curry": [24.5, 20.0, 30.2], "embiid": [30.2, 24.5, 34.0], 
    "antetokounmpo": [29.8, 24.0, 32.5], "davis": [25.0, 20.5, 26.8], "durant": [24.0, 21.0, 29.0],
    "booker": [21.5, 18.5, 28.0], "gilgeous": [27.5, 22.0, 31.5], "brunson": [21.5, 17.5, 30.5],
    "wembanayama": [22.0, 18.0, 28.5], "haliburton": [20.0, 17.0, 25.0]
}

# --- 3. FUNCIONES INTELIGENTES (SCRAPING Y CÁLCULO) ---

def get_star_rating(player_name):
    name_lower = player_name.lower()
    for star in STARS_DB.keys():
        if star in name_lower: return "⭐⭐⭐ (Elite)", "elite"
    return "⭐ (Rotación)", 0.015

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
    detected_stars = []
    for player in bajas:
        label, val = get_star_rating(player)
        detected_stars.append(f"{label} {player}")
        if val == "elite": penalty += 0.12
        else: penalty += val
    return min(0.30, penalty), detected_stars

# --- 4. INTERFAZ Y SIDEBAR ---
with st.sidebar:
    st.header("📝 GESTIÓN HISTÓRICA")
    fecha_consulta = st.date_input("Consultar fecha:", datetime.now() - timedelta(days=1))
    
    conn = sqlite3.connect('nba_historial.db')
    df_pendientes = pd.read_sql_query(f"SELECT * FROM predicciones WHERE fecha = '{fecha_consulta.strftime('%Y-%m-%d')}'", conn)
    
    if not df_pendientes.empty:
        for _, row in df_pendientes.iterrows():
            with st.expander(f"{row['equipo_l']} vs {row['equipo_v']}"):
                res_real = st.number_input(f"Total Real", key=f"res_{row['id']}")
                if st.button("Guardar Resultado", key=f"btn_{row['id']}"):
                    c = conn.cursor()
                    c.execute("UPDATE predicciones SET real_total = ? WHERE id = ?", (res_real, row['id']))
                    conn.commit()
                    st.success("¡Hecho!")
                    st.rerun()
    conn.close()

    st.divider()
    st.subheader("🦓 Arbitraje y Casino")
    ref_trend = st.selectbox("Tendencia Árbitros", ["Neutral", "Over (Pitan Mucho)", "Under (Dejan Jugar)"])
    linea_ou = st.number_input("Línea O/U Casino", value=220.50)

# --- 5. CUERPO PRINCIPAL ---
st.title("🏀 NBA AI PREDICTOR V10.2")

inj_db = get_espn_injuries()
stats_db = ADVANCED_STATS_FALLBACK

# Expandible de Lesionados (Reporte General)
with st.expander("🚑 REPORTE DE LESIONADOS (ESPN)"):
    if inj_db:
        cols = st.columns(3)
        for i, (team, players) in enumerate(inj_db.items()):
            with cols[i % 3]:
                st.write(f"**{team}**")
                for p in players:
                    st.caption(f"{get_star_rating(p)[0]} {p}")
    else:
        st.write("No se pudo cargar la data de ESPN en este momento.")

st.divider()

col1, col2 = st.columns(2)
with col1:
    l_nick = st.selectbox("LOCAL", sorted(stats_db.keys()), index=0)
    penal_l, bajas_l = calculate_injury_penalty(l_nick, inj_db)
    if bajas_l:
        st.error(f"Impacto Bajas: -{round(penal_l*100, 1)}%")
        for b in bajas_l: st.caption(b)

with col2:
    v_nick = st.selectbox("VISITANTE", sorted(stats_db.keys()), index=1)
    penal_v, bajas_v = calculate_injury_penalty(v_nick, inj_db)
    if bajas_v:
        st.error(f"Impacto Bajas: -{round(penal_v*100, 1)}%")
        for b in bajas_v: st.caption(b)

if st.button("🚀 ANALIZAR PARTIDO", type="primary"):
    # Parámetros de cálculo
    ref_f = 1.035 if "Over" in ref_trend else (0.965 if "Under" in ref_trend else 1.0)
    
    # Proyección con penalizaciones aplicadas
    proj_l = (stats_db[l_nick][0] * (1 - penal_l) + 2.5) * ref_f
    proj_v = (stats_db[v_nick][0] * (1 - penal_v)) * ref_f
    total_ia = round(proj_l + proj_v, 1)

    # Mostrar Resultados
    st.header(f"Proyección: {l_nick} {int(proj_l)} - {int(proj_v)} {v_nick}")
    
    # PICKS AUTOMÁTICOS
    st.markdown("---")
    diff = total_ia - linea_ou
    if abs(diff) > 8:
        st.success(f"🔥 **VALOR ALTO:** Apostar al {'OVER' if diff > 0 else 'UNDER'} ({total_ia} vs {linea_ou})")
    elif abs(diff) > 4:
        st.info(f"✅ **VALOR MODERADO:** Sugerido {'Over' if diff > 0 else 'Under'}")
    else:
        st.warning("⚖️ **LÍNEA AJUSTADA:** Poco valor hoy.")

    # Guardar en DB para el Historial
    conn = sqlite3.connect('nba_historial.db')
    c = conn.cursor()
    c.execute("INSERT INTO predicciones (fecha, equipo_l, equipo_v, pred_total, casino_total) VALUES (?,?,?,?,?)",
              (datetime.now().strftime("%Y-%m-%d"), l_nick, v_nick, total_ia, linea_ou))
    conn.commit()
    conn.close()

    # Mapa de Matchup
    st.subheader("🔥 Análisis de Matchup")
    chart_data = pd.DataFrame({l_nick: TEAM_SKILLS.get(l_nick, [5,5,5,5]), 
                              v_nick: TEAM_SKILLS.get(v_nick, [5,5,5,5])}, 
                              index=["Triples", "Pintura", "Rebote", "Ritmo"])
    st.bar_chart(chart_data)

st.caption("Los datos se extraen dinámicamente. Verifica siempre las alineaciones finales.")