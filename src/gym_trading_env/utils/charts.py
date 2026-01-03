from __future__ import annotations

from typing import List

import pandas as pd
import pyecharts.options as opts
from pyecharts.charts import Bar, Candlestick, Grid, Line


def create_candlestick_chart(df: pd.DataFrame, x_axis_data: List[str]) -> Candlestick:
    return (
        Candlestick()
        .add_xaxis(xaxis_data=x_axis_data)
        .add_yaxis(
            series_name="",
            y_axis=df[["open", "close", "low", "high"]].values.tolist(),
            itemstyle_opts=opts.ItemStyleOpts(
                color="#06AF8F",
                color0="#FC4242",
                border_color="#06AF8F",
                border_color0="#FC4242",
            ),
        )
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitline_opts=opts.SplitLineOpts(
                    is_show=True, linestyle_opts=opts.LineStyleOpts(color="#ffffff1f")
                ),
                axistick_opts=opts.AxisTickOpts(
                    linestyle_opts=opts.LineStyleOpts(opacity=0.3)
                ),
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(opacity=0.3)
                ),
                axislabel_opts=opts.LabelOpts(color="grey", position="top"),
            ),
            yaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitarea_opts=opts.SplitAreaOpts(is_show=True),
                splitline_opts=opts.SplitLineOpts(
                    is_show=True, linestyle_opts=opts.LineStyleOpts(color="#ffffff1f")
                ),
                axispointer_opts=opts.AxisPointerOpts(is_show=False),
                axistick_opts=opts.AxisTickOpts(
                    linestyle_opts=opts.LineStyleOpts(opacity=0.3)
                ),
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(opacity=0.3)
                ),
                axislabel_opts=opts.LabelOpts(color="grey", position="top"),
            ),
            datazoom_opts=[
                opts.DataZoomOpts(
                    is_show=False,
                    type_="inside",
                    xaxis_index=list(range(5)),
                    range_start=98,
                    range_end=100,
                ),
                opts.DataZoomOpts(
                    is_show=True,
                    type_="slider",
                    xaxis_index=list(range(5)),
                    pos_top="2%",
                    range_start=95,
                    range_end=100,
                ),
            ],
            legend_opts=opts.LegendOpts(is_show=False),
            axispointer_opts=opts.AxisPointerOpts(
                is_show=True,
                link=[{"xAxisIndex": list(range(5))}],
                label=opts.LabelOpts(background_color="#777", is_show=False),
            ),
        )
    )


def create_volume_chart(df: pd.DataFrame, x_axis_data: List[str], top: str) -> Bar:
    return (
        Bar()
        .add_xaxis(x_axis_data)
        .add_yaxis(
            series_name="Volume",
            y_axis=df["volume"].tolist(),
            xaxis_index=1,
            yaxis_index=1,
            label_opts=opts.LabelOpts(is_show=False),
            itemstyle_opts=opts.ItemStyleOpts(
                color="blue", opacity=0.3, border_color="1px solid #CCCCFF"
            ),
        )
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(is_show=False),
                axisline_opts=opts.AxisLineOpts(is_show=False),
                axistick_opts=opts.AxisTickOpts(is_show=False),
                splitline_opts=opts.SplitLineOpts(
                    is_show=True, linestyle_opts=opts.LineStyleOpts(color="#ffffff1f")
                ),
            ),
            yaxis_opts=opts.AxisOpts(
                splitline_opts=opts.SplitLineOpts(
                    is_show=True, linestyle_opts=opts.LineStyleOpts(color="#ffffff1f")
                ),
                axispointer_opts=opts.AxisPointerOpts(is_show=False),
                axistick_opts=opts.AxisTickOpts(
                    linestyle_opts=opts.LineStyleOpts(opacity=0.3)
                ),
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(opacity=0.3)
                ),
                axislabel_opts=opts.LabelOpts(color="grey"),
            ),
            legend_opts=opts.LegendOpts(is_show=False),
            title_opts=opts.TitleOpts(
                is_show=True,
                title="Volume",
                pos_top=f"{int(top[:-1]) - 1}%",
                pos_left="50%",
                text_align="center",
                title_textstyle_opts=opts.TextStyleOpts(
                    font_size=12, color="#adadad", font_weight=400
                ),
            ),
        )
    )


