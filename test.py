import urllib
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc
from dash import html
from jupyter_dash import JupyterDash
from dash.dependencies import Input, Output
from traceback import print_tb
from datetime import datetime as dt
from smb.SMBHandler import SMBHandler

pd.options.plotting.backend = "plotly"

director = urllib.request.build_opener(SMBHandler)

fh = director.open('smb://airvisual:wau46aj7@192.168.1.86/airvisual/202209_AirVisual_values.txt')

data = fh.readlines()

previous_lines = len(data)
current_lines = len(data)

cols = ["CO2(ppm)"] #["PM2_5(ug/m3)", 
sensor_data = np.array([l.decode().replace(";\n", "").split(";") for l in data[1:]])
fh.close()


ix = [dt.combine(dt.strptime(entry[0], "%Y/%m/%d").date(), dt.strptime(entry[1], "%H:%M:%S").time()) for entry in sensor_data]
# pm2_5 = sensor_data[:, 3].astype(float)
co2 = sensor_data[:, -1].astype(int)
df = pd.DataFrame(co2, index=ix, columns=cols)


# # plotly figure
fig = df.plot(template = 'plotly_dark')

app = JupyterDash(__name__)
app.layout = html.Div([
    html.H1("Streaming of Air Quality Sensor data"),
            dcc.Interval(
            id='interval-component',
            interval=20*1000, # in milliseconds
            n_intervals=0
        ),
    dcc.Graph(id='graph'),
])


# Define callback to update graph
@app.callback(
    Output('graph', 'figure'),
    [Input('interval-component', "n_intervals")]
)
def streamFig(value):
    
    global df
    global previous_lines
    global current_lines
    
    temp_file = director.open('smb://airvisual:wau46aj7@192.168.1.86/airvisual/202209_AirVisual_values.txt')
    temp = temp_file.readlines()
    current_lines = len(temp)
    new_lines = current_lines - previous_lines
    previous_lines = current_lines

    temp_data = np.array([l.decode().replace(";\n", "").split(";") for l in temp[-new_lines:]])
    temp_ix = [dt.combine(dt.strptime(e[0], "%Y/%m/%d").date(), dt.strptime(e[1], "%H:%M:%S").time()) for e in temp_data]
    temp_co2 = temp_data[:, -1].astype(int)
    temp_df = pd.DataFrame(temp_co2, index=temp_ix, columns=cols)
    df = pd.concat([df, temp_df], axis=0)

    print(temp_df)
    temp_file.close()
    
    fig = df.plot(template = 'plotly_dark')
    
    colors = px.colors.qualitative.Plotly
    for i, col in enumerate(df.columns):
            fig.add_annotation(x=df.index[-1], y=df[col].iloc[-1],
                                   text = str(df[col].iloc[-1])[:4],
                                   align="right",
                                   arrowcolor = 'rgba(0,0,0,0)',
                                   ax=25,
                                   ay=0,
                                   yanchor = 'middle',
                                   font = dict(color = colors[i]))
    
    return(fig)

app.run_server(mode='external', port = 8069, dev_tools_ui=True, #debug=True,
              dev_tools_hot_reload =True, threaded=True)