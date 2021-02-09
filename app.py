import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px
import dill
import pandas as pd
import numpy as np
from datetime import date, timedelta

group_colors = {"control": "light blue", "reference": "red"}

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
server = app.server

data = dill.load(open('data.dill', 'rb'))
tracts = dill.load(open('austin.json', 'rb'))
tract_list = pd.DataFrame({'tract': data.GeoID.sort_values(ascending = True).unique()})

# App Layout
app.layout = html.Div(
    children=[
        # Top Banner
        html.Div(
            className="study-browser-banner row",
            children=[
                html.H2(className="h2-title", children="E-Scooter Sharing Trip Predictor - Austin, Texas"),
                html.Div(
                    className="div-logo",
                    children=html.Img(
                        className="logo", src=app.get_asset_url("tdi-logo.png")
                    ),
                ),
            ],
        ),
        # Body of the App
        html.Div(
            className="row app-body",
            children=[
                # User Controls
                html.Div(
                    className="four columns card",
                    children=[
                        html.Div(
                            className="bg-white user-control",
                            children=[
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.H6("Date"),
                                        dcc.DatePickerSingle(
                                            id='date_picker',
                                            date=date.today(),
                                            min_date_allowed=date(2018, 4, 3),
                                            max_date_allowed=(date.today()+timedelta(6))
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.H6("Trip direction"),
                                        dcc.Dropdown(id="direction",
                                            options=[
                                                {'label': 'Outgoing trips', 'value': 'Starts'},
                                                {'label': 'Incoming trips', 'value': 'Ends'}
                                            ],
                                            value='Starts'
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.H6("Day split"),
                                        dcc.Dropdown(id="AMPM",
                                            options=[
                                                {'label': 'AM', 'value': 'AM'},
                                                {'label': 'PM', 'value': 'PM'}
                                            ],
                                            value='AM'
                                        ),
                                    ],
                                ),
                                html.Br(),
                                html.Br(),
                                html.Br(),
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.H6("Created by OR CASPI"),
                                        html.H6("orcaspi@gmail.com")
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                # Graph
                html.Div(
                    className="eight columns card-left",
                    children=[
                        html.Div(
                            className="bg-white",
                            children=[
                                html.H5("E-Scooter trips"),
                                dcc.Graph(id="choropleth", figure={}),
                            ],
                        ),
                    ],
                ),               
                html.Div(
                    className="eight columns card-left",
                    children=[
                        html.Div(
                            className="bg-white",
                            children=[
                                html.H5("Daily trips timeline"),
                                dcc.Graph(id="timeline", figure={}),   
                            ],
                        )
                    ],
                ),
                html.Div(
                    className="four columns card",
                    children=[
                        html.Div(
                            className="bg-white user-control",
                            children=[
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.H6("Census tract"),
                                        dcc.Dropdown(id="tract",
                                            options=[
                                                {'label': i, 'value': i} for i in tract_list['tract']
                                            ],
                                            value='48453001100'
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ]
)

@app.callback(
    Output("choropleth", "figure"), 
    [Input("direction", "value"),
     Input("date_picker", "date"),
     Input("AMPM", "value")]
)

def display_choropleth(direction, date_picker, AMPM):
       
    df = data[data['Date']==date_picker].copy()
    df = df[df['AMPM']==AMPM].copy()
    zero = df[df[direction]==0].copy()
    zero['log'] = 0
    non_zero = df[df[direction]>0].copy()
    non_zero['log'] = np.log10(non_zero[direction])
    df = zero.append(non_zero, ignore_index=True)
    
    fig = px.choropleth_mapbox(data_frame=df, geojson=tracts, locations='GeoID', featureidkey='properties.GEOID', color='log',
                               hover_data=['Starts','Ends'],
                               color_continuous_scale="ylorrd",
                               mapbox_style="stamen-toner", #"stamen-terrain", "stamen-toner"
                               zoom=10.5, center = {"lat": 30.26722, "lon": -97.74306},
                               opacity=0.6
                              )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},coloraxis_colorbar=dict(
        title="Trips", tickvals=[0,1,2,3,4], ticktext=["0", "10", "100", "1,000", "10,000"]))

    return fig

@app.callback(
    Output("timeline", "figure"),
    Input("tract", "value")
)

def display_graph(tract):
    df2 = data[data['GeoID']==tract].groupby('Date').sum()[['Starts','Ends']]
    df2['Starts7'] = 0
    df2['Ends7'] = 0
    date = min(df2.index)
    for i in range(len(df2)):
        j = i
        mean_starts = 0
        mean_ends = 0
        while j >= 0 and i-j < 7:
            mean_starts += df2.iloc[j,0]
            mean_ends += df2.iloc[j,1]
            j -= 1
        df2.iloc[i,2] = round(mean_starts / (i-j), 0)
        df2.iloc[i,3] = round(mean_ends / (i-j), 0)  
        date += timedelta(1)
    df2['Day'] = df2.index.strftime('%A')

    fig = go.Figure()

    starts = go.Scatter(x=df2.index, y=df2.Starts, name="Outgoing trips")
    ends = go.Scatter(x=df2.index, y=df2.Ends, name="Incoming trips", visible=False)
    starts7 = go.Scatter(x=df2.index, y=df2.Starts7, name="7-day average")
    ends7 = go.Scatter(x=df2.index, y=df2.Ends7, name="7-day average", visible=False)

    fig.add_trace(starts)
    fig.add_trace(starts7)
    fig.add_trace(ends)
    fig.add_trace(ends7)


    fig.update_layout(
        updatemenus=[dict(
            active=0,
            buttons=list(
                [dict(label = 'Outgoing trips',
                      method = 'update',
                      args = [{'visible': [True, True, False, False]},
                              {'showlegend':True}]),
                 dict(label = 'Incoming trips',
                      method = 'update',
                      args = [{'visible': [False, False, True, True]},
                              {'showlegend':True}]),
                ]),
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0,
                xanchor="left",
                y=1.25,
                yanchor="top"
            )
        ])
    fig.update_layout(hovermode="x unified")
    fig.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=1.02,
    xanchor="right",
    x=1
    ))
    fig.update_layout(margin={"r":0,"b":0})
    fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)
