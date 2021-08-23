from bokeh.plotting import figure, show, output_notebook
from bokeh.models import Slider, CheckboxGroup, CustomJS, ColumnDataSource, CDSView, HoverTool, Label, LabelSet, LinearColorMapper, ColorBar
from bokeh.models.filters import CustomJSFilter
from bokeh.layouts import row
from bokeh.transform import factor_cmap
from bokeh.palettes import Category10_10
from bokeh.embed import components
from bokeh.resources import INLINE

import matplotlib.pylab as pl
import matplotlib

import pandas as pd
import numpy as np
import geopandas as gpd
from app.models import User, Stake, Entry

def getPolyCoords(row, geom, coord_type):
    """Returns the coordinates ('x|y') of edges/vertices of a Polygon/others"""

    # Parse the geometries and grab the coordinate
    geometry = row[geom]
    #print(geometry.type)

    if geometry.type=='Polygon':
        if coord_type == 'x':
            # Get the x coordinates of the exterior
            # Interior is more complex: xxx.interiors[0].coords.xy[0]
            return list( geometry.exterior.coords.xy[0] )
        elif coord_type == 'y':
            # Get the y coordinates of the exterior
            return list( geometry.exterior.coords.xy[1] )

    if geometry.type in ['Point', 'LineString']:
        if coord_type == 'x':
            return list( geometry.xy[0] )
        elif coord_type == 'y':
            return list( geometry.xy[1] )

    if geometry.type=='MultiLineString':
        all_xy = []
        for ea in geometry:
            if coord_type == 'x':
                all_xy.append(list( ea.xy[0] ))
            elif coord_type == 'y':
                all_xy.append(list( ea.xy[1] ))
        return all_xy

    if geometry.type=='MultiPolygon':
        all_xy = []
        for ea in geometry:
            if coord_type == 'x':
                all_xy.append(list( ea.exterior.coords.xy[0] ))
            elif coord_type == 'y':
                all_xy.append(list( ea.exterior.coords.xy[1] ))
        return all_xy

    else:
        # Finally, return empty list for unknown geometries
        return []


def getsource():
    data = Entry.query.all()
    outputdf = pd.DataFrame([(d.stake_id, d.date, d.FE, d.FE_new, d.comment,
                            d.abl_since_last, d.abl_since_oct) for d in data],
                            columns=['stake_id', 'date', 'FE', 'FE_new', 'comment',
                            'abl_since_last', 'abl_since_oct'])
    return (outputdf)


def mapplot():
    # File path glacier boundary
    bound_fp = '/Users/leahartl/Desktop/Jam2021/App3/Jamtalferner_GI5.shp'
    bound = gpd.read_file(bound_fp).explode()

    df_bound = pd.DataFrame(columns=['x', 'y'])

    df_bound['x'] = bound.apply(getPolyCoords, geom='geometry', coord_type='x', axis=1)
    df_bound['y'] = bound.apply(getPolyCoords, geom='geometry', coord_type='y', axis=1)
    bsource = ColumnDataSource(df_bound)

    # get stake locations
    stk = Stake.query.all()
    xc = []
    yc = []
    stake_id = []
    abl_since_drilled = []
    drilldate = []
    df = pd.DataFrame(columns=['xc', 'yc', 'stake_id', 'abl_since_drilled', 'drilldate'])
    for s in stk:
        xc.append(s.x)
        yc.append(s.y)
        stake_id.append(s.stake_id)
        abl_since_drilled.append(s.abl_since_drilled)
        drilldate.append(s.drilldate)

    df['xc'] = xc
    df['yc'] = yc
    df['stake_id'] = stake_id
    df['abl_since_drilled'] = abl_since_drilled
    df['drilldate'] = drilldate

    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.xc, df.yc))
    gdf.crs = 'EPSG:4326'

    CRS = bound.crs

    gdf['geometry'] = gdf['geometry'].to_crs(crs=CRS)

    # p_df = pd.DataFrame(columns=['x', 'y', 'stake_id'])
    gdf['x'] = gdf.apply(getPolyCoords, geom='geometry', coord_type='x', axis=1)
    gdf['y'] = gdf.apply(getPolyCoords, geom='geometry', coord_type='y', axis=1)

    gdf['x'] = [v[0] for v in gdf['x'].values]
    gdf['y'] = [v[0] for v in gdf['y'].values]

    # Make a copy, drop the geometry column and create ColumnDataSource
    p_df = gdf.drop('geometry', axis=1).copy()
    psource = ColumnDataSource(p_df)

    fig = figure(title="Pegelplan (Farbskala: Ablation seit Bohrung in cm Eis)", plot_width=800, plot_height=600)#, x_axis_type="mercator", y_axis_type="mercator",)

    # Plot boundary
    glacier = fig.patches('x', 'y', source=bsource,
                fill_alpha=0, line_color="black", line_width=1)
    # Plot points
    color_mapper = LinearColorMapper(palette='Magma256', low=0, high=800)
    points = fig.circle('x', 'y', source=psource, color={'field': 'abl_since_drilled', 'transform': color_mapper}, size=8)

    labels = LabelSet(x='x', y='y', text='stake_id',
                      source=psource, render_mode='canvas', text_font_size='10pt',
                      x_offset=2, y_offset=-18,
                      background_fill_color='white', background_fill_alpha=0.6)

    # there is no built in function for a color bar label...
    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12)
    hover = HoverTool(tooltips=[('Pegel', '@stake_id'), ('Bohrdatum', '@drilldate{%F}'),
                                ('Ablation seit Bohrung', '@abl_since_drilled')],
                      formatters={"@drilldate": "datetime"}, renderers=[points])
    fig.add_tools(hover)

    fig.add_layout(color_bar, 'right')
    fig.add_layout(labels)

    layout = row(fig)

    return(layout)


def pointplot():
    df = getsource()
    df['color'] = ''

    # works more or less but sorting does not do what i want it to.
    checks = df['stake_id'].drop_duplicates().sort_values().tolist()
    n = len(checks)
    colors = pl.cm.nipy_spectral(np.linspace(0, 1, n))

    for i, c in enumerate(checks):
        df.loc[df['stake_id'] == c, 'color'] = matplotlib.colors.to_hex(colors[i])

    source = ColumnDataSource(df)
    checkboxes = CheckboxGroup(labels=checks, active=[])#list(range(len(checks))))

    fig = figure(plot_height=600, plot_width=720,
                 x_axis_type='datetime')

    hover = HoverTool(tooltips=[("Ablation seit Herbst (cm Eis)", "@abl_since_oct"), ("Datum", "@date{%F}"), ("Pegel", "@stake_id")],
                      formatters={"@date": "datetime"})
    fig.add_tools(hover)

    filter = CustomJSFilter(code="""
    let selected = checkboxes.active.map(i=>checkboxes.labels[i]);
    let indices = [];
    let column = source.data['stake_id'];
    for(let i=0; i<column.length; i++){
        if(selected.includes(column[i])){
            indices.push(i);
            }
        }
    return indices;
    """, args=dict(checkboxes=checkboxes))

    checkboxes.js_on_change("active", CustomJS(code="source.change.emit();", args=dict(source=source)))

    # fig.line(x="date", y="abl_since_oct", source=source, line_width=2,  view=CDSView(source=source, filters=[filter]))
    p = fig.circle(x="date", y="abl_since_oct", source=source, view=CDSView(source=source, filters=[filter]), size=5, fill_color='color', line_color=None )

    layout = row(checkboxes, fig)
    return (layout)



