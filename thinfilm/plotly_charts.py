"""Interactive Plotly charts for optical thin-film demonstration.

Provides publication-quality interactive visualizations for the
teaching platform and competition demos.

Requires: plotly
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import numpy as np

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    raise ImportError("plotly is required: pip install plotly")


# ---------------------------------------------------------------------------
# Color scheme
# ---------------------------------------------------------------------------

COLORS = {
    "R": "#c94f2d",  # MAIN_RED
    "T": "#0f766e",  # TARGET_GREEN
    "A": "#b7791f",  # ABS_GOLD
    "layer_high": "#1d4ed8",  # Blue
    "layer_low": "#d7dde5",  # Light gray
    "substrate": "#f7f8fb",  # Off-white
    "incident": "#ffffff",  # White
    "grid": "#d7dde5",
    "text": "#223046",
    "bg": "#ffffff",
}


# ---------------------------------------------------------------------------
# 1. R/T/A Spectrum Chart
# ---------------------------------------------------------------------------

def plot_rta_spectrum(
    wavelengths_nm: np.ndarray,
    R: np.ndarray,
    T: np.ndarray,
    A: np.ndarray,
    *,
    title: str = "光学薄膜光谱特性",
    design_type: str | None = None,
    show_legend: bool = True,
    height: int = 450,
) -> go.Figure:
    """Create an interactive R/T/A spectrum plot.

    Parameters
    ----------
    wavelengths_nm : array
        Wavelength array in nanometers.
    R, T, A : arrays
        Reflectance, transmittance, absorptance arrays.
    title : str
        Chart title.
    design_type : str, optional
        Design type label to show in subtitle.
    show_legend : bool
        Whether to show legend.
    height : int
        Chart height in pixels.

    Returns
    -------
    go.Figure
        Plotly figure object.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=wavelengths_nm, y=R,
        name="反射率 R",
        line=dict(color=COLORS["R"], width=2.5),
        hovertemplate="λ=%{x:.1f} nm<br>R=%{y:.4f}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=wavelengths_nm, y=T,
        name="透射率 T",
        line=dict(color=COLORS["T"], width=2.5),
        hovertemplate="λ=%{x:.1f} nm<br>T=%{y:.4f}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=wavelengths_nm, y=A,
        name="吸收率 A",
        line=dict(color=COLORS["A"], width=2, dash="dot"),
        hovertemplate="λ=%{x:.1f} nm<br>A=%{y:.4f}<extra></extra>",
    ))

    # Energy conservation line
    total = R + T + A
    if not np.allclose(total, 1.0, atol=0.01):
        fig.add_trace(go.Scatter(
            x=wavelengths_nm, y=total,
            name="R+T+A",
            line=dict(color="#999999", width=1, dash="dash"),
            hovertemplate="λ=%{x:.1f} nm<br>R+T+A=%{y:.4f}<extra></extra>",
        ))

    subtitle = design_type if design_type else ""

    fig.update_layout(
        title=dict(
            text=f"{title}<br><sub>{subtitle}</sub>" if subtitle else title,
            x=0.02,
            xanchor="left",
        ),
        xaxis_title="波长 (nm)",
        yaxis_title="R / T / A",
        yaxis=dict(range=[-0.02, 1.05]),
        legend=dict(
            x=0.01, y=0.99,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=COLORS["grid"],
            borderwidth=1,
        ),
        template="plotly_white",
        height=height,
        hovermode="x unified",
    )

    return fig


# ---------------------------------------------------------------------------
# 2. Layer Structure Diagram
# ---------------------------------------------------------------------------

