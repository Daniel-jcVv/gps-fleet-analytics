import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

MAX_CHART_ROWS = 15

AGENCY_COLORS = {
    "AGS": "#636EFA",
    "CELAYA": "#EF553B",
    "QUERETARO": "#00CC96",
    "S.L.P.": "#AB63FA",
    "SAN JUAN": "#FFA15A",
    "SILAO": "#19D3F3",
    "TOLUCA": "#FF6692",
    "ZACATECAS": "#B6E880",
}


def cap_rows(df: pd.DataFrame, limit: int = MAX_CHART_ROWS) -> pd.DataFrame:
    """Limit DataFrame to max rows for clean charts."""
    if len(df) > limit:
        return df.head(limit)
    return df


def make_chart(df: pd.DataFrame, chart_type: str = "bar_h", title: str = "") -> go.Figure | None:
    """Create a plotly chart from a DataFrame."""
    if chart_type not in ("heatmap", "line"):
        df = cap_rows(df)
    text_cols = df.select_dtypes(include="object").columns
    num_cols = df.select_dtypes(include="number").columns
    if len(text_cols) == 0 or len(num_cols) == 0:
        return None

    label = text_cols[0]
    value = num_cols[-1]

    if chart_type == "bar_h":
        fig = px.bar(
            df, y=label, x=value, orientation="h",
            text_auto=True, color=label,
            color_discrete_map=AGENCY_COLORS,
        )
        fig.update_layout(
            showlegend=False,
            xaxis_title=value.replace("_", " ").title(),
            yaxis_title="Agencia",
            yaxis=dict(categoryorder="total ascending"),
        )
    elif chart_type == "donut":
        fig = px.pie(
            df, names=label, values=value, hole=0.45,
            color=label, color_discrete_map=AGENCY_COLORS,
        )
    elif chart_type == "heatmap":
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_labels = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
        df.iloc[:, 0] = df.iloc[:, 0].str.replace("AGUASCALIENTES", "AGS")
        pivot = df.pivot(index=df.columns[0], columns=df.columns[1], values=df.columns[2])
        pivot = pivot.reindex(columns=[d for d in day_order if d in pivot.columns])
        pivot.columns = [day_labels[day_order.index(d)] for d in pivot.columns]
        fig = px.imshow(
            pivot, text_auto=True,
            color_continuous_scale="YlOrRd",
            aspect="auto",
        )
        fig.update_layout(
            xaxis_title="Dia de la Semana",
            yaxis_title="Agencia",
        )
    elif chart_type == "line":
        df = df.copy()
        df[label] = pd.to_datetime(df[label])
        df = df.sort_values(label)
        mes_col = text_cols[1] if len(text_cols) > 1 else None
        fig = px.area(
            df, x=label, y=value,
            color=mes_col, markers=True,
            color_discrete_map={"December": "#636EFA", "January": "#EF553B"},
        )
        fig.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Costo MXN",
            legend_title="Mes",
            xaxis=dict(nticks=12, tickformat="%d %b", tickangle=45),
            width=700,
        )
    else:
        return None

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center"),
        margin=dict(l=10, r=10, t=40, b=10),
        height=300,
    )
    return fig
