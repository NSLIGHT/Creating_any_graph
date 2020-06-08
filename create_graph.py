import dash
import dash_core_components as dcc
import dash_html_components as html
from pymongo import MongoClient
import plotly.graph_objs as go
import plotly.io as pio
import json
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import re
from fstring import fstring
import plotly.express as px


class creating_graph(object):
    def __init__(self,
                 db_name,
                 collection_name,
                 chart_type,
                 columns,
                 title="Untitled",
                 limit=None):
        self.client = MongoClient('localhost', 27017)

        self.dbname = db_name
        self.clname = collection_name
        self.ctype = chart_type
        self.columns = columns
        self.limit = limit
        self.title = title

        self.express_related = [
            "scatter", "scatter_3d", "scatter_polar", "scatter_ternary",
            "scatter_mapbox", "scatter_geo", "line", "line_3d", "line_polar",
            "line_ternary", "line_mapbox", "line_geo", "area", "bar",
            "bar_polar", "violin", "box", "strip", "histogram", "pie",
            "treemap", "sunburst", "funnel", "funnel_area", "scatter_matrix",
            "parallel_coordinates", "parallel_categories", "choropleth",
            "choropleth_mapbox", "density_contour", "density_heatmap",
            "density_mapbox", "imshow"
        ]

    def graph_data(self,
                   chartType,
                   fig_class,
                   df_data,
                   x=None,
                   y=None,
                   z=None,
                   lat=None,
                   lon=None,
                   orientation=None,
                   barmode=None,
                   size=None,
                   color=None,
                   names=None,
                   values=None,
                   hole=None):
        dataframe = df_data
        if x:
            dataframe = df_data[[x]]
        if y:
            dataframe = df_data[[y]]
        if x and y:
            dataframe = df_data[[x, y]]
        if z and (isinstance(z, str)):
            z = df_data[z]
            fig = fig_class(dataframe, x, y)
            return fig
        if chartType == "bar":
            fig = fig_class(dataframe,
                            x=x,
                            y=y,
                            barmode=barmode,
                            orientation=orientation)
        elif chartType == "scatter":
            if bool(re.search(r"bubble|dot", self.ctype)):
                fig = fig_class(dataframe, x=x, y=y,size=size)
            else:
                fig = fig_class(dataframe, x=x, y=y)
            
        elif chartType == "pie":
            fig = fig_class(dataframe, names=names, values=values, hole=hole)
        elif chartType == "density_mapbox":
            fig = fig_class(dataframe,
                            lat="charges",
                            lon="bmi",
                            z="sex",
                            mapbox_style="white-bg")
        else:
            fig = fig_class(dataframe, x, y)
        return fig

    def create_data_graph(self, data):
        chartType = self.ctype
        barmode = ""
        orientation = self.columns.get("orientation", "")
        size = []
        color = ""
        hole = 0
        names = self.columns.get("names")
        values = self.columns.get("values")
        if isinstance(self.columns.get("names"), (str)):
            names = list(pd.DataFrame(data)[self.columns.get("names")].values)
            values = list(
                pd.DataFrame(data)[self.columns.get("values")].values)
        if bool(re.search(r"bar|stack|group|horizon", self.ctype)):
            chartType = "bar"
            barmode = "relative"
            orientation = "v"
            if bool(re.search(r"stack", self.ctype)):
                barmode = "overlay"
            if bool(re.search(r"group", self.ctype)):
                barmode = "group"
            if bool(re.search(r"horizon", self.ctype)):
                orientation = "h"

        if bool(re.search(r"scatter|bubble|dot", self.ctype)):
            chartType = "scatter"
            size = 1
            color = "blue"
            if bool(re.search(r"bubble|dot", self.ctype)):
                size = self.columns.get("size",self.columns.get("y"))
        if bool(re.search(r"pie|donut", self.ctype)):
            chartType = "pie"
            hole = 0
            if bool(re.search(r"donut", self.ctype)):
                hole = self.columns.get("hole", 0.5)

        if chartType in self.express_related:
            fig_class = getattr(px, chartType.lower())
            fig = self.graph_data(chartType,
                                  fig_class,
                                  pd.DataFrame(data),
                                  self.columns.get("x"),
                                  self.columns.get("y"),
                                  self.columns.get("z"),
                                  lon=self.columns.get("lon"),
                                  lat=self.columns.get("lat"),
                                  barmode=barmode,
                                  orientation=orientation,
                                  size=size,
                                  color=color,
                                  names=names,
                                  values=values,
                                  hole=hole)
            fig = go.Figure(data=fig)
            fig.update_layout(
                title={
                    "text":
                    self.title +
                    "<i> (If you didn't get any graph check the parameters)</i>"
                })
            return fig

    def create(self):
        db = self.client[self.dbname]
        if self.limit:
            data = db[self.clname].find().limit(self.limit)
        else:
            data = db[self.clname].find()
        try:
            fig = self.create_data_graph(data=list(data))
            app = dash.Dash()
            app.layout = html.Div([dcc.Graph(figure=fig)])
        except Exception as e:
            print(e)
        finally:
            app.run_server(debug=True, use_reloader=True)


c1 = creating_graph(db_name="insurance",
                    collection_name="medical",
                    chart_type="bubble",
                    columns={
                        "x": "bmi",
                        "y": "charges"
                    },
                    limit=10)

c1.create()