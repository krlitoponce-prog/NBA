import streamlit as st
import requests
import pandas as pd
import altair as alt
from datetime import datetime
from bs4 import BeautifulSoup

# Intentar importar librerías de la NBA
try:
    from nba_api.stats.endpoints import leaguestandings, leaguedashteamstats
    NBA_API_AVAILABLE = True
except:
    NBA_API_AVAILABLE = False

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI PRO V9.0", layout="wide", page_icon="🏀")

# --- 2. BASE DE DATOS Y CONSTANTES ---

# Base de datos de respaldo (Fallback)
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

# Base de datos de impacto de Estrellas (Cálculo preciso)
STARS_DB = {
    "tatum": [22.5, 18.5, 29.5], "jokic": [31.5, 25.0, 32.1], "doncic": [28.1, 23.5, 35.8], 
    "james": [23.0, 19.0, 28.5], "curry": [24.5, 20.0, 30.2], "embiid": [30.2, 24.5, 34.0], 
    "antetokounmpo": [29.8, 24.0, 32.5], "davis": [25.0, 20.5, 26.8], "durant": [24.0, 21.0, 29.0],
    "booker": [21.5, 18.5, 28.0], "gilgeous": [27.5, 22.0, 31.5], "brunson": [21.5, 17.5, 30.5],
    "wembanayama": [22.0, 18.0, 28.5], "maxey": [21.0, 17.0, 26.5], "fox": [22.0, 18.0, 29.0],
    "morant": [23.0, 18.0, 29.5], "mitchell": [25.0, 19.0, 30.0], "haliburton": [20.0, 17.0, 25.0]
}

# Lista ampliada de jugadores "Nivel 2" (Titulares importantes)
TIER_2_STARS = ["porzingis", "murray", "brown", "adebayo", "george", "randle", "siakam", "ingram", "butler", "banchero", "sengun", "mobley", "holmgren", "williams"]

# --- 3. FUNCIONES INTELIGENTES ---

def get_star_rating(player_name):
    """
    Clasifica al jugador y retorna (TextoVisual, FactorNuméricoDeResta)
    """
    name_lower = player_name.lower()
    
    # Nivel 1: ⭐⭐⭐ ELITE (Usa cálculo matemático preciso después)
    for star in STARS_DB.keys():
        if star in name_lower:
            return "⭐⭐⭐ (Elite)", "elite"
            
    # Nivel 2: ⭐⭐ TITULAR CLAVE (Resta fija aprox 6-7%)
    for star in TIER_2_STARS:
        if star in name_lower:
            return "⭐⭐ (Titular Clave)", 0.065
            
    # Nivel 3: ⭐ ROL (Resta leve 1.5%)
    return "⭐ (Rotación)", 0.015

@st.cache_data(ttl=21600)
def get_live_advanced_stats():
    """Descarga stats reales de la NBA API (Puntos, Pace, etc)"""
    if not NBA_API_AVAILABLE: return ADVANCED_STATS_FALLBACK
    try:
        stats = leaguedashteamstats.LeagueDashTeamStats(season='2024-25').get_data_frames()[0]
        live_map = {}
        for _, row in stats.iterrows():
            name = row['TEAM_NAME'].split()[-1]
            if "76ers" in row['TEAM_NAME']: name = "76ers"
            if "Blazers" in row['TEAM_NAME']: name = "Trail Blazers"
            
            live_map[name] = [
                round(row['PTS']/row['GP'], 1),  # Pts Anotados
                round((row['PTS'] - row['PLUS_MINUS'])/row['GP'], 1), # Pts Recibidos
                1.05, 4.0, 1.0  # Factores base (Pace, TOV, Reb)
            ]
        return live_map
    except: return ADVANCED_STATS_FALLBACK

@st.cache_data(ttl=3600)
def get_l10_stats():
    try:
        standings = leaguestandings.LeagueStandings(season='2024-25').get_dict()
        data = standings['resultSets'][0]['rowSet']
        l10_map = {}
        headers = standings['resultSets'][0]['headers']
        idx_name, idx_l10 = headers.index('TeamName'), headers.index('L10')
        for row in data: l10_map[row[idx_name]] = row[idx_l10]
        return l10_map
    except: return {}