def plot_layer_structure(
    layers: List[Dict[str, Any]],
    *,
    n_incident: float = 1.0,
    n_substrate: float = 1.52,
    title: str = "膜层结构示意图",
    height: int = 400,
) -> go.Figure:
    """Create a schematic layer structure diagram.

    Parameters
    ----------
    layers : list of dict
        Each dict has 'name', 'thickness_nm', and optionally 'n' or 'material'.
    n_incident : float
        Incident medium refractive index.
    n_substrate : float
        Substrate refractive index.
    title : str
        Chart title.
    height : int
        Chart height.

    Returns
    -------
    go.Figure
        Plotly figure with colored rectangles for each layer.
    """
    fig = go.Figure()

    # Build layer list with incident and substrate
    all_layers = [{"name": "入射介质", "thickness_nm": 0, "n": n_incident, "is_halfspace": True}]
    all_layers.extend(layers)
    all_layers.append({"name": "基底", "thickness_nm": 0, "n": n_substrate, "is_halfspace": True})

    # Calculate positions
    total_thickness = sum(float(l.get("thickness_nm", 0)) for l in layers)
    scale = max(total_thickness, 100) / 10  # Normalize to reasonable width

    x_left = 0
    colors = [COLORS["incident"], COLORS["substrate"]]
    layer_colors = [COLORS["layer_high"], COLORS["layer_low"]]

    for i, layer in enumerate(all_layers):
        if layer.get("is_halfspace"):
            # Half-space: draw wide rectangle
            width = scale * 2
            if i == 0:
                x = -width
            else:
                x = total_thickness
            color = colors[i % 2]
            fig.add_shape(
                type="rect",
                x0=x, x1=x + width,
                y0=0, y1=1,
                fillcolor=color,
                opacity=0.3,
                line=dict(width=1, color=COLORS["grid"]),
            )
            fig.add_annotation(
                x=x + width / 2, y=0.5,
                text=f"{layer['name']}<br>n={layer.get('n', '?'):.2f}",
                showarrow=False,
                font=dict(size=10, color=COLORS["text"]),
            )
        else:
            # Regular layer
            thickness = float(layer.get("thickness_nm", 0))
            n_val = layer.get("n", layer.get("n_real", 1.5))
            color = layer_colors[i % 2]

            fig.add_shape(
                type="rect",
                x0=x_left, x1=x_left + thickness,
                y0=0, y1=1,
                fillcolor=color,
                opacity=0.6,
                line=dict(width=2, color=color),
            )

            label = f"{layer['name']}<br>{thickness:.0f} nm<br>n={n_val:.2f}"
            fig.add_annotation(
                x=x_left + thickness / 2, y=0.5,
                text=label,
                showarrow=False,
                font=dict(size=10, color="white"),
            )

            x_left += thickness

    fig.update_layout(
        title=title,
        xaxis=dict(
            title="位置 (nm)",
            range=[-scale * 2.5, total_thickness + scale * 2.5],
            showgrid=False,
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            range=[-0.1, 1.1],
        ),
        template="plotly_white",
        height=height,
        plot_bgcolor=COLORS["bg"],
    )

    return fig


# ---------------------------------------------------------------------------
# 3. Angle Dependence 3D Surface
# ---------------------------------------------------------------------------

def plot_angle_wavelength_surface(
    wavelengths_nm: np.ndarray,
    angles_deg: np.ndarray,
    R_2d: np.ndarray,
    *,
    title: str = "角度-波长-反射率曲面",
    quantity: str = "R",
    height: int = 500,
) -> go.Figure:
    """Create a 3D surface plot of R/T vs angle and wavelength.

    Parameters
    ----------
    wavelengths_nm : array
        1D wavelength array.
    angles_deg : array
        1D angle array.
    R_2d : 2D array
        Shape (len(angles), len(wavelengths)).
    title : str
        Chart title.
    quantity : str
        "R", "T", or "A".
    height : int
        Chart height.

    Returns
    -------
    go.Figure
        3D surface plot.
    """
    fig = go.Figure(data=[
        go.Surface(
            x=wavelengths_nm,
            y=angles_deg,
            z=R_2d,
            colorscale="RdBu_r" if quantity == "R" else "Viridis",
            colorbar=dict(title=quantity),
        )
    ])

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="波长 (nm)",
            yaxis_title="入射角 (°)",
            zaxis_title=quantity,
        ),
        template="plotly_white",
        height=height,
    )

    return fig


# ---------------------------------------------------------------------------
# 4. Electric Field Distribution Heatmap
# ---------------------------------------------------------------------------

def plot_field_distribution(
    wavelengths_nm: np.ndarray,
    positions_nm: np.ndarray,
    field_2d: np.ndarray,
    *,
    title: str = "电场强度分布",
    quantity: str = "|E|²",
    height: int = 450,
) -> go.Figure:
    """Create a heatmap of electric field distribution.

    Parameters
    ----------
    wavelengths_nm : array
        1D wavelength array.
    positions_nm : array
        1D position array (depth into structure).
    field_2d : 2D array
        Shape (len(positions), len(wavelengths)).
    title : str
        Chart title.
    quantity : str
        Label for colorbar.
    height : int
        Chart height.

    Returns
    -------
    go.Figure
        Heatmap plot.
    """
    fig = go.Figure(data=[
        go.Heatmap(
            x=wavelengths_nm,
            y=positions_nm,
            z=field_2d,
            colorscale="Hot",
            colorbar=dict(title=quantity),
        )
    ])

    fig.update_layout(
        title=title,
        xaxis_title="波长 (nm)",
        yaxis_title="位置 (nm)",
        template="plotly_white",
        height=height,
    )

    return fig


# ---------------------------------------------------------------------------
# 5. Convergence Plot
# ---------------------------------------------------------------------------

