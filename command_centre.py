"""
Command Centre - Dash + Plotly globe news dashboard
Clean main entry that imports data and classifier modules and builds
presentation (globe figure + UI) and Dash callbacks.
"""

from __future__ import annotations

import math
from typing import Optional

import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback_context, no_update

from feeds import DEFAULT_FEED_HEADERS, NEWS_SOURCES, FeedManager, NewsEvent
from classifiers import EventCategory, CATEGORY_COLOR, CATEGORY_SYMBOL, DEFAULT_CLASSIFIER
from geo import GeoIndex


class GlobeFigureBuilder:
    """Builds the Plotly globe figure from a list of NewsEvent objects.

    Provides helpers to spread overlapping markers and create flow/arc
    traces for movement events.
    """

    @staticmethod
    def _spread_markers(events: list[NewsEvent]) -> list[tuple[float, float]]:
        out: list[tuple[float, float]] = []
        for ev in events:
            base_lat, base_lon = ev.lat, ev.lon
            h = abs(hash((ev.title, ev.lat, ev.lon)))
            angle = (h % 360) * math.pi / 180.0
            jitter = 0.08 * (1 + (h % 7) / 7.0)
            out.append((base_lat + jitter * math.cos(angle), base_lon + jitter * math.sin(angle)))
        return out

    @staticmethod
    def _flow_segments(events: list[NewsEvent], pulse_phase: float) -> list[go.Scattergeo]:
        traces: list[go.Scattergeo] = []
        for ev in events:
            angle = (abs(hash(ev.title)) % 360) * math.pi / 180.0
            step = 0.8 + 0.5 * abs(math.sin(pulse_phase * math.pi))
            offset_lat = ev.lat + 1.2 * step * math.cos(angle)
            offset_lon = ev.lon + 1.2 * step * math.sin(angle)
            traces.append(go.Scattergeo(
                lon=[ev.lon, offset_lon], lat=[ev.lat, offset_lat], mode="lines",
                line=dict(width=1, color="rgba(102, 255, 255, 0.18)", dash="dot"),
                showlegend=False, hoverinfo="skip",
            ))
        return traces

    @staticmethod
    def build(events: list[NewsEvent], pulse_phase: float, rotation_lon: float) -> go.Figure:
        fig = go.Figure()
        adjusted_positions = GlobeFigureBuilder._spread_markers(events)

        fig.add_trace(go.Scattergeo(lon=[], lat=[], mode="markers", showlegend=False, hoverinfo="skip"))

        for category in EventCategory:
            category_indices = [i for i, e in enumerate(events) if e.category == category]
            if not category_indices:
                continue
            size = 14 + 6 * abs(pulse_phase) if category == EventCategory.MILITARY else 11
            fig.add_trace(go.Scattergeo(
                lon=[adjusted_positions[i][1] for i in category_indices],
                lat=[adjusted_positions[i][0] for i in category_indices],
                text=[events[i].title for i in category_indices],
                customdata=category_indices,
                mode="markers",
                marker=dict(
                    size=size,
                    color=CATEGORY_COLOR[category],
                    symbol=CATEGORY_SYMBOL[category],
                    line=dict(width=1, color="white"),
                    opacity=0.6 + 0.3 * abs(pulse_phase),
                ),
                name=category.value.title(),
                showlegend=False,
                hovertemplate="%{text}<extra>" + category.value.title() + "</extra>",
            ))

        for line_trace in GlobeFigureBuilder._flow_segments(events, pulse_phase):
            fig.add_trace(line_trace)

        for ev in events:
            if ev.category == EventCategory.MILITARY and ev.target_lat is not None:
                fig.add_trace(go.Scattergeo(
                    lon=[ev.lon, ev.target_lon],
                    lat=[ev.lat, ev.target_lat],
                    mode="lines",
                    line=dict(width=1.75 + abs(pulse_phase) * 1.5, color=f"rgba(255,102,102,{0.22 + 0.18 * abs(pulse_phase)})", dash="dash"),
                    showlegend=False,
                    hoverinfo="skip",
                ))
                fig.add_trace(go.Scattergeo(
                    lon=[ev.target_lon], lat=[ev.target_lat],
                    mode="markers",
                    marker=dict(size=8 + abs(pulse_phase) * 2, color="#ff9f1c", symbol="diamond",
                                line=dict(width=1, color="rgba(255,255,255,0.9)")),
                    showlegend=False,
                    text=[f"Target: {ev.target_name}"],
                    hovertemplate="%{text}<extra></extra>",
                ))

        fig.update_geos(
            projection_type="orthographic",
            projection_rotation=dict(lon=rotation_lon, lat=10, roll=0),
            showland=True, landcolor="#04130d",
            showocean=True, oceancolor="#031121",
            showcountries=True, countrycolor="#1e9f7d",
            showcoastlines=True, coastlinecolor="#20d8b4",
            showframe=False,
            bgcolor="rgba(0,0,0,0)",
        )
        fig.update_layout(
            showlegend=False,
            paper_bgcolor="#05101c",
            plot_bgcolor="#05101c",
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(font=dict(color="#d5f8ff"), bgcolor="rgba(1,18,31,0.72)", bordercolor="rgba(78, 241, 255, 0.28)", borderwidth=1,
                        orientation="h", yanchor="bottom", y=0.02, x=0.02),
            uirevision="keep-camera",
            transition=dict(duration=300, easing="cubic-in-out"),
        )
        return fig


