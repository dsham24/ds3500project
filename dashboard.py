"""
dashboard.py - U.S. Housing Market & Affordability Dashboard
Run: panel serve dashboard.py --show
"""

import io, html, os
import pandas as pd
import panel as pn
import plotly.express as px
import plotly.graph_objects as go

pn.extension("plotly")

# ── Load data ────────────────────────────────────────────────────────────────

df = pd.read_parquet(os.path.join(os.path.dirname(__file__), "data", "merged.parquet"))

STATE_ABBREV = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA",
    "Colorado":"CO","Connecticut":"CT","Delaware":"DE","District of Columbia":"DC",
    "Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL",
    "Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA",
    "Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN",
    "Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV",
    "New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY",
    "North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR",
    "Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD",
    "Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA",
    "Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY","Puerto Rico":"PR"
}
df["state_abbrev"] = df["state_name"].map(STATE_ABBREV)

METRICS = {
    "price_to_income_ratio":   "Price-to-Income Ratio",
    "median_home_value":       "Median Home Value ($)",
    "median_household_income": "Median Household Income ($)",
    "homeownership_rate":      "Homeownership Rate (%)",
    "median_gross_rent":       "Median Gross Rent ($)",
    "zhvi":                    "Zillow Home Value Index ($)",
}
STATES = sorted(df["state_name"].dropna().unique().tolist())

# ── Widgets ──────────────────────────────────────────────────────────────────

year_slider   = pn.widgets.IntSlider(name="Year", start=int(df["year"].min()),
                                     end=int(df["year"].max()), step=1, value=2020)
metric_select = pn.widgets.Select(name="Metric",
                                  options={v: k for k, v in METRICS.items()},
                                  value="price_to_income_ratio")
state_search  = pn.widgets.AutocompleteInput(name="Search State", options=STATES,
                                             value="California", min_characters=1,
                                             placeholder="Type a state name...")

# ── Chart functions ───────────────────────────────────────────────────────────

def metric_cards(year):
    """Five summary number cards for the selected year."""
    y = df[df["year"] == year]
    return pn.Row(
        pn.indicators.Number(name="Price-to-Income Ratio",
            value=round(y["price_to_income_ratio"].mean(), 2),
            format="{value}x", default_color="#38bdf8"),
        pn.indicators.Number(name="Avg Home Value",
            value=round(y["median_home_value"].mean() / 1000, 1),
            format="${value}K", default_color="#38bdf8"),
        pn.indicators.Number(name="Avg Household Income",
            value=round(y["median_household_income"].mean() / 1000, 1),
            format="${value}K", default_color="#38bdf8"),
        pn.indicators.Number(name="Mortgage Rate",
            value=round(y["MORTGAGE30US"].mean(), 2),
            format="{value}%", default_color="#38bdf8"),
        pn.indicators.Number(name="Avg Gross Rent",
            value=round(y["median_gross_rent"].mean()),
            format="${value}/mo", default_color="#38bdf8"),
        sizing_mode="stretch_width",
    )


def viz1():
    """National median home price vs 30-yr mortgage rate over time."""
    nat = df.groupby("year")[["MORTGAGE30US","MSPUS"]].mean().reset_index().dropna()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=nat["year"], y=nat["MSPUS"],
        name="Median Home Price", line=dict(color="#2563eb", width=3), yaxis="y1"))
    fig.add_trace(go.Scatter(x=nat["year"], y=nat["MORTGAGE30US"],
        name="30-Yr Mortgage Rate", line=dict(color="#f97316", width=3, dash="dash"), yaxis="y2"))
    fig.update_layout(
        paper_bgcolor="#fff", plot_bgcolor="#fff",
        font=dict(color="#111827"), height=420,
        title=dict(text="National Home Price vs. Mortgage Rate", x=0.5),
        xaxis=dict(title="Year", gridcolor="#e5e7eb"),
        yaxis=dict(title="Median Home Price (USD)", tickprefix="$", tickformat=",", gridcolor="#e5e7eb"),
        yaxis2=dict(title="Mortgage Rate (%)", overlaying="y", side="right", showgrid=False),
        legend=dict(bgcolor="rgba(255,255,255,0.9)"),
        hovermode="x unified",
    )
    return fig