def plot_convergence(
    orders: List[int],
    R_values: List[float],
    *,
    title: str = "RCWA 收敛性测试",
    height: int = 350,
) -> go.Figure:
    """Plot RCWA convergence with increasing number of orders.

    Parameters
    ----------
    orders : list
        Number of diffraction orders.
    R_values : list
        Zeroth-order reflectance for each order count.
    title : str
        Chart title.
    height : int
        Chart height.

    Returns
    -------
    go.Figure
        Line plot with markers.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=orders, y=R_values,
        mode="lines+markers",
        name="R₀",
        line=dict(color=COLORS["R"], width=2),
        marker=dict(size=8),
        hovertemplate="N=%{x}<br>R₀=%{y:.6f}<extra></extra>",
    ))

    # Convergence band
    if len(R_values) >= 3:
        R_final = R_values[-1]
        fig.add_hline(
            y=R_final,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"收敛值: {R_final:.6f}",
            annotation_position="bottom right",
        )

    fig.update_layout(
        title=title,
        xaxis_title="衍射阶数 N (总阶数 = 2N+1)",
        yaxis_title="零阶反射率 R₀",
        template="plotly_white",
        height=height,
    )

    return fig


# ---------------------------------------------------------------------------
# 6. Multi-design Comparison
# ---------------------------------------------------------------------------

def plot_design_comparison(
    designs: Dict[str, Dict[str, Any]],
    *,
    title: str = "多设计对比",
    quantity: str = "R",
    height: int = 450,
) -> go.Figure:
    """Compare multiple designs on the same plot.

    Parameters
    ----------
    designs : dict
        Keys are design names, values are dicts with 'wavelength_nm' and quantity.
    title : str
        Chart title.
    quantity : str
        "R", "T", or "A".
    height : int
        Chart height.

    Returns
    -------
    go.Figure
        Multi-line plot.
    """
    fig = go.Figure()

    colors = ["#c94f2d", "#0f766e", "#1d4ed8", "#b7791f", "#7c3aed", "#0891b2"]

    for i, (name, data) in enumerate(designs.items()):
        wl = data.get("wavelength_nm", data.get("wavelengths_nm", []))
        vals = data.get(quantity, data.get(f"{quantity}_values", []))
        color = colors[i % len(colors)]

        fig.add_trace(go.Scatter(
            x=wl, y=vals,
            name=name,
            line=dict(color=color, width=2),
            hovertemplate=f"{name}<br>λ=%{{x:.1f}} nm<br>{quantity}=%{{y:.4f}}<extra></extra>",
        ))

    fig.update_layout(
        title=title,
        xaxis_title="波长 (nm)",
        yaxis_title=quantity,
        yaxis=dict(range=[-0.02, 1.05]),
        legend=dict(
            x=0.01, y=0.99,
            bgcolor="rgba(255,255,255,0.8)",
        ),
        template="plotly_white",
        height=height,
        hovermode="x unified",
    )

    return fig


# ---------------------------------------------------------------------------
# 7. Metrics Dashboard
# ---------------------------------------------------------------------------

def plot_pdrc_dashboard(
    lambda_um: np.ndarray,
    R: np.ndarray,
    T: np.ndarray,
    A: np.ndarray,
    metrics: Dict[str, float],
    *,
    title: str = "PDRC 光谱仪表盘",
    height: int = 500,
) -> go.Figure:
    """Create a PDRC-specific dashboard with spectrum and metrics.

    Parameters
    ----------
    lambda_um : array
        Wavelength in micrometers.
    R, T, A : arrays
        Reflectance, transmittance, absorptance.
    metrics : dict
        Contains A_solar_avg, epsilon_8_13_avg, cooling_score.
    title : str
        Chart title.
    height : int
        Chart height.

    Returns
    -------
    go.Figure
        Subplot with spectrum and metrics annotation.
    """
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.7, 0.3],
        specs=[[{"type": "xy"}, {"type": "table"}]],
    )

    # Spectrum
    fig.add_trace(go.Scatter(
        x=lambda_um, y=R,
        name="R", line=dict(color=COLORS["R"], width=2),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=lambda_um, y=T,
        name="T", line=dict(color=COLORS["T"], width=2),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=lambda_um, y=A,
        name="A (ε)", line=dict(color=COLORS["A"], width=2, dash="dot"),
    ), row=1, col=1)

    # Highlight solar and atmospheric window bands
    fig.add_vrect(x0=0.3, x1=2.5, fillcolor="yellow", opacity=0.1,
                  line_width=0, row=1, col=1, annotation_text="太阳波段")
    fig.add_vrect(x0=8.0, x1=13.0, fillcolor="cyan", opacity=0.1,
                  line_width=0, row=1, col=1, annotation_text="大气窗口")

    # Metrics table
    fig.add_trace(go.Table(
        header=dict(
            values=["指标", "数值"],
            fill_color=COLORS["layer_low"],
            font=dict(size=12),
        ),
        cells=dict(
            values=[
                ["A_solar", "ε_8-13μm", "冷却评分"],
                [
                    f"{metrics.get('A_solar_avg', 0):.4f}",
                    f"{metrics.get('epsilon_8_13_avg', 0):.4f}",
                    f"{metrics.get('cooling_score', 0):.4f}",
                ],
            ],
            fill_color="white",
            font=dict(size=11),
        ),
    ), row=1, col=2)

    fig.update_layout(
        title=title,
        xaxis_title="波长 (μm)",
        yaxis_title="R / T / A",
        yaxis=dict(range=[-0.02, 1.05]),
        template="plotly_white",
        height=height,
        showlegend=True,
    )
    fig.update_xaxes(title_text="波长 (μm)", row=1, col=1)

    return fig