class UIBuilder:
    @staticmethod
    def build_layout(sources) -> html.Div:
        options = [{'label': s.label, 'value': s.key} for s in sources]
        return html.Div([
            dcc.Store(id='events-store'),
            html.Div([
                html.H2('Command Centre', style={'color': '#8ae6ff', 'fontFamily': 'Georgia, serif', 'marginBottom': '12px'}),
                dcc.Dropdown(id='source-dropdown', options=options, value=options[0]['value'], clearable=False,
                             style={'color': '#000000', 'backgroundColor': '#ffffff', 'borderRadius': '6px'}),
                html.Div(id='status-line', style={'color': '#dbe9ff', 'marginTop': '12px', 'marginBottom': '8px'}),
                html.H4('Recent events', style={'color': '#8ae6ff', 'marginTop': '16px'}),
                html.Div(id='event-ticker', style={'maxHeight': '320px', 'overflowY': 'auto', 'paddingRight': '6px'}),
                html.H4('Time window', style={'color': '#8ae6ff', 'marginTop': '16px'}),
                html.Div([
                    dcc.Slider(id='days-slider', min=1, max=7, step=1, value=2, marks={i: str(i) for i in range(1, 8)}, tooltip={'placement': 'bottom'}),
                    html.Div(id='days-box', style={'marginTop': '8px'})
                ], style={'display': 'flex', 'alignItems': 'center', 'gap': '12px'}),
            ], style={'width': '320px', 'padding': '18px', 'backgroundColor': '#021018', 'boxShadow': 'inset 4px 0 0 rgba(0,0,0,0.6)'}),
            html.Div([
                html.Div([
                    dcc.Graph(id='globe', figure=go.Figure(), style={'height': '80vh'}),
                    html.Div(id='globe-legend', children=[
                        html.Div([html.Span(style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '3px', 'backgroundColor': '#ff4d4d', 'marginRight': '8px'}), html.Span('Military', style={'color': '#e6f9ff'})], style={'display': 'flex', 'alignItems': 'center', 'gap': '6px'}),
                        html.Div([html.Span(style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '50%', 'backgroundColor': '#ffd166', 'marginRight': '8px'}), html.Span('Political', style={'color': '#e6f9ff'})], style={'display': 'flex', 'alignItems': 'center', 'gap': '6px'}),
                        html.Div([html.Span(style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '50%', 'backgroundColor': '#b388ff', 'marginRight': '8px'}), html.Span('Disaster', style={'color': '#e6f9ff'})], style={'display': 'flex', 'alignItems': 'center', 'gap': '6px'}),
                        html.Div([html.Span(style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '50%', 'backgroundColor': '#7fd3ff', 'marginRight': '8px'}), html.Span('General', style={'color': '#e6f9ff'})], style={'display': 'flex', 'alignItems': 'center', 'gap': '6px'}),
                    ], style={'position': 'absolute', 'bottom': '18px', 'left': '18px', 'backgroundColor': 'rgba(3,16,22,0.72)', 'padding': '8px 10px', 'borderRadius': '6px', 'display': 'flex', 'gap': '12px', 'alignItems': 'center'}),
                ], style={'position': 'relative'}),
                dcc.Interval(id='anim-tick', interval=3000, n_intervals=0),
                html.Div(id='detail-panel', style={
                    'color': '#dbe9ff', 'padding': '14px', 'maxHeight': '34vh', 'overflowY': 'auto', 'whiteSpace': 'normal',
                    'backgroundColor': 'rgba(1,6,8,0.88)', 'borderRadius': '6px', 'position': 'absolute', 'bottom': '18px', 'left': '18px', 'right': '18px', 'zIndex': 9999,
                }),
            ], style={'flex': '1', 'padding': '8px', 'position': 'relative'})
        ], style={'display': 'flex', 'gap': '8px', 'backgroundColor': '#01070a', 'height': '100vh', 'padding': '8px'})