def calculate_inertia(l10_record):
    if not l10_record: return 0.0, "Neutral"
    try:
        wins = int(l10_record.split('-')[0])
        if wins >= 8: return 0.035, "🔥 On Fire"
        elif wins >= 6: return 0.02, "📈 Positiva"
        elif wins <= 2: return -0.035, "🧊 Congelado"
        elif wins <= 4: return -0.015, "📉 Negativa"
        else: return 0.0, "Neutral"
    except: return 0.0, "Neutral"

@st.cache_data(ttl=600)
def get_espn_injuries():
    """Scraping de lesiones desde ESPN"""
    try:
        res = requests.get("https://espndeportes.espn.com/basquetbol/nba/lesiones", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        injuries = {}
        for title in soup.find_all('div', class_='Table__Title'):
            team_raw = title.text.strip().lower()
            team_key = "76ers" if "76ers" in team_raw else team_raw.split()[-1]
            rows = title.find_parent('div', class_='ResponsiveTable').find_all('tr', class_='Table__TR')
            injuries[team_key] = [r.find_all('td')[0].text.strip() for r in rows[1:]]
        return injuries
    except: return {}

def calculate_injury_penalty(team_nick, injuries_db):
    """
    Calcula automáticmente cuánto porcentaje restar al equipo según sus bajas
    """
    bajas = injuries_db.get(team_nick.lower(), [])
    total_penalty = 0.0
    detected_details = []
    
    for player in bajas:
        rating_txt, rating_val = get_star_rating(player)
        
        # Si es Elite, calculamos matemáticamente
        if rating_val == "elite":
            for star, stats in STARS_DB.items():
                if star in player.lower():
                    # Fórmula de impacto: (Pts + Reb + Usage) ponderado
                    impacto = (stats[0]/200) + (stats[1]/200) + (stats[2]/600)
                    total_penalty += impacto
                    detected_details.append(f"{player} {rating_txt}")
        # Si es Titular o Rol, sumamos el valor fijo
        else:
            total_penalty += rating_val
            detected_details.append(f"{player} {rating_txt}")
            
    # Capamos la penalización máxima al 30% para que no rompa el modelo si faltan todos
    return min(0.30, total_penalty), detected_details

# --- 4. CARGA DE DATOS ---
ADVANCED_STATS = get_live_advanced_stats()
inj_db = get_espn_injuries()
l10_data = get_l10_stats()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ CONTROL ROOM V9.0")
    if st.button("🔄 REFRESCAR DATOS API"):
        st.cache_data.clear(); st.rerun()
    
    st.info("ℹ️ Betano/Bet365: Integración en desarrollo. Ingresa cuotas manuales por ahora.")
    
    st.subheader("🦓 Árbitros")
    ref_trend = st.selectbox("Tendencia", ["Neutral", "Over (Pitan Mucho)", "Under (Dejan Jugar)"])
    
    st.divider()
    st.subheader("💰 Casino (Manual)")
    linea_ou = st.number_input("Línea Total Puntos", value=220.0, step=0.5)
    linea_spread = st.number_input("Hándicap Local", value=-4.5, step=0.5)
    
    st.subheader("🔋 Fatiga (B2B)")
    b2b_l = st.toggle("Local jugó ayer", key="b2bl")
    b2b_v = st.toggle("Visita jugó ayer (+Castigo)", key="b2bv")

# --- 6. INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PREDICTOR: AUTO-ADJUST V9.0")

# Sección visual de lesiones (Expandible)
with st.expander("🚑 REPORTE DE BAJAS E IMPACTO (CLIC PARA ABRIR)", expanded=True):
    if inj_db:
        cols = st.columns(3)
        for i, (team, players) in enumerate(inj_db.items()):
            with cols[i % 3]:
                st.markdown(f"**{team.upper()}**")
                if not players:
                    st.caption("✅ Plantilla Saludable")
                for p in players:
                    rating_txt, _ = get_star_rating(p)
                    color = "red" if "⭐⭐⭐" in rating_txt else ("orange" if "⭐⭐" in rating_txt else "gray")
                    st.markdown(f":{color}[{rating_txt}] {p}")
    else:
        st.warning("⚠️ No se pudo conectar con ESPN. Verifica tu conexión.")

st.divider()

# Selectores de Equipos
c1, c2 = st.columns(2)

with c1:
    l_nick = st.selectbox("EQUIPO LOCAL", sorted(ADVANCED_STATS.keys()), index=5)
    st.image(f"https://a.espncdn.com/i/teamlogos/nba/500/{l_nick.lower()}.png", width=100)
    
    # Análisis L10
    rec_l = l10_data.get(l_nick, l10_data.get(l_nick.split()[-1], None))
    bonus_l10_l, status_l = calculate_inertia(rec_l)
    st.markdown(f"**Racha:** {status_l} ({rec_l if rec_l else 'N/A'})")
    
    # Cálculo automático de penalización
    penal_auto_l, bajas_l = calculate_injury_penalty(l_nick, inj_db)
    if penal_auto_l > 0:
        st.error(f"📉 Impacto Bajas: -{round(penal_auto_l*100, 1)}% Potencial")
    
    venganza_l = st.checkbox("🔥 Factor Venganza Local", key="vl")

with c2:
    v_nick = st.selectbox("EQUIPO VISITANTE", sorted(ADVANCED_STATS.keys()), index=23)
    st.image(f"https://a.espncdn.com/i/teamlogos/nba/500/{v_nick.lower()}.png", width=100)
    
    # Análisis L10
    rec_v = l10_data.get(v_nick, l10_data.get(v_nick.split()[-1], None))
    bonus_l10_v, status_v = calculate_inertia(rec_v)
    st.markdown(f"**Racha:** {status_v} ({rec_v if rec_v else 'N/A'})")
    
    # Cálculo automático de penalización
    penal_auto_v, bajas_v = calculate_injury_penalty(v_nick, inj_db)
    if penal_auto_v > 0:
        st.error(f"📉 Impacto Bajas: -{round(penal_auto_v*100, 1)}% Potencial")
        
    venganza_v = st.checkbox("🔥 Factor Venganza Visita", key="vv")

# --- 7. MOTOR DE CÁLCULO (CORE) ---
if st.button("🚀 EJECUTAR SIMULACIÓN IA", type="primary"):
    # Obtener stats base
    s_l, s_v = ADVANCED_STATS[l_nick], ADVANCED_STATS[v_nick]
    
    # Bonos especiales (Altura, Altitud, B2B)
    alt_bonus = 1.025 if l_nick in ["Nuggets", "Jazz"] else 1.0
    penal_b2b_l = 0.035 if b2b_l else 0
    penal_b2b_v = 0.045 if b2b_v else 0 
    
    # Factor Arbitral
    ref_factor = 1.035 if "Over" in ref_trend else (0.965 if "Under" in ref_trend else 1.0)
    
    # Ritmo de juego proyectado (Pace)
    ritmo_p = ((s_l[4] + s_v[4])/2) * (0.98 if (b2b_l or b2b_v) else 1.0) * ref_factor
    
    # --- FÓRMULA MAESTRA CON DEDUCCIONES AUTOMÁTICAS ---
    # Potencial Local = (Ofensiva * (1 - PENALIZACION_LESIONES - B2B + RACHA))
    adj_off_l = s_l[0] * (1 - penal_auto_l - penal_b2b_l + bonus_l10_l + (0.03 if venganza_l else 0))
    adj_off_v = s_v[0] * (1 - penal_auto_v - penal_b2b_v + bonus_l10_v + (0.03 if venganza_v else 0))
    
    pot_l = ((adj_off_l * 0.65) + (s_v[1] * 0.35)) * ritmo_p * alt_bonus
    pot_v = ((adj_off_v * 0.65) + (s_l[1] * 0.35)) * ritmo_p
    
    # Home Court Advantage (Ventaja Localía Base)
    res_l = round(pot_l + 2.5, 1) # +2.5 puntos por ser local
    res_v = round(pot_v, 1)
    
    # --- ADN POR CUARTOS ---
    dna_l = TEAM_QUARTER_DNA.get(l_nick, [0.25, 0.25, 0.25, 0.25])
    dna_v = TEAM_QUARTER_DNA.get(v_nick, [0.25, 0.25, 0.25, 0.25])
    
    q1_l, q2_l, q3_l = [res_l * p for p in dna_l[:3]]
    q1_v, q2_v, q3_v = [res_v * p for p in dna_v[:3]]
    
    # --- DETECCIÓN DE PALIZA (GARBAGE TIME) ---
    cum_l_q3 = q1_l + q2_l + q3_l
    cum_v_q3 = q1_v + q2_v + q3_v
    diff_q3 = cum_l_q3 - cum_v_q3
    
    q4_l, q4_v = res_l * dna_l[3], res_v * dna_v[3]
    
    blowout_msg = ""
    if abs(diff_q3) > 16:
        blowout_msg = "🚨 ALERTA PALIZA: Los titulares descansarán en Q4 (Puntos reducidos)"
        if diff_q3 > 0: # Local gana por mucho
            q4_l *= 0.82; q4_v *= 0.92 # Local se relaja mucho, visita intenta maquillar
        else: # Visita gana por mucho
            q4_v *= 0.85; q4_l *= 0.90 # Visita se relaja, local tira la toalla
            
    final_l, final_v = sum([q1_l, q2_l, q3_l, q4_l]), sum([q1_v, q2_v, q3_v, q4_v])
    total_ia = round(final_l + final_v, 1)
    diff_final = final_l - final_v
    
    # Probabilidad de victoria (Sigmoide)
    wp_l = 1 / (1 + (10 ** (-diff_final / 14.5)))

    # --- RESULTADOS FINALES ---
    st.markdown("---")
    
    if blowout_msg: st.info(blowout_msg)
    
    col_res1, col_res2, col_res3 = st.columns([2, 1, 1])
    
    with col_res1:
        st.subheader(f"{l_nick} {int(final_l)} - {int(final_v)} {v_nick}")
        if diff_final > 0:
            st.success(f"🏆 GANA {l_nick.upper()} por {int(diff_final)} pts")
        else:
            st.error(f"🏆 GANA {v_nick.upper()} por {int(abs(diff_final))} pts")
        st.progress(wp_l, text=f"Confianza IA: {round(wp_l*100, 1)}%")
        
    with col_res2:
        st.metric("TOTAL PUNTOS", total_ia, delta=f"{round(total_ia - linea_ou, 1)} vs Casino")
        if total_ia > linea_ou: st.caption("🟢 PROYECCIÓN: OVER")
        else: st.caption("🔴 PROYECCIÓN: UNDER")

    with col_res3:
        st.metric("SPREAD REAL", round(-diff_final, 1), delta=f"{round((-diff_final) - linea_spread, 1)} Valor")

    # Tabla Detallada
    st.markdown("### 📅 Desglose por Cuartos")
    df_cuartos = pd.DataFrame({
        "Equipo": [l_nick, v_nick],
        "Q1": [round(q1_l,1), round(q1_v,1)],
        "Q2": [round(q2_l,1), round(q2_v,1)],
        "Q3": [round(q3_l,1), round(q3_v,1)],
        "Q4": [round(q4_l,1), round(q4_v,1)],
        "FINAL": [round(final_l,1), round(final_v,1)]
    })
    st.table(df_cuartos)

    # Gráfico
    st.markdown("### 📈 Evolución del Marcador")
    evolucion = pd.DataFrame({
        'Momento': ['Inicio', 'Q1', 'Q2', 'Q3', 'Final'],
        l_nick: [0, q1_l, q1_l+q2_l, q1_l+q2_l+q3_l, final_l],
        v_nick: [0, q1_v, q1_v+q2_v, q1_v+q2_v+q3_v, final_v]
    }).melt('Momento', var_name='Equipo', value_name='Puntos')
    
    chart = alt.Chart(evolucion).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X('Momento', sort=None),
        y='Puntos',
        color='Equipo',
        tooltip=['Momento', 'Equipo', 'Puntos']
    ).properties(height=350)
    
    st.altair_chart(chart, use_container_width=True)

    # Nota sobre Betano
    st.caption("Nota: Las comparaciones con el casino son referenciales basadas en los valores ingresados manualmente en el menú lateral.")