def create_line_chart(
    df: pd.DataFrame,
    x_axis_data: List[str],
    y_col: str,
    title: str,
    top: str,
    is_step: bool = False,
) -> Line:
    chart = (
        Line()
        .add_xaxis(x_axis_data)
        .add_yaxis(
            series_name=title,
            y_axis=df[y_col].tolist(),
            is_smooth="smooth",
            is_step=is_step,
            label_opts=opts.LabelOpts(is_show=False),
            linestyle_opts=opts.LineStyleOpts(color="blue"),
            itemstyle_opts=opts.ItemStyleOpts(opacity=0, color="blue", border_color="blue"),
        )
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(is_show=False),
                axisline_opts=opts.AxisLineOpts(is_show=False),
                axistick_opts=opts.AxisTickOpts(is_show=False),
                splitline_opts=opts.SplitLineOpts(
                    is_show=True, linestyle_opts=opts.LineStyleOpts(color="#ffffff1f")
                ),
            ),
            yaxis_opts=opts.AxisOpts(
                splitline_opts=opts.SplitLineOpts(
                    is_show=True, linestyle_opts=opts.LineStyleOpts(color="#ffffff1f")
                ),
                axispointer_opts=opts.AxisPointerOpts(is_show=False),
                axistick_opts=opts.AxisTickOpts(
                    linestyle_opts=opts.LineStyleOpts(opacity=0.3)
                ),
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(opacity=0.3)
                ),
                axislabel_opts=opts.LabelOpts(color="grey"),
            ),
            legend_opts=opts.LegendOpts(is_show=False),
            title_opts=opts.TitleOpts(
                is_show=True,
                title=title,
                pos_top=f"{int(top[:-1]) - 3}%",
                pos_left="50%",
                text_align="center",
                title_textstyle_opts=opts.TextStyleOpts(
                    font_size="14px", color="#adadad", font_weight="400"
                ),
            ),
        )
    )
    if is_step:
        chart.set_series_opts(areastyle_opts=opts.AreaStyleOpts(opacity=0.2, color="blue"))
    return chart


def create_financial_chart(df: pd.DataFrame, lines: List[dict] | None = None) -> Grid:
    lines = lines or []
    df = df.copy()
    df["date_str"] = df.index.strftime("%Y-%m-%d %H:%M")
    df["cumulative_rewards"] = df["reward"].cumsum()
    x_axis_data = df["date_str"].tolist()

    layout = {
        "candlesticks": {"height": "35%", "top": "10%"},
        "volumes": {"height": "9%", "top": "50%"},
        "portfolios": {"height": "9%", "top": "63%"},
        "positions": {"height": "9%", "top": "76%"},
        "rewards": {"height": "9%", "top": "89%"},
    }

    candlestick_chart = create_candlestick_chart(df, x_axis_data)
    for line_opts in lines:
        line_plot = (
            Line()
            .add_xaxis(xaxis_data=x_axis_data)
            .add_yaxis(
                series_name=line_opts["name"],
                y_axis=line_opts["function"](df).tolist(),
                itemstyle_opts=opts.ItemStyleOpts(opacity=0),
                linestyle_opts=opts.LineStyleOpts(**line_opts.get("line_options", {})),
            )
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(is_show=False))
            )
        )
        candlestick_chart = candlestick_chart.overlap(line_plot)

    volume_chart = create_volume_chart(df, x_axis_data, layout["volumes"]["top"])
    portfolio_chart = create_line_chart(
        df, x_axis_data, "portfolio_valuation", "Portfolio value", layout["portfolios"]["top"]
    )
    positions_chart = create_line_chart(
        df, x_axis_data, "position", "Positions", layout["positions"]["top"], is_step=True
    )
    rewards_chart = create_line_chart(
        df, x_axis_data, "cumulative_rewards", "Cumulative Rewards", layout["rewards"]["top"]
    )

    grid_chart = Grid(
        init_opts=opts.InitOpts(
            width="800px",
            height="650px",
            animation_opts=opts.AnimationOpts(animation=False),
            bg_color="white",
            is_horizontal_center=True,
        )
    )

    charts = {
        candlestick_chart: "candlesticks",
        volume_chart: "volumes",
        portfolio_chart: "portfolios",
        positions_chart: "positions",
        rewards_chart: "rewards",
    }

    for chart, name in charts.items():
        grid_chart.add(
            chart,
            grid_opts=opts.GridOpts(
                pos_left="10%",
                pos_right="8%",
                pos_top=layout[name]["top"],
                height=layout[name]["height"],
            ),
        )

    return grid_chart