class CommandCentreApp:
    """Owns the Dash app: layout, state, and callbacks."""

    def __init__(self):
        self.app = Dash(__name__, title="Command Centre")
        self.events: list[NewsEvent] = []
        self._pulse_t = 0.0
        self._rotation = 0.0
        self._build_layout()
        self._register_callbacks()

    def _build_layout(self) -> None:
        self.app.layout = UIBuilder.build_layout(NEWS_SOURCES)

    def _register_callbacks(self) -> None:
        app = self.app

        @app.callback(
            Output("events-store", "data"),
            Output("status-line", "children"),
            Input("source-dropdown", "value"),
            Input("days-slider", "value"),
        )
        def load_source(source_key: str, days: int):
            source = next(s for s in NEWS_SOURCES if s.key == source_key)
            events = FeedManager(NEWS_SOURCES).fetch(source_key, days=days)
            self.events = events
            payload = [dict(title=e.title, source=e.source, lat=e.lat, lon=e.lon,
                             category=e.category.value if hasattr(e.category, 'value') else str(e.category), target_lat=e.target_lat,
                             target_lon=e.target_lon, target_name=e.target_name,
                             published=e.published) for e in events]
            plural = "day" if days == 1 else "days"
            return payload, f" {len(events)} recent events ({days} {plural}) — {source.label}"

        @app.callback(
            Output("event-ticker", "children"),
            Input("days-slider", "value"),
            Input("events-store", "data"),
        )
        def update_ticker(days, payload):
            if payload is None:
                payload = []
            if not payload:
                return html.Div("No geo-tagged events from the selected window yet.", style={"color": "#eef6ff"})
            items = []
            for row in payload[:14]:
                items.append(html.Div([
                    html.Span("● ", style={"color": "#8ac7ff"}),
                    html.Span(row["title"], style={"color": "#eef6ff"}),
                ], style={"marginBottom": "10px"}))
            return items

        @app.callback(
            Output("days-box", "children"),
            Input("days-slider", "value"),
        )
        def update_days_box(value):
            return html.Div(str(value), style={'width': '40px', 'height': '36px', 'backgroundColor': '#ffffff', 'color': '#000000', 'borderRadius': '6px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'fontWeight': '700'})

        @app.callback(
            Output("globe", "figure"),
            Input("events-store", "data"),
            Input("anim-tick", "n_intervals"),
        )
        def update_globe(payload, n_intervals):
            triggered = [t["prop_id"] for t in callback_context.triggered]
            events = self._rehydrate(payload)
            has_military = any(e.category == EventCategory.MILITARY for e in events)
            if any('anim-tick' in t for t in triggered) and not has_military:
                return no_update
            phase = abs(((n_intervals or 0) * 0.5 % 2.0) - 1.0) if has_military else 0.4
            return GlobeFigureBuilder.build(events, pulse_phase=phase, rotation_lon=0)

        @app.callback(
            Output("detail-panel", "children"),
            Input("globe", "clickData"),
            State("events-store", "data"),
        )
        def show_detail(click_data, payload):
            if not click_data or not payload:
                return no_update
            point = click_data["points"][0]
            title = point.get("text")
            match = next((r for r in payload if r["title"] == title), None)
            if not match:
                return no_update
            children = [
                html.Div(match["category"].upper(), style={"color": "#8ac7ff", "fontWeight": "bold", "marginBottom": "6px"}),
                html.Div(match["title"], style={"color": "#eef6ff", "fontWeight": "bold", "marginBottom": "8px"}),
                html.Div(f"Source: {match['source']}", style={"color": "#dbe9ff"}),
                html.Div(f"Location: {match['lat']:.1f}, {match['lon']:.1f}", style={"color": "#dbe9ff"}),
            ]
            if match.get("target_name"):
                children.append(html.Div(
                    f"Movement toward: {match['target_name']} ({match['target_lat']:.1f}, {match['target_lon']:.1f})",
                    style={"color": "#dbe9ff"}))
            if match.get("published"):
                children.append(html.Div(f"Published: {match['published']}", style={"color": "#dbe9ff"}))
            return children

        @app.callback(
            Output('globe-legend', 'style'),
            Input('detail-panel', 'children'),
        )
        def adjust_legend_pos(detail_children):
            base = {
                'position': 'absolute', 'left': '18px', 'backgroundColor': 'rgba(3,16,22,0.72)',
                'padding': '8px 10px', 'borderRadius': '6px', 'display': 'flex', 'gap': '12px', 'alignItems': 'center'
            }
            if detail_children:
                base['bottom'] = 'calc(6px + 6vh)'
            else:
                base['bottom'] = '18px'
            return base

    @staticmethod
    def _rehydrate(payload) -> list[NewsEvent]:
        if not payload:
            return []
        return [NewsEvent(
            title=r["title"], source=r["source"], lat=r["lat"], lon=r["lon"],
            category=EventCategory(r["category"]), target_lat=r.get("target_lat"),
            target_lon=r.get("target_lon"), target_name=r.get("target_name"),
            published=r.get("published", ""),
        ) for r in payload]

    def run(self, debug: bool = False, port: int = 8050) -> None:
        self.app.run(debug=debug, port=port)


if __name__ == "__main__":
    CommandCentreApp().run()
