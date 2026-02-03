import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# --- 1. BASE DE DATOS MEJORADA ---
def init_db():
    conn = sqlite3.connect('nba_historial.db')
    c = conn.cursor()
    # Tabla para guardar lo que la IA predijo
    c.execute('''CREATE TABLE IF NOT EXISTS predicciones 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  fecha TEXT, 
                  equipo_l TEXT, 
                  equipo_v TEXT,
                  pred_total REAL, 
                  casino_total REAL,
                  real_total REAL DEFAULT NULL)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. FUNCIONES DE GESTIÓN DE RESULTADOS ---
def guardar_prediccion(l, v, p_t, c_t):
    conn = sqlite3.connect('nba_historial.db')
    c = conn.cursor()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO predicciones (fecha, equipo_l, equipo_v, pred_total, casino_total) VALUES (?,?,?,?,?)",
              (fecha_hoy, l, v, p_t, c_t))
    conn.commit()
    conn.close()

def actualizar_resultado_real(p_id, real_score):
    conn = sqlite3.connect('nba_historial.db')
    c = conn.cursor()
    c.execute("UPDATE predicciones SET real_total = ? WHERE id = ?", (real_score, p_id))
    conn.commit()
    conn.close()

# --- 3. INTERFAZ EN EL SIDEBAR (PARA DÍAS ANTERIORES) ---
with st.sidebar:
    st.header("📝 REGISTRO HISTÓRICO")
    
    # Selector de fecha para buscar partidos de hace 2 días o más
    fecha_consulta = st.date_input("Consultar fecha:", datetime.now() - timedelta(days=2))
    fecha_str = fecha_consulta.strftime("%Y-%m-%d")
    
    conn = sqlite3.connect('nba_historial.db')
    df_pendientes = pd.read_sql_query(f"SELECT * FROM predicciones WHERE fecha = '{fecha_str}'", conn)
    conn.close()
    
    if not df_pendientes.empty:
        st.subheader(f"Partidos del {fecha_str}")
        for index, row in df_pendientes.iterrows():
            with st.expander(f"{row['equipo_l']} vs {row['equipo_v']}"):
                st.write(f"Predicción IA: {row['pred_total']}")
                resultado_input = st.number_input(f"Score Total Real", key=f"res_{row['id']}", value=0.0)
                if st.button(f"Confirmar {row['id']}", key=f"btn_{row['id']}"):
                    actualizar_resultado_real(row['id'], resultado_input)
                    st.success("✅ ¡Guardado!")
                    st.rerun()
    else:
        st.caption("No hay predicciones guardadas para esta fecha.")

# --- 4. CÁLCULO DE EFICACIA REAL ---
st.title("🏀 NBA AI PRO V10.1")

conn = sqlite3.connect('nba_historial.db')
# Solo tomamos partidos que ya tienen un resultado real ingresado
df_stats = pd.read_sql_query("SELECT * FROM predicciones WHERE real_total IS NOT NULL", conn)
conn.close()

if not df_stats.empty:
    # Error = Valor Absoluto de (Predicción - Real)
    df_stats['error'] = abs(df_stats['pred_total'] - df_stats['real_total'])
    margen_promedio = round(df_stats['error'].mean(), 2)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Eficacia (Margen Error)", f"{margen_promedio} pts")
    c2.metric("Partidos Analizados", len(df_stats))
    # Porcentaje de acierto al Over/Under comparado con casino
    # (Lógica: Si ambos son > línea o ambos son < línea, es acierto)
    df_stats['acierto'] = ((df_stats['pred_total'] > df_stats['casino_total']) & (df_stats['real_total'] > df_stats['casino_total'])) | \
                          ((df_stats['pred_total'] < df_stats['casino_total']) & (df_stats['real_total'] < df_stats['casino_total']))
    pct_acierto = round(df_stats['acierto'].mean() * 100, 1)
    c3.metric("Acierto O/U", f"{pct_acierto}%")

st.divider()

# --- 5. BOTÓN PARA GUARDAR LA PREDICCIÓN ACTUAL ---
# (Agrega esto dentro de tu botón principal de "CALCULAR")
# if st.button("🚀 EJECUTAR SIMULACIÓN IA"):
#    ... tus cálculos ...
#    guardar_prediccion(l_nick, v_nick, total_ia, linea_ou)
#    st.info("📍 Predicción guardada en la base de datos para seguimiento.")