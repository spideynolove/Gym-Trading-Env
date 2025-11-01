import numpy as np
import pandas as pd
import pyecharts.options as opts
from pyecharts.charts import Candlestick, Bar, Grid, Line
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType
def create_financial_chart(df: pd.DataFrame, lines: list=None):
    if lines is None:
        lines = []
    df = df.copy()
    line_key_prefix = 'ievi4G3vG678Vszad'
    for line in lines:
        col_name = line_key_prefix + line['name']
        df[col_name] = line['function'](df)
    df['date_str'] = df.index.strftime('%Y-%m-%d %H:%M')
    df['cumulative_rewards'] = df['reward'].cumsum()
    candle_data = df[['date_str', 'open', 'close', 'low', 'high']].to_numpy()
    x_axis_data = candle_data[:, 0].tolist()
    y_axis_candles = candle_data[:, 1:].tolist()
    layout = {'candlesticks': {'height': 35, 'top': 10}, 'randle_slider': {
        'top': 2}, 'volumes': {'height': 9, 'top': 50}, 'portfolios': {
        'height': 9, 'top': 63}, 'positions': {'height': 9, 'top': 76},
        'rewards': {'height': 9, 'top': 89}}
    for panel in layout.values():
        for key, value in list(panel.items()):
            if isinstance(value, int):
                panel[f'{key}_%'] = f'{value}%'
    candlestick_chart = Candlestick().add_xaxis(xaxis_data=x_axis_data
        ).add_yaxis(series_name='', y_axis=y_axis_candles, itemstyle_opts=
        opts.ItemStyleOpts(color='#06AF8F', color0='#FC4242', border_color=
        '#06AF8F', border_color0='#FC4242')).set_global_opts(xaxis_opts=
        opts.AxisOpts(is_scale=True, splitline_opts=opts.SplitLineOpts(
        is_show=True, linestyle_opts=opts.LineStyleOpts(color='#ffffff1f')),
        axistick_opts=opts.AxisTickOpts(linestyle_opts=opts.LineStyleOpts(
        opacity=0.3)), axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.
        LineStyleOpts(opacity=0.3)), axislabel_opts=opts.LabelOpts(color=
        'grey', position='top')), yaxis_opts=opts.AxisOpts(is_scale=True,
        splitarea_opts=opts.SplitAreaOpts(is_show=True), splitline_opts=
        opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(
        color='#ffffff1f')), axispointer_opts=opts.AxisPointerOpts(is_show=
        False), axistick_opts=opts.AxisTickOpts(linestyle_opts=opts.
        LineStyleOpts(opacity=0.3)), axisline_opts=opts.AxisLineOpts(
        linestyle_opts=opts.LineStyleOpts(opacity=0.3)), axislabel_opts=
        opts.LabelOpts(color='grey', position='top')), datazoom_opts=[opts.
        DataZoomOpts(is_show=False, type_='inside', xaxis_index=list(range(
        5)), range_start=98, range_end=100), opts.DataZoomOpts(is_show=True,
        type_='slider', xaxis_index=list(range(5)), pos_top=layout[
        'randle_slider']['top_%'], range_start=95, range_end=100)],
        legend_opts=opts.LegendOpts(is_show=False), axispointer_opts=opts.
        AxisPointerOpts(is_show=True, link=[{'xAxisIndex': list(range(5))}],
        label=opts.LabelOpts(background_color='#777', is_show=False)))
    for line in lines:
        series_name = line['name']
        y_data = line['function'](df).tolist()
        line_style = opts.LineStyleOpts(**line['line_options']
            ) if 'line_options' in line else None
        line_plot = Line().add_xaxis(xaxis_data=x_axis_data).add_yaxis(
            series_name=series_name, y_axis=y_data, itemstyle_opts=opts.
            ItemStyleOpts(opacity=0), linestyle_opts=line_style
            ).set_global_opts(xaxis_opts=opts.AxisOpts(axislabel_opts=opts.
            LabelOpts(is_show=False)))
        candlestick_chart = candlestick_chart.overlap(line_plot)
    volume_chart = Bar().add_xaxis(x_axis_data).add_yaxis(series_name=
        'Volume', y_axis=df['volume'].tolist(), xaxis_index=1, yaxis_index=
        1, label_opts=opts.LabelOpts(is_show=False), itemstyle_opts=opts.
        ItemStyleOpts(color='blue', opacity=0.3, border_color=
        '1px solid #CCCCFF')).set_global_opts(xaxis_opts=opts.AxisOpts(
        axislabel_opts=opts.LabelOpts(is_show=False), axisline_opts=opts.
        AxisLineOpts(is_show=False), axistick_opts=opts.AxisTickOpts(
        is_show=False), splitline_opts=opts.SplitLineOpts(is_show=True,
        linestyle_opts=opts.LineStyleOpts(color='#ffffff1f'))), yaxis_opts=
        opts.AxisOpts(splitline_opts=opts.SplitLineOpts(is_show=True,
        linestyle_opts=opts.LineStyleOpts(color='#ffffff1f')),
        axispointer_opts=opts.AxisPointerOpts(is_show=False), axistick_opts
        =opts.AxisTickOpts(linestyle_opts=opts.LineStyleOpts(opacity=0.3)),
        axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(
        opacity=0.3)), axislabel_opts=opts.LabelOpts(color='grey')),
        legend_opts=opts.LegendOpts(is_show=False), title_opts=opts.
        TitleOpts(is_show=True, title='Volume', pos_top=
        f"{layout['volumes']['top'] - 1}%", pos_left='50%', text_align=
        'center', title_textstyle_opts=opts.TextStyleOpts(font_size=12,
        color='#adadad', font_weight=400)))
    portfolio_chart = Line().add_xaxis(x_axis_data).add_yaxis(series_name=
        'Portfolio valuation', y_axis=df['portfolio_valuation'].tolist(),
        is_smooth=True, xaxis_index=1, yaxis_index=1, label_opts=opts.
        LabelOpts(is_show=False), linestyle_opts=opts.LineStyleOpts(color=
        'blue'), markpoint_opts=opts.MarkPointOpts(symbol_size=0),
        itemstyle_opts=opts.ItemStyleOpts(opacity=0, color='blue',
        border_color='blue')).set_global_opts(xaxis_opts=opts.AxisOpts(
        axislabel_opts=opts.LabelOpts(is_show=False), axisline_opts=opts.
        AxisLineOpts(is_show=False), axistick_opts=opts.AxisTickOpts(
        is_show=False), splitline_opts=opts.SplitLineOpts(is_show=True,
        linestyle_opts=opts.LineStyleOpts(color='#ffffff1f'))), yaxis_opts=
        opts.AxisOpts(splitline_opts=opts.SplitLineOpts(is_show=True,
        linestyle_opts=opts.LineStyleOpts(color='#ffffff1f')),
        axispointer_opts=opts.AxisPointerOpts(is_show=False), axistick_opts
        =opts.AxisTickOpts(linestyle_opts=opts.LineStyleOpts(opacity=0.3)),
        axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(
        opacity=0.3)), axislabel_opts=opts.LabelOpts(color='grey')),
        legend_opts=opts.LegendOpts(is_show=False), title_opts=opts.
        TitleOpts(is_show=True, title='Portfolio value', pos_top=
        f"{layout['portfolios']['top'] - 3}%", pos_left='50%', text_align=
        'center', title_textstyle_opts=opts.TextStyleOpts(font_size='14px',
        color='#adadad', font_weight='400')))
    positions_chart = Line().add_xaxis(x_axis_data).add_yaxis(series_name=
        'Positions', y_axis=df['position'].tolist(), is_step=True,
        label_opts=opts.LabelOpts(is_show=False), linestyle_opts=opts.
        LineStyleOpts(color='blue'), itemstyle_opts=opts.ItemStyleOpts(
        opacity=0, color='blue', border_color='blue')).set_series_opts(
        areastyle_opts=opts.AreaStyleOpts(opacity=0.2, color='blue')
        ).set_global_opts(xaxis_opts=opts.AxisOpts(axislabel_opts=opts.
        LabelOpts(is_show=False), axisline_opts=opts.AxisLineOpts(is_show=
        False), axistick_opts=opts.AxisTickOpts(is_show=False),
        splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts
        .LineStyleOpts(color='#ffffff1f'))), yaxis_opts=opts.AxisOpts(
        splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts
        .LineStyleOpts(color='#ffffff1f')), axispointer_opts=opts.
        AxisPointerOpts(is_show=False), axistick_opts=opts.AxisTickOpts(
        linestyle_opts=opts.LineStyleOpts(opacity=0.3)), axisline_opts=opts
        .AxisLineOpts(linestyle_opts=opts.LineStyleOpts(opacity=0.3)),
        axislabel_opts=opts.LabelOpts(color='grey')), legend_opts=opts.
        LegendOpts(is_show=False), title_opts=opts.TitleOpts(is_show=True,
        title='Positions', pos_top=f"{layout['positions']['top'] - 3}%",
        pos_left='50%', text_align='center', title_textstyle_opts=opts.
        TextStyleOpts(font_size='14px', color='#adadad', font_weight='400')))
    rewards_chart = Line().add_xaxis(x_axis_data).add_yaxis(series_name=
        'Cumulative Rewards', y_axis=df['cumulative_rewards'].tolist(),
        is_smooth=True, xaxis_index=1, yaxis_index=1, label_opts=opts.
        LabelOpts(is_show=False), linestyle_opts=opts.LineStyleOpts(color=
        'blue'), markpoint_opts=opts.MarkPointOpts(symbol_size=0),
        itemstyle_opts=opts.ItemStyleOpts(opacity=0, color='blue',
        border_color='blue')).set_series_opts(areastyle_opts=opts.
        AreaStyleOpts(opacity=0.3, color='blue')).set_global_opts(xaxis_opts
        =opts.AxisOpts(axislabel_opts=opts.LabelOpts(is_show=False),
        axisline_opts=opts.AxisLineOpts(is_show=False), axistick_opts=opts.
        AxisTickOpts(is_show=False), splitline_opts=opts.SplitLineOpts(
        is_show=True, linestyle_opts=opts.LineStyleOpts(color='#ffffff1f'))
        ), yaxis_opts=opts.AxisOpts(splitline_opts=opts.SplitLineOpts(
        is_show=True, linestyle_opts=opts.LineStyleOpts(color='#ffffff1f')),
        axispointer_opts=opts.AxisPointerOpts(is_show=False), axistick_opts
        =opts.AxisTickOpts(linestyle_opts=opts.LineStyleOpts(opacity=0.3)),
        axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(
        opacity=0.3)), axislabel_opts=opts.LabelOpts(color='grey')),
        legend_opts=opts.LegendOpts(is_show=False), title_opts=opts.
        TitleOpts(is_show=True, title='Cumulative Rewards', pos_top=
        f"{layout['rewards']['top'] - 3}%", pos_left='50%', text_align=
        'center', title_textstyle_opts=opts.TextStyleOpts(font_size='14px',
        color='#adadad', font_weight='400')))
    grid_chart = Grid(init_opts=opts.InitOpts(width='800px', height='650px',
        animation_opts=opts.AnimationOpts(animation=False), bg_color=
        'white', is_horizontal_center=True))
    grid_chart.add(candlestick_chart, grid_opts=opts.GridOpts(pos_left=
        '10%', pos_right='8%', pos_top=layout['candlesticks']['top_%'],
        height=layout['candlesticks']['height_%']))
    grid_chart.add(volume_chart, grid_opts=opts.GridOpts(pos_left='10%',
        pos_right='8%', pos_top=layout['volumes']['top_%'], height=layout[
        'volumes']['height_%']))
    grid_chart.add(portfolio_chart, grid_opts=opts.GridOpts(pos_left='10%',
        pos_right='8%', pos_top=layout['portfolios']['top_%'], height=
        layout['portfolios']['height_%']))
    grid_chart.add(positions_chart, grid_opts=opts.GridOpts(pos_left='10%',
        pos_right='8%', pos_top=layout['positions']['top_%'], height=layout
        ['positions']['height_%']))
    grid_chart.add(rewards_chart, grid_opts=opts.GridOpts(pos_left='10%',
        pos_right='8%', pos_top=layout['rewards']['top_%'], height=layout[
        'rewards']['height_%']))
    return grid_chart