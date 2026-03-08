import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from src.etl.database import create_connection
from src.dashboard.charts import make_chart
from src.dashboard.chat import ask_groq
from src.dashboard.queries import (
    build_where, get_agencies, get_kpis, get_cost_by_agency,
    get_off_hours_by_agency, get_idle_heatmap, get_daily_cost_trend,
)

load_dotenv()


# --- Page config ---
st.set_page_config(
    page_title="GPS Fleet Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }

    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 12px 16px;
        text-align: center;
    }
    [data-testid="stMetric"] label {
        color: #e0e0e0 !important;
        font-size: 0.8rem;
        display: flex;
        justify-content: center;
        width: 100%;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 1.4rem;
        text-align: center;
        width: 100%;
    }

    [data-testid="stSidebar"] [data-testid="stChatMessage"] {
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

conn = create_connection()

# --- Header ---
st.title("GPS Fleet Analytics")
st.subheader("Analisis de datos de GPS de unidades de transporte")

# --- Filters ---
all_agencies = get_agencies(conn)

f1, f2, f3 = st.columns(3)
with f1:
    sel_agencies = st.multiselect("Agencia", all_agencies, default=[], placeholder="Todas")
with f2:
    sel_months = st.multiselect("Mes", ["December", "January"], default=[], placeholder="Todos")
with f3:
    sel_horario = st.selectbox("Horario", ["Todos", "Dentro de horario", "Fuera de horario"])

where, params = build_where(sel_agencies, sel_months, sel_horario)

# --- KPI cards ---
kpis = get_kpis(conn, where, params)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Costo Total", f"${int(kpis['total_cost'][0] or 0):,}")
c2.metric("Costo Fuera de Horario", f"${int(kpis['off_hours_cost'][0] or 0):,}")
c3.metric("Litros Consumidos", f"{int(kpis['total_liters'][0] or 0):,}")
c4.metric("Costo Promedio / Unidad", f"${int(kpis['cost_per_unit'][0] or 0):,}")
c5.metric("Costo Promedio / Viaje", f"${float(kpis['cost_per_trip'][0] or 0):,.2f}")

# --- Chart data (filtered) ---
chart_data = {
    "bar_h": get_cost_by_agency(conn, where, params),
    "donut": get_off_hours_by_agency(conn, where, params),
    "heatmap": get_idle_heatmap(conn, where, params),
    "line": get_daily_cost_trend(conn, where, params),
}
chart_titles = {
    "bar_h": "Costo de Combustible por Agencia",
    "donut": "Viajes Fuera de Horario por Agencia",
    "heatmap": "Inactividad por Agencia y Dia (horas)",
    "line": "Tendencia Diaria de Costo de Combustible",
}

# --- 4 charts in 2x2 grid ---
row1_left, row1_right = st.columns(2)
row2_left, row2_right = st.columns(2)

with row1_left:
    fig1 = make_chart(chart_data["bar_h"], "bar_h", chart_titles["bar_h"])
    if fig1:
        st.plotly_chart(fig1, width="stretch")

with row1_right:
    fig2 = make_chart(chart_data["donut"], "donut", chart_titles["donut"])
    if fig2:
        st.plotly_chart(fig2, width="stretch")

with row2_left:
    fig3 = make_chart(chart_data["heatmap"], "heatmap", chart_titles["heatmap"])
    if fig3:
        st.plotly_chart(fig3, width="stretch")

with row2_right:
    fig4 = make_chart(chart_data["line"], "line", chart_titles["line"])
    if fig4:
        st.plotly_chart(fig4, width="stretch")

# --- Chat panel (sidebar) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Chat con tus datos")
    st.caption('Pregunta en espanol. Ej: "Top 10 unidades mas caras"')

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["text"])
            if "df" in msg:
                st.dataframe(msg["df"], hide_index=True)

    if prompt := st.chat_input("Escribe tu pregunta..."):
        st.session_state.messages.append(
            {"role": "user", "text": prompt}
        )

        result = ask_groq(prompt)
        sql = result.get("sql", "")
        answer = result.get("answer", "")

        if not sql:
            st.session_state.messages.append(
                {"role": "assistant", "text": answer}
            )
        else:
            try:
                df_result = pd.read_sql(sql, conn)
                msg_data = {"role": "assistant", "text": answer}
                if not df_result.empty:
                    msg_data["df"] = df_result
                st.session_state.messages.append(msg_data)
            except Exception as e:
                st.session_state.messages.append(
                    {"role": "assistant", "text": f"Error: {e}"}
                )

        st.rerun()

conn.close()