def viz2_map(year, metric):
    """Choropleth map of selected metric by state."""
    label = METRICS[metric]
    ydf = df[df["year"] == year].dropna(subset=[metric, "state_abbrev"])
    fig = px.choropleth(ydf, locations="state_abbrev", locationmode="USA-states",
        color=metric, scope="usa", color_continuous_scale="RdYlGn_r",
        hover_name="state_name", labels={metric: label},
        title=f"{label} by State ({year})")
    fig.update_layout(paper_bgcolor="#fff", font=dict(color="#111827"), height=400,
        title=dict(x=0.5),
        geo=dict(bgcolor="#f8fafc", lakecolor="#dbeafe", landcolor="#e2e8f0"))
    return fig


def viz2_bar(year, metric):
    """Top 10 states bar chart for selected metric."""
    label = METRICS[metric]
    ydf = df[df["year"] == year].dropna(subset=[metric]).nlargest(10, metric)
    fig = px.bar(ydf, x=metric, y="state_name", orientation="h",
        color=metric, color_continuous_scale="Blues",
        labels={metric: label, "state_name": "State"},
        title=f"Top 10 States — {label} ({year})")
    fig.update_layout(paper_bgcolor="#fff", plot_bgcolor="#fff",
        font=dict(color="#111827"), height=400, title=dict(x=0.5),
        showlegend=False, coloraxis_showscale=False,
        yaxis=dict(autorange="reversed", gridcolor="#e5e7eb"),
        xaxis=dict(gridcolor="#e5e7eb"))
    return fig


def viz3(state):
    """Home value, income, and price-to-income ratio over time for one state."""
    if state not in STATES:
        state = "California"
    s = df[df["state_name"] == state].sort_values("year")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=s["year"], y=s["median_home_value"],
        name="Home Value", line=dict(color="#2563eb", width=2), yaxis="y1"))
    fig.add_trace(go.Scatter(x=s["year"], y=s["median_household_income"],
        name="Household Income", line=dict(color="#16a34a", width=2), yaxis="y1"))
    fig.add_trace(go.Scatter(x=s["year"], y=s["price_to_income_ratio"],
        name="Price-to-Income Ratio", line=dict(color="#f97316", width=2, dash="dot"), yaxis="y2"))
    fig.update_layout(
        paper_bgcolor="#fff", plot_bgcolor="#fff",
        font=dict(color="#111827"), height=440,
        title=dict(text=f"{state}: Affordability Over Time", x=0.5),
        xaxis=dict(title="Year", gridcolor="#e5e7eb"),
        yaxis=dict(title="USD ($)", tickprefix="$", tickformat=",", gridcolor="#e5e7eb"),
        yaxis2=dict(title="Price-to-Income Ratio", overlaying="y", side="right", showgrid=False),
        legend=dict(bgcolor="rgba(255,255,255,0.9)"),
        hovermode="x unified",
    )
    return fig


