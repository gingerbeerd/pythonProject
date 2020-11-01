import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly as py
import dash
import dash_core_components as dcc
import dash_html_components as html
import jupyterlab_dash
import dateutil.parser
import datetime


from datetime import datetime


from dash.dependencies import Input, Output
from jupyterlab_dash import AppViewer
from plotly.subplots import make_subplots

##################################
###########DATA PREP##############
##################################

#confirmed case data
confirmed = pd.read_csv('time_series_covid19_confirmed_global.csv')
#deaths data
deaths = pd.read_csv('time_series_covid19_deaths_global.csv')
#recovered data
recovered = pd.read_csv('time_series_covid19_recovered_global.csv')

movement = pd.read_csv('movement.csv')
stringency = pd.read_csv('Australia - stringincy_news.csv')

#filter to australia only
confirmed = confirmed.loc[confirmed['Country/Region'] == "Australia"]

#Movement data has Australia & states. Nulls on sub_region_1 indicate total australia value, not specific state val
movement = movement.loc[movement['sub_region_1'].notnull()]

#Pivot case data from columns with case numbers to rows
df = pd.melt(confirmed, id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
             var_name='date', value_name='confirmed')

#rename columns to simple values
df.columns = ["state", "country", "lat", "long", "date", "confirmed"]

#State border data for map
#with urlopen('https://github.com/rowanhogan/australian-states/raw/master/states.geojson') as response:
#    states = json.load(response)

# Convert date format to all same
df['date'] = pd.to_datetime(df.date)
movement['date'] = pd.to_datetime(movement.date)
stringency['date'] = pd.to_datetime(stringency.date)

#filter out early data, before cases started
df = df.loc[df['date'] > '2020-2-14']

#join movement and confirmed case DF's
df2 = pd.merge(df, movement, how='outer', left_on=['date', 'state'], right_on=['date', 'sub_region_1'])
df2['dt_str'] = df2['date'].astype(str)


#########################
#########VISUAL##########
#########################


dates =[]
for date in df2['dt_str'].unique():
    dates.append({'label':date ,'value':date})



# make list of continents
#
states = []
for state in df2["state"]:
    if state not in states:
        states.append(state)
# make figure
fig_dict = {
    "data": [],
    "layout": {},
    "frames": []
}

# fill in most of layout
fig_dict["layout"]["xaxis"] = {"range": [00, 30000], "title": "Confirmed Cases"} #,"type":"log"
fig_dict["layout"]["yaxis"] = {"range":[-100,100],"title": "% Movement"}
fig_dict["layout"]["hovermode"] = "closest"
fig_dict["layout"]["updatemenus"] = [
    {
        "buttons": [
            {
                "args": [None, {"frame": {"duration": 50, "redraw": False},
                                "fromcurrent": True, "transition": {"duration": 100,
                                                                    "easing": "quadratic-in-out"}}],
                "label": "Play",
                "method": "animate"
            },
            {
                "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                  "mode": "immediate",
                                  "transition": {"duration": 0}}],
                "label": "Pause",
                "method": "animate"
            }
        ],
        "direction": "left",
        "pad": {"r": 10, "t": 87},
        "showactive": False,
        "type": "buttons",
        "x": 0.1,
        "xanchor": "right",
        "y": 0,
        "yanchor": "top"
    }
]

sliders_dict = {
    "active": 0,
    "yanchor": "top",
    "xanchor": "left",
    "currentvalue": {
        "font": {"size": 20},
        "prefix": "Date:",
        "visible": True,
        "xanchor": "right"
    },
    "transition": {"duration": 50, "easing": "cubic-in-out"},
    "pad": {"b": 10, "t": 50},
    "len": 0.9,
    "x": 0.1,
    "y": 0,
    "steps": []
}

# make data
date = '2020-02-15'
for state in states:
    dataset_by_day = df2[df2["dt_str"] == date]
    dataset_by_day_and_state = dataset_by_day[
        dataset_by_day["state"] == state]

    data_dict = {
        "x": list(dataset_by_day_and_state["confirmed"]),
        "y": list(dataset_by_day_and_state["retail_and_recreation_percent_change_from_baseline"]),
        "mode": "lines+markers",
        "text": list(dataset_by_day_and_state["state"]),
        "marker" : {"size":12, "line":{"width":2,"color":'DarkSlateGrey'}},
        #"marker": {
        #    "sizemode": "area",
        #    "sizeref": 200000,
        #    "size": list(dataset_by_year_and_cont["pop"])
        #},
        "name": state
    }
    fig_dict["data"].append(data_dict)

# make frames
for date in dates:
    frame = {"data": [], "name":date["label"]}
    for state in states:
        dataset_by_date = df2[df2["dt_str"] == date["label"]]
        dataset_by_date_and_state = dataset_by_date[
            dataset_by_date["state"] == state]

        data_dict = {
            "x": list(dataset_by_date_and_state["confirmed"]),
            "y": list(dataset_by_date_and_state["retail_and_recreation_percent_change_from_baseline"]),
            "mode": "markers",
            "text": list(dataset_by_date_and_state["state"]),
            #"marker": {
            #    "sizemode": "area",
            #    "sizeref": 200000,
            #    "size": list(dataset_by_year_and_cont["pop"])
            #},
            "name": state
        }
        frame["data"].append(data_dict)

    fig_dict["frames"].append(frame)
    slider_step = {"args": [
        date["label"],
        {"frame": {"duration": 100, "redraw": False},
         "mode": "immediate",
         "transition": {"duration": 100}}
    ],
        "label": date["label"],
        "method": "animate"}
    sliders_dict["steps"].append(slider_step)


fig_dict["layout"]["sliders"] = [sliders_dict]

fig = go.Figure(fig_dict)

#fig.show()

app = dash.Dash()
app.layout = html.Div([
    dcc.Graph(figure=fig)
])

app.run_server(debug=True, use_reloader=False)