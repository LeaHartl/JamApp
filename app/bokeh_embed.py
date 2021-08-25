from bokeh.plotting import figure, show, output_notebook
from bokeh.models import Scatter, Legend, LegendItem, CheckboxGroup, CheckboxButtonGroup, CustomJS, ColumnDataSource, CDSView, HoverTool, Label, LabelSet, LinearColorMapper, ColorBar
from bokeh.models.filters import CustomJSFilter
from bokeh.layouts import row, column
from bokeh.transform import factor_cmap
from bokeh.palettes import Category10_10
from bokeh.embed import components
from bokeh.resources import INLINE
from bokeh.core.enums import MarkerType
# from bokeh.charts import Scatter

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
    outputdf = pd.DataFrame([(d.id, d.stake_id, d.date, d.FE, d.FE_new, d.comment,
                            d.abl_since_last, d.abl_since_oct) for d in data],
                            columns=['id', 'stake_id', 'date', 'FE', 'FE_new', 'comment',
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
    print(df)
    # works more or less but sorting does not do what i want it to.
    checks = df['stake_id'].drop_duplicates().sort_values().tolist()
    n = len(checks)
    colors = pl.cm.nipy_spectral(np.linspace(0, 1, n))

    for i, c in enumerate(checks):
        df.loc[df['stake_id'] == c, 'color'] = matplotlib.colors.to_hex(colors[i])

    source = ColumnDataSource(df)
    act=[0, 21]
    checkboxes = CheckboxGroup(labels=checks, active=act)#list(range(len(checks))))

    lbls = pd.DataFrame(columns=['x', 'y', 'stake_id', 'color'])
    lbls.stake_id = checks
    lbls['txt'] = ['P'+c for c in checks]
    lbls.y = [500-v*10 for v in range(len(checks))]

    lbls.x = 20

    for i, c in enumerate(checks):
        lbls.loc[lbls['stake_id'] == c, 'color'] = matplotlib.colors.to_hex(colors[i])


    lsource = ColumnDataSource(lbls.iloc[act])

    fig = figure(plot_height=600, plot_width=720,
                 x_axis_label='Datum', y_axis_label='Ablation (cm Eis)',
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


    code = """

    let selected = checkboxes.active.map(i=>checkboxes.labels[i]);

    var y = []
    var x = []
    var color = []
    var ix = []
    var id = []
    var txt = []

    for(let i=0;i<checks.length; i++){
    //console.log(i)
        if(selected.includes(checks[i])){
            //console.log(selected.includes(checks[i]))
            //console.log(checks[i])
            //console.log(dx[i])

                    //y.push(dy[i]);
                    y.push(500-i*10);
                    x.push(dx[i]);
                    color.push(dc[i]);
                    ix.push(di[i]);
                    id.push(checks[i]);
                    txt.push(dt[i]);
                    //inds.push[i]
            }

    }


    source.data['y']=y//.sort();
    source.data['x']=x;
    source.data['color']=color;
    source.data['txt']=txt;
    source.data.index=ix;
    source.data['stake_id']=id;
    //console.log(source.data)
    source.change.emit();
    """

    # use this if not trying to change label text.
    checkboxes.js_on_change("active", CustomJS(code="source.change.emit();", args=dict(source=source)))
    checkboxes.js_on_change("active", CustomJS(code=code, args=dict(source=lsource, 
        checkboxes=checkboxes, checks=checks, dx=lbls['x'].values, dy=lbls['y'].values, 
        dc=lbls['color'].values, dt=lbls['txt'].values, di=lbls.index.values)))

    # print(lsource.data)

    labels = LabelSet(x='x', y='y', x_units='screen', y_units='screen',
                      text='txt',
                      source=lsource,
                      render_mode='canvas', text_font_size='10pt',
                      #x_offset=2, y_offset=-18,
                      background_fill_color='color', background_fill_alpha=0.4)

    p = fig.circle(x="date", y="abl_since_oct", source=source,
                   view=CDSView(source=source, filters=[filter]),
                   size=10, fill_color='color', line_color=None,)
                   #legend_group='stake_id')




    # fig.add_layout(legend)
    fig.add_layout(labels)
    layout = row(checkboxes, fig)
    return (layout)


def pointplotbyyear():
    df = getsource()
    df['color'] = ''

    # works more or less but sorting does not do what i want it to.
    checks = df['stake_id'].drop_duplicates().sort_values().tolist()
    yrs = df['date'].dt.year.drop_duplicates().sort_values().astype(str).tolist()
    print(min(yrs))
    n = len(checks)
    colors = pl.cm.nipy_spectral(np.linspace(0, 1, n))
    colors_yr = pl.cm.Accent(np.linspace(0, 1, len(yrs)))

    # markers = list(MarkerType)
    # markers = markers[0:len(yrs)+1]
    markers = ['diamond', 'square', 'circle', 'triangle']

    for i, c in enumerate(checks):
        df.loc[df['stake_id'] == c, 'color'] = matplotlib.colors.to_hex(colors[i])

    df2 = df.copy()

    new_range = pd.date_range(start=min(yrs)+'-05-01', end=max(yrs)+'-10-31', freq='D' )
    dic = {}
    df3=pd.DataFrame()

    ##resample maybe not needed, can be shortened.
    for c in checks:
        dic[c] = df2.loc[df['stake_id']==c]
        dic[c].set_index('date', inplace=True)
        dic[c].sort_index(inplace=True)
        dic[c] = dic[c].resample('D').asfreq().reindex(new_range)
        dic[c] = dic[c].loc[(dic[c].index.month >= 5) & (dic[c].index.month <= 10)]
        dic[c] = dic[c][['stake_id', 'abl_since_oct', 'color']]
        dic[c]['stake_id'] = c
        dic[c]['year'] = dic[c].index.year.astype(str)
        dic[c]['month'] = dic[c].index.month.astype(str)
        dic[c]['day'] = dic[c].index.day.astype(str)
        dic[c]['doy'] = dic[c].index.dayofyear
        dic[c]['dummydate'] = '2020-'+dic[c]['month']+'-'+dic[c]['day']
        dic[c]['dummydate'] = pd.to_datetime(dic[c]['dummydate'])
        dic[c]['date'] = dic[c].index
        dic[c].drop(['day', 'month'], axis=1, inplace=True)

        df3 = pd.concat([df3, dic[c]])
        #dic[c] = dic[c].set_index(['year', 'date']).abl_since_oct.unstack(-2) #(reshape...)
    df3['color_y'] = '-'
    for i, y in enumerate(yrs):
        df3.loc[df3['year'] == y, 'color_y'] = matplotlib.colors.to_hex(colors_yr[i])
        df3.loc[df3['year'] == y, 'markers'] = markers[i]

    # print(df3)
    # print(df3.markers.unique())
    source = ColumnDataSource(df3)
    checkboxes = CheckboxGroup(labels=checks, active=[0, 21])#list(range(len(checks))))
    checkbox_b = CheckboxButtonGroup(labels=yrs, active=list(range(len(yrs))))

    fig = figure(plot_height=600, plot_width=720,
                 x_axis_type='datetime', y_axis_label='Ablation (cm Eis)',
                 x_axis_label='Datum')

    hover = HoverTool(tooltips=[("Datum", "@date{%F}")],
                      formatters={"@date": "datetime"})
    fig.add_tools(hover)

    filter1 = CustomJSFilter(code="""
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

    filter2 = CustomJSFilter(code="""
    let selected2 = checkbox_b.active.map(i=>checkbox_b.labels[i]);
    let indices2 = [];
    let column2 = source.data['year'];
    for(let i=0; i<column2.length; i++){
        if(selected2.includes(column2[i])){
            indices2.push(i);
            }
        }
    return indices2;
    """, args=dict(checkbox_b=checkbox_b))

    text = 'test'
    citation = Label(x=70, y=70, x_units='screen', y_units='screen',
                 text=text, render_mode='css', 
                 border_line_color='black', border_line_alpha=1.0,
                 background_fill_color='white', background_fill_alpha=1.0)

    checkboxes.js_on_change("active", CustomJS(code="source.change.emit();", args=dict(source=source)))
    checkbox_b.js_on_change("active", CustomJS(code="source.change.emit();", args=dict(source=source)))
    

    p = fig.scatter(x="dummydate", y="abl_since_oct", marker='markers', source=source, 
                    view=CDSView(source=source, filters=[filter1, filter2]), size=10, fill_color='color', 
                    line_color=None)#, legend_field='year')#legend_group="year")



    layout = row(column(checkbox_b, checkboxes), fig)#, sizing_mode="stretch_both")
    return (layout)