def viz4_iframe():
    """
    Animated bar chart as srcdoc iframe so the Play button actually works.
    Panel's Bokeh layer breaks Plotly animation — iframe bypasses this.
    """
    anim = df.dropna(subset=["zhvi","state_name"]).copy()
    top  = anim.groupby("state_name")["zhvi"].mean().nlargest(15).index.tolist()
    anim = anim[anim["state_name"].isin(top)].sort_values(["year","zhvi"])

    fig = px.bar(anim, x="zhvi", y="state_name", animation_frame="year",
        orientation="h", color="zhvi", color_continuous_scale="Blues",
        labels={"zhvi":"Zillow Home Value Index ($)","state_name":"State"},
        title="Home Values Over Time — Top 15 States (Animated)",
        range_x=[0, anim["zhvi"].max() * 1.1])
    fig.update_layout(
        paper_bgcolor="#fff", plot_bgcolor="#fff",
        font=dict(color="#111827"), height=500,
        title=dict(x=0.5), coloraxis_showscale=False,
        yaxis=dict(autorange="reversed", gridcolor="#e5e7eb"),
        xaxis=dict(gridcolor="#e5e7eb"),
        updatemenus=[dict(type="buttons", showactive=False, y=1.15, x=0.5,
            xanchor="center", buttons=[
                dict(label="▶ Play", method="animate",
                     args=[None, dict(frame=dict(duration=900, redraw=True),
                                      fromcurrent=True, mode="immediate")]),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode="immediate")]),
            ])],
        sliders=[dict(active=0,
            currentvalue=dict(prefix="Year: ", visible=True, xanchor="center"),
            pad=dict(t=40),
            steps=[dict(label=str(int(fr.name)), method="animate",
                        args=[[fr.name], dict(frame=dict(duration=300, redraw=True),
                                              mode="immediate")])
                   for fr in fig.frames])]
    )

    buf = io.StringIO()
    fig.write_html(buf, full_html=True, include_plotlyjs="cdn", config={"responsive": True})
    escaped = html.escape(buf.getvalue())
    return pn.pane.HTML(
        f'<iframe srcdoc="{escaped}" style="width:100%;height:560px;border:none;'
        f'background:#fff;border-radius:8px;" frameborder="0"></iframe>',
        sizing_mode="stretch_width", height=570,
    )


# ── Bind widgets to charts ────────────────────────────────────────────────────

cards_bound  = pn.bind(metric_cards, year=year_slider)
map_bound    = pn.bind(viz2_map,     year=year_slider, metric=metric_select)
bar_bound    = pn.bind(viz2_bar,     year=year_slider, metric=metric_select)
trend_bound  = pn.bind(viz3,         state=state_search)

# ── Layout ────────────────────────────────────────────────────────────────────

template = pn.template.FastListTemplate(
    title="U.S. Housing Market & Affordability Dashboard",
    header_background="#0b1220",
    accent_base_color="#38bdf8",
    theme="dark",
    sidebar_width=0,
    main=[pn.Column(

        # Summary metrics
        pn.pane.Markdown("## National Summary Metrics"),
        year_slider,
        cards_bound,
        pn.layout.Divider(),

        # Viz 1
        pn.pane.Markdown("## Visualization 1: National Trends Over Time"),
        pn.pane.Markdown("*Hover over any point for exact values. Click legend to show/hide lines.*"),
        pn.pane.Plotly(viz1(), sizing_mode="stretch_width"),
        pn.layout.Divider(),

        # Viz 2
        pn.pane.Markdown("## Visualization 2: State Comparison — Map & Rankings"),
        pn.pane.Markdown("*Use the Year slider and Metric dropdown to update both charts.*"),
        pn.Row(year_slider, metric_select, sizing_mode="stretch_width"),
        pn.Row(
            pn.pane.Plotly(map_bound, sizing_mode="stretch_width"),
            pn.pane.Plotly(bar_bound, sizing_mode="stretch_width"),
            sizing_mode="stretch_width",
        ),
        pn.layout.Divider(),

        # Viz 3
        pn.pane.Markdown("## Visualization 3: State Drill-Down"),
        pn.pane.Markdown("*Search or type a state name to see its affordability trend.*"),
        state_search,
        pn.pane.Plotly(trend_bound, sizing_mode="stretch_width"),
        pn.layout.Divider(),

        # Viz 4
        pn.pane.Markdown("## Visualization 4: Animated Home Values"),
        pn.pane.Markdown("*Press ▶ Play inside the chart. Use the year slider to jump to any year.*"),
        viz4_iframe(),

        sizing_mode="stretch_width",
    )]
)

template.servable()

if __name__ == "__main__":
    template.show()
