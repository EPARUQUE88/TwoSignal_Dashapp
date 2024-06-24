import os
from openpyxl import load_workbook, workbook
import pandas as pd
import numpy as np
#from xbbg import blp
import xlwings as xw
import time
import win32com.client
import datetime as dt
from datetime import date
import holidays
import calendar
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import seaborn as sns
import plotly.express as px
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.io as pio
from dash import Dash, html, dash_table, dcc, callback, Output, Input, no_update, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from backtesting import Strategy
from backtesting import Backtest
import warnings 
warnings.filterwarnings('ignore') 


name = "Supranationals1"
securities = "AFDB", "AIIB", "ASIA", "COE", "EBRD", "EIB", "ESM", "IADB", "IBRD", "IDBINV", "IFC", "NIB"
last_date_thnss = '2024-05-03'
frequency = 2
dt_delta = 45
window = 45


def nss_model(x, b0, b1, b2, b3, lambda1, lambda2):

    nss_model_yields = b0 + (b1 * ((1 - np.exp(-x * lambda1)) / (x * lambda1))) + (b2 * (((1 - np.exp(-x * lambda1)) / (
        x * lambda1)) - np.exp(-x * lambda1))) + (b3 * (((1 - np.exp(-x * lambda2)) / (x * lambda2)) - np.exp(-x * lambda2)))

    return nss_model_yields


def nss_curve_fit(maturities, yields):
    p0 = [0.1, 0.1, 0.1, 0.1, 1, 1]

    our_bounds = ([0, -np.inf, -np.inf, -np.inf, -np.inf, -np.inf],
                  [np.inf, np.inf, np.inf, np.inf, np.inf, np.inf])

    nss_curve_fit_results = curve_fit(
        nss_model, maturities, yields, p0=p0, bounds=our_bounds)

    params = nss_curve_fit_results[0]

    return params

ticker_historical_nss = pd.read_excel(
    f"{name}_{last_date_thnss}_Historical_NSS.xlsx", )
ticker_historical_nss.set_index(ticker_historical_nss.columns[0], inplace=True)
df_bondid = pd.read_excel(f"{name}_{last_date_thnss}_Bond_IDs.xlsx")

yerrors = pd.read_excel("YE.xlsx")
yerrors.set_index(yerrors.columns[0], inplace=True)
yields = pd.read_excel("Yields.xlsx")
yields.set_index(yields.columns[0], inplace=True)
yields.columns = yerrors.columns
nss = pd.read_excel("NSS.xlsx")
nss.set_index(nss.columns[0], inplace=True)
nss.columns = yerrors.columns

rolling_mean = yerrors.rolling(window).mean().dropna()
rolling_std = yerrors.rolling(window).std().dropna()
rolling_yerrors = yerrors.iloc[-len(rolling_mean) :]

df_date = pd.DataFrame()
d_empty = []

for i in ticker_historical_nss.index:
    d_empty.append(dt.date.fromisoformat(i))
df_date["Dates"] = d_empty

df_to_locate_ids = pd.DataFrame(yerrors.columns, df_bondid['ID'], columns = ["Bond_Name"]).reset_index()

def cheap_zscore_days_ago(days_ago = 1):
    
    z_score = pd.DataFrame(index=df_bondid["ID"])
    z_score['Name'] = yerrors.columns
    z_score['Tenor'] = df_bondid["Tenor"].to_list()
    
    z = []
    
    for i in range (0,len(z_score.index)):
        rolling_zscore = (rolling_yerrors.iloc[-days_ago][i] - rolling_mean.iloc[-days_ago][i]) / rolling_std.iloc[-days_ago][i]
        z.append(rolling_zscore)
    
    z_score[f"z-score_{days_ago}D"] = z
    
    cheap = [[],[],[],[]]
    
    for i in range (0, len(z_score.index)):
        if z_score.iloc[i][2] > 0:
            cheap[0].append(z_score.index[i])
            cheap[1].append(z_score.iloc[i][0])
            cheap[2].append(z_score.iloc[i][1])
            cheap[3].append(z_score.iloc[i][2])
    
    return cheap   

def rich_zscore_days_ago(days_ago = 1):
    
    z_score = pd.DataFrame(index=df_bondid["ID"])
    z_score['Name'] = yerrors.columns
    z_score['Tenor'] = df_bondid["Tenor"].to_list()
    
    z = []
    
    for i in range (0,len(z_score.index)):
        rolling_zscore = (rolling_yerrors.iloc[-days_ago][i] - rolling_mean.iloc[-days_ago][i]) / rolling_std.iloc[-days_ago][i]
        z.append(rolling_zscore)
    
    z_score[f"z-score_{days_ago}D"] = z
    
    rich = [[],[],[],[]]
    
    for i in range (0, len(z_score.index)):
        if z_score.iloc[i][2] < 0:
            rich[0].append(z_score.index[i])
            rich[1].append(z_score.iloc[i][0])
            rich[2].append(z_score.iloc[i][1])
            rich[3].append(z_score.iloc[i][2])
    
    return rich
    
cheap_1d = cheap_zscore_days_ago(1)
cheap_3d = cheap_zscore_days_ago(3)
cheap_15d = cheap_zscore_days_ago(15)
cheap_30d = cheap_zscore_days_ago(30)

rich_1d = rich_zscore_days_ago(1)
rich_3d = rich_zscore_days_ago(3)
rich_15d = rich_zscore_days_ago(15)
rich_30d = rich_zscore_days_ago(30)

df_cheap_1d = pd.DataFrame(cheap_1d, index = ["ID","Name", "Tenor", "Z_Score"]).T.set_index("ID")
xls_cheap_1d = df_cheap_1d.to_excel("Cheap_1d.xlsx")

df_cheap_3d = pd.DataFrame(cheap_3d, index = ["ID","Name", "Tenor", "Z_Score"]).T.set_index("ID")
xls_cheap_3d = df_cheap_3d.to_excel("Cheap_3d.xlsx")

df_cheap_15d = pd.DataFrame(cheap_15d, index = ["ID","Name", "Tenor", "Z_Score"]).T.set_index("ID")
xls_cheap_15d = df_cheap_15d.to_excel("Cheap_15d.xlsx")

df_cheap_30d = pd.DataFrame(cheap_30d, index = ["ID","Name", "Tenor", "Z_Score"]).T.set_index("ID")
xls_cheap_30d = df_cheap_30d.to_excel("Cheap_30d.xlsx")


df_rich_1d = pd.DataFrame(rich_1d, index = ["ID","Name", "Tenor", "Z_Score"]).T.set_index("ID")
xls_rich = df_rich_1d.to_excel("Rich_1d.xlsx")

df_rich_3d = pd.DataFrame(rich_3d, index = ["ID","Name", "Tenor", "Z_Score"]).T.set_index("ID")
xls_rich = df_rich_3d.to_excel("Rich_3d.xlsx")

df_rich_15d = pd.DataFrame(rich_15d, index = ["ID","Name", "Tenor", "Z_Score"]).T.set_index("ID")
xls_rich = df_rich_15d.to_excel("Rich_15d.xlsx")

df_rich_30d = pd.DataFrame(rich_30d, index = ["ID","Name", "Tenor", "Z_Score"]).T.set_index("ID")
xls_rich = df_rich_30d.to_excel("Rich_30d.xlsx")

cheap_names = pd.concat([df_cheap_1d["Name"],df_cheap_3d["Name"],df_cheap_15d["Name"],df_cheap_30d["Name"]]).unique().tolist()
rich_names = pd.concat([df_rich_1d["Name"],df_rich_3d["Name"],df_rich_15d["Name"],df_rich_30d["Name"]]).unique().tolist()

searchable_names = yerrors.columns.tolist()
type(searchable_names)


# df_bondid_ajdusted_to_issue_dt
x_nss_curve = np.arange(
    1/frequency, df_bondid["Tenor"].round(0).max()+1, 1/frequency/2)
y_nss_curve = nss_model(x_nss_curve, *ticker_historical_nss.iloc[-1])

fig1 = make_subplots(rows=1,
                     cols=1)

fig1.add_trace(go.Scatter(x=df_bondid["Tenor"],
                          y=df_bondid.loc[:][df_bondid.columns[8]],
                          mode="markers",
                          hovertext=df_bondid['name().value'],
                          name=f'{name} Market Level',
                          legendgroup="2"),
               row=1, col=1)

fig1.add_trace(go.Scatter(x=x_nss_curve,
                          y=y_nss_curve,
                          line=dict(color='green', dash="dash", width=6),
                          name="NSS Curve",
                          legendgroup="2"),
               row=1, col=1)

fig1.update_traces(marker_size=25)
fig1.update_layout(template="plotly_dark", legend_tracegroupgap=280)
fig1.update_xaxes(title_text="Maturity")
# fig1.update_yaxes(title_text = "Z_SCORE", row = 1, col = 1)
fig1.update_yaxes(title_text="Yield(%)", row=1, col=1)

fig1.for_each_xaxis(lambda x: x.update(showgrid=False))
fig1.for_each_yaxis(lambda x: x.update(showgrid=False))

fig1.update_traces(marker=dict(color='red'), row=1, col=1)

# fig1.show()

df_cheap_1d.loc[:][df_cheap_1d.columns[0]]

# Plot the historical Z - Score
fig2 = go.Figure()

fig2.add_trace(go.Scatter(x=df_cheap_1d.loc[:][df_cheap_1d.columns[1]],
                          y=df_cheap_1d.loc[:][df_cheap_1d.columns[2]],
                          mode="markers",
                          marker=dict(
                              color=df_cheap_1d.loc[:][df_cheap_1d.columns[2]], colorscale='greens'),
                          hovertext=df_cheap_1d.loc[:][df_cheap_1d.columns[0]],
                          name=f"{name}Cheapest",
                          legendgroup="1",
                          visible=True
                          ))

fig2.add_trace(go.Scatter(x=df_rich_1d.loc[:][df_rich_1d.columns[1]],
                          y=df_rich_1d.loc[:][df_rich_1d.columns[2]],
                          mode="markers",
                          marker=dict(
                              color=df_rich_1d.loc[:][df_rich_1d.columns[2]], colorscale='reds_r'),
                          hovertext=df_rich_1d.loc[:][df_rich_1d.columns[0]],
                          name=f"{name}Richest",
                          legendgroup="1",
                          visible=True
                          ))

fig2.add_trace(go.Scatter(x=df_cheap_3d.loc[:][df_cheap_3d.columns[1]],
                          y=df_cheap_3d.loc[:][df_cheap_3d.columns[2]],
                          mode="markers",
                          marker=dict(
                              color=df_cheap_3d.loc[:][df_cheap_3d.columns[2]], colorscale='greens'),
                          hovertext=df_cheap_3d.loc[:][df_cheap_3d.columns[0]],
                          name=f"{name}Cheapest",
                          legendgroup="1",
                          visible=False
                          ))

fig2.add_trace(go.Scatter(x=df_rich_3d.loc[:][df_rich_3d.columns[1]],
                          y=df_rich_3d.loc[:][df_rich_3d.columns[2]],
                          mode="markers",
                          marker=dict(
                              color=df_rich_3d.loc[:][df_rich_3d.columns[2]], colorscale='reds_r'),
                          hovertext=df_rich_3d.loc[:][df_rich_3d.columns[0]],
                          name=f"{name}Richest",
                          legendgroup="1",
                          visible=False
                          ))
fig2.add_trace(go.Scatter(x=df_cheap_15d.loc[:][df_cheap_15d.columns[1]],
                          y=df_cheap_15d.loc[:][df_cheap_15d.columns[2]],
                          mode="markers",
                          marker=dict(
                              color=df_cheap_15d.loc[:][df_cheap_15d.columns[2]], colorscale='greens'),
                          hovertext=df_cheap_15d.loc[:][df_cheap_15d.columns[0]],
                          name=f"{name}Cheapest",
                          legendgroup="1",
                          visible=False
                          ))

fig2.add_trace(go.Scatter(x=df_rich_15d.loc[:][df_rich_15d.columns[1]],
                          y=df_rich_15d.loc[:][df_rich_15d.columns[2]],
                          mode="markers",
                          marker=dict(
                              color=df_rich_15d.loc[:][df_rich_15d.columns[2]], colorscale='reds_r'),
                          hovertext=df_rich_15d.loc[:][df_rich_15d.columns[0]],
                          name=f"{name}Richest",
                          legendgroup="1",
                          visible=False
                          ))
fig2.add_trace(go.Scatter(x=df_cheap_30d.loc[:][df_cheap_30d.columns[1]],
                          y=df_cheap_30d.loc[:][df_cheap_30d.columns[2]],
                          mode="markers",
                          marker=dict(
                              color=df_cheap_30d.loc[:][df_cheap_30d.columns[2]], colorscale='greens'),
                          hovertext=df_cheap_30d.loc[:][df_cheap_30d.columns[0]],
                          name=f"{name}Cheapest",
                          legendgroup="1",
                          visible=False
                          ))

fig2.add_trace(go.Scatter(x=df_rich_30d.loc[:][df_rich_30d.columns[1]],
                          y=df_rich_30d.loc[:][df_rich_30d.columns[2]],
                          mode="markers",
                          marker=dict(
                              color=df_rich_30d.loc[:][df_rich_30d.columns[2]], colorscale='reds_r'),
                          hovertext=df_rich_30d.loc[:][df_rich_30d.columns[0]],
                          name=f"{name}Richest",
                          legendgroup="1",
                          visible=False
                          ))

fig2.add_hline(y=0, line_color="red", row=1, col=1)
fig2.update_traces(marker_size=25)

fig2.for_each_xaxis(lambda x: x.update(showgrid=False))
fig2.for_each_yaxis(lambda x: x.update(showgrid=False))

fig2.update_layout(template="plotly_dark", legend_tracegroupgap=280)
fig2.update_xaxes(title_text="Maturity")
fig2.update_yaxes(title_text="Z_SCORE")

fig2.update_layout(
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            x=0.7,
            y=1.2,
            showactive=True,
            buttons=list(
                [
                    dict(
                        label="1D",
                        method="update",
                        args=[{"visible": [True, True, False,
                                           False, False, False, False, False]}],
                    ),
                    dict(
                        label="3D",
                        method="update",
                        args=[{"visible": [False, False, True,
                                           True, False, False, False, False]}],
                    ),

                    dict(
                        label="15D",
                        method="update",
                        args=[{"visible": [False, False, False,
                                           False, True, True, False, False]}],
                    ),
                    dict(
                        label="30D",
                        method="update",
                        args=[{"visible": [False, False, False,
                                           False, False, False, True, True]}],
                    )
                ]
            )
        )
    ]
)
#fig2.show()


def get_data_for_backtesting (the_bond):

    sec_in_analysis = the_bond

    for i in range (len(df_to_locate_ids[df_to_locate_ids.columns[1]])):
        if df_to_locate_ids[df_to_locate_ids.columns[1]][i] == sec_in_analysis:
            id_security = df_to_locate_ids[df_to_locate_ids.columns[0]][i]
        else:
            None

    diff = []
    yi =[]

    for i in range (len(yerrors.index)):
        
        di = yields[sec_in_analysis][i] - nss[sec_in_analysis][i]
        yy = yerrors.index[i]

        diff.append(di)
        yi.append(yy)

        market_vs_nss = pd.DataFrame(diff, columns = ["Diff_Level"], index = yi)
        market_vs_nss.index.set_names("Date", inplace=True)


    individual_zscore = (yerrors[sec_in_analysis] - (yerrors[sec_in_analysis].rolling(window).mean().dropna()))/ yerrors[sec_in_analysis].rolling(window).std().dropna()
    individual_zscore  = individual_zscore.dropna()
    individual_zscore.index.set_names("Date", inplace=True)

    px_data = blp.bdh(id_security, ["PX_OPEN", "PX_HIGH", "PX_LOW", "PX_LAST"],individual_zscore .index[0],individual_zscore .index[-1])
    px_data = px_data.droplevel(0, axis=1)
    market_vs_nss = market_vs_nss[-len(px_data):]
    individual_zscore = individual_zscore[-len(px_data):]
    px_data.index.set_names("Date", inplace=True)
    date_index = pd.to_datetime(px_data.index)
    px_data.index = date_index
    market_vs_nss.index = date_index
    individual_zscore.index = date_index

    data_for_backtesting = pd.concat([px_data,market_vs_nss,individual_zscore], axis=1, ignore_index=True)
    data_for_backtesting.columns = ['Open', 'High', 'Low', 'Close',"DiffLevel", "Zscore"]

    return data_for_backtesting



def Buy_Signal(backtest_data, nss_up_bound_threshold = 0.2, zcsore_up_bound_threshold = 2 ):

    action_obs = []

    nss_up_bound = nss_up_bound_threshold
    zcsore_up_bound = zcsore_up_bound_threshold 


    for i in range (len(backtest_data['Zscore'])):

        if backtest_data['Zscore'][i] >= zcsore_up_bound and backtest_data['DiffLevel'][i] >= nss_up_bound:
            
            action_obs.append(2)

        elif backtest_data['Zscore'][i] < 0 and backtest_data['DiffLevel'][i] < 0:

            action_obs.append(1)

        else:
            action_obs.append(0)
    
    buysinal = pd.DataFrame(action_obs, index=backtest_data.index, columns=["BuySignal"])

    return buysinal


def Sell_Signal(backtest_data, nss_lower_bound_threshold = -0.2, zcsore_lower_bound_threshold = -2 ):

    action_obs = []

    nss_lower_bound = nss_lower_bound_threshold
    zcsore_lower_bound = zcsore_lower_bound_threshold 


    for i in range (len(backtest_data['Zscore'])):

        if backtest_data['Zscore'][i] <= zcsore_lower_bound and backtest_data['DiffLevel'][i] <= nss_lower_bound:
            
            action_obs.append(-2)

        elif backtest_data['Zscore'][i] > 0: #and backtest_data['DiffLevel'][i] > 0:

            action_obs.append(-1)

        else:
            
            action_obs.append(0)
    
    sellsinal = pd.DataFrame(action_obs, index=backtest_data.index, columns=["SellSignal"])

   
    return sellsinal

class TwoSignal(Strategy):

    nss_upper_100= 10
    nss_lower_100 = -10
    zscore_upper_100 = 200
    zscore_lower_100 = -200

    nss_upper = nss_upper_100/100
    nss_lower = nss_lower_100 /100
    zscore_upper = zscore_upper_100/100
    zscore_lower = zscore_lower_100/100


    def init(self):
        super().init()
        self.buysignal = self.I(Buy_Signal, self.data, self.nss_upper, self.zscore_upper )
        self.sellsignal = self.I(Sell_Signal, self.data, self.nss_lower, self.zscore_lower)

    def next(self):

        if self.buysignal == 2:
            if not self.position.is_long:
                price = self.data.Close[-1]
                self.buy(sl=price - 0.10)

        elif self.buysignal == 1:
            if self.position.is_long:
                self.position.close()

        if self.sellsignal == -2:
            if not self.position.is_short:
                price = self.data.Close[-1]
                self.sell(sl = price + 0.10)
        elif self.sellsignal == -1:
            if self.position.is_short:
                self.position.close()
        
        else:
            None 

the_bond = "IBRD 4 3/4 11/14/33"

#backtest_data = get_data_for_backtesting(the_bond)


#bt = Backtest(backtest_data,TwoSignal ,cash=10_000, commission=0)
#stats = bt.run()
"""stats = bt.optimize(nss_upper_100 = range(0,30,5),
                    nss_lower_100 = range(-100,0,1),
                    zscore_upper_100 = range(0,300,50),
                    zscore_lower_100 = range(-500,0,100),
                    maximize= "Sharpe Ratio")"""
#stats
#stats._strategy
#bt.plot(filename="assets/plots4bkbacktesting_plot.html",open_browser=False)

"""
df_stats_bkx = stats.to_frame()
df_stats_bkx = df_stats_bkx.drop(labels = ["_equity_curve","_trades","Buy & Hold Return [%]","SQN", "Calmar Ratio"])
df_stats_bkx.reset_index(inplace = True)
df_stats_bkx.columns = ["Description", "Output"]
xls_df_stats_bkx  = df_stats_bkx.to_excel("BK_Stats.xlsx")

df_stats_bk = pd.read_excel("BK_Stats.xlsx")
df_stats_bk.set_index(df_stats_bk.columns[0], inplace=True)
df_stats_bk
"""

the_bond = "IBRD 4 3/4 11/14/33"
df_stats = pd.read_excel("Stats.xlsx")
df_stats.set_index(df_stats.columns[0], inplace = True)
df_stats.drop(labels = ["_equity_curve","_trades","Buy & Hold Return [%]","SQN", "Calmar Ratio", 'Security Name'],inplace=True)
df_stats.reset_index(inplace=True)
df_stats.rename(columns = {"Unnamed: 0" : "Description"}, inplace = True)
stats_bondid = df_stats.columns
position = stats_bondid.tolist().index(the_bond)
df_stats.columns[position]
datatable_stast = dash_table.DataTable(data = df_stats.to_dict('records'), columns = [{"Description" : i , "Output" : j} for i, j in zip (df_stats["Description"],df_stats[f"{the_bond}"])])
datatable_stast

app = Dash(__name__,external_stylesheets=[dbc.themes.DARKLY],
           meta_tags=[{'name': 'viewport',
                       'content': 'width = device-width, initial-scale = 1.0'}]
           )

app.layout = dbc.Container([
    html.Div(id="output"),
    dcc.Store(id="store-data", data = [], storage_type = 'memory'),
    dbc.Row([
        dbc.Col(html.H1("Relative Value Analysis: NSS Model & Z - Score (90D)",
                        className='text-center font-weight-bolder text-primary mb-4'),
                width=12),

    ]),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='cheap_dropdown', multi=True,
                         value=[],
                         options=cheap_names,
                         style={"color": "white",
                                'background-color': 'black'},
                         placeholder="Select a Cheapest...",
                         className="VirtualizedSelectOption"
                         )
        ]),
        dbc.Col([dcc.Dropdown(id='rich_dropdown', multi=True,
                              value=[],
                              options=rich_names,
                              style={"color": "white",
                                     'background-color': 'black'},
                              placeholder="Select a Richest...",
                              className="VirtualizedSelectOption"
                              )
                 ])
    ]),
    html.Br(),
    dbc.Row([dcc.Graph(id='NSS_Graph', figure=fig1)
             ]),
    html.Br(),
    dbc.Row([dcc.Graph(id='zscore_graph', figure=fig2)]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='backtested_security', multi=False,
                         value=the_bond,
                         options= stats_bondid,
                         style={"color": "white",
                                'background-color': 'black'},
                         placeholder="Select Security..."
                         )
        ]),
        dbc.Col([dbc.Button("Click Here To Run The Backtest", id='run_backtesting',
                              style={"color": "white",
                                     'background-color': 'black'},
                              n_clicks = 0,
                              outline = False,
                              className="VirtualizedSelectOption"
                              )
                 ], width=8, className="d-grid gap-2 col-6 mx-auto")
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([dash_table.DataTable(id ="backtesting_stats", data = df_stats.to_dict('records'), 
                                      columns =[{"id" : "Description" , "name" : "Description"},
                                                {"id" : the_bond, "name" : the_bond}],
                                      style_cell={'textAlign': 'center'},
                                      style_header={'backgroundColor': 'rgb(15, 15, 15)',
                                                        'color': 'white','fontWeight': 'bold',
                                                        'border': '1px solid black'},
                                        style_data={'backgroundColor': 'rgb(15, 15, 15)',
                                                    'color': 'white',
                                                    'border': '1px solid black'})
                                                ]
                                        ),

        dbc.Col([html.Iframe(id="backtesting_plot",
                             src="assets/plots4bk/backtesting_plot.html",
                             style={"height" : "2500px", 
                                    "width" : "100%"}
                             )],width=8)])
    ],fluid=True)

@app.callback(Output(component_id='zscore_graph', component_property='figure'),
          [Input(component_id='cheap_dropdown', component_property='value'),
           Input(component_id='rich_dropdown', component_property='value')])

def update_cheap_graph(value_cheap, value_rich):
    
    full_list = value_cheap + value_rich
    
    if len(full_list) == 0:
        
        return fig2
    
    elif len(full_list) > 0:

        cheap_1d_updated = df_cheap_1d[df_cheap_1d["Name"].isin(value_cheap)]
        cheap_3d_updated = df_cheap_3d[df_cheap_3d["Name"].isin(value_cheap)]
        cheap_15d_updated = df_cheap_15d[df_cheap_15d["Name"].isin(value_cheap)]
        cheap_30d_updated = df_cheap_30d[df_cheap_30d["Name"].isin(value_cheap)]
        
        rich_1d_updated = df_rich_1d[df_rich_1d["Name"].isin(value_rich)]
        rich_3d_updated = df_rich_3d[df_rich_3d["Name"].isin(value_rich)]
        rich_15d_updated = df_rich_15d[df_rich_15d["Name"].isin(value_rich)]
        rich_30d_updated = df_rich_30d[df_rich_30d["Name"].isin(value_rich)]

        fig_rv_updated = go.Figure()

        fig_rv_updated.add_trace(go.Scatter(x=cheap_1d_updated.loc[:][cheap_1d_updated.columns[1]],
                                               y=cheap_1d_updated.loc[:][cheap_1d_updated.columns[2]],
                                               mode="markers",
                                               marker=dict(
                                                   color=cheap_1d_updated.loc[:][cheap_1d_updated.columns[2]], colorscale='greens'),
                                               hovertext=cheap_1d_updated.loc[:][cheap_1d_updated.columns[0]],
                                               name=f"{name}Cheapest",
                                               legendgroup="1",
                                               visible=True
                                               ))
        
        fig_rv_updated.add_trace(go.Scatter(x=rich_1d_updated.loc[:][rich_1d_updated.columns[1]],
                                               y=rich_1d_updated.loc[:][rich_1d_updated.columns[2]],
                                               mode="markers",
                                               marker=dict(
                                                   color=rich_1d_updated.loc[:][rich_1d_updated.columns[2]], colorscale='reds_r'),
                                               hovertext=rich_1d_updated.loc[:][rich_1d_updated.columns[0]],
                                               name=f"{name}Richest",
                                               legendgroup="1",
                                               visible=True
                                               ))
 
        fig_rv_updated.add_trace(go.Scatter(x=cheap_3d_updated.loc[:][cheap_3d_updated.columns[1]],
                                               y=cheap_3d_updated.loc[:][cheap_3d_updated.columns[2]],
                                               mode="markers",
                                               marker=dict(
                                                   color=cheap_3d_updated.loc[:][cheap_3d_updated.columns[2]], colorscale='greens'),
                                               hovertext=cheap_3d_updated.loc[:][cheap_3d_updated.columns[0]],
                                               name=f"{name}Cheapest",
                                               legendgroup="1",
                                               visible=False
                                               ))
        
        fig_rv_updated.add_trace(go.Scatter(x=rich_3d_updated.loc[:][rich_3d_updated.columns[1]],
                                               y=rich_3d_updated.loc[:][rich_3d_updated.columns[2]],
                                               mode="markers",
                                               marker=dict(
                                                   color=rich_3d_updated.loc[:][rich_3d_updated.columns[2]], colorscale='reds_r'),
                                               hovertext=rich_3d_updated.loc[:][rich_3d_updated.columns[0]],
                                               name=f"{name}Richest",
                                               legendgroup="1",
                                               visible=False
                                               ))
        
        fig_rv_updated.add_trace(go.Scatter(x=cheap_15d_updated.loc[:][cheap_15d_updated.columns[1]],
                                               y=cheap_15d_updated.loc[:][cheap_15d_updated.columns[2]],
                                               mode="markers",
                                               marker=dict(
                                                   color=cheap_15d_updated.loc[:][cheap_15d_updated.columns[2]], colorscale='greens'),
                                               hovertext=cheap_15d_updated.loc[:][cheap_15d_updated.columns[0]],
                                               name=f"{name}Cheapest",
                                               legendgroup="1",
                                               visible=False
                                               ))
        
        fig_rv_updated.add_trace(go.Scatter(x=rich_15d_updated.loc[:][rich_15d_updated.columns[1]],
                                               y=rich_15d_updated.loc[:][rich_15d_updated.columns[2]],
                                               mode="markers",
                                               marker=dict(
                                                   color=rich_15d_updated.loc[:][rich_15d_updated.columns[2]], colorscale='reds_r'),
                                               hovertext=rich_15d_updated.loc[:][rich_15d_updated.columns[0]],
                                               name=f"{name}Richest",
                                               legendgroup="1",
                                               visible=False
                                               )) 

        fig_rv_updated.add_trace(go.Scatter(x=cheap_30d_updated.loc[:][cheap_30d_updated.columns[1]],
                                               y=cheap_30d_updated.loc[:][cheap_30d_updated.columns[2]],
                                               mode="markers",
                                               marker=dict(
                                                   color=cheap_30d_updated.loc[:][cheap_30d_updated.columns[2]], colorscale='greens'),
                                               hovertext=cheap_30d_updated.loc[:][cheap_30d_updated.columns[0]],
                                               name=f"{name}Cheapest",
                                               legendgroup="1",
                                               visible=False
                                               ))
        
        fig_rv_updated.add_trace(go.Scatter(x=rich_30d_updated.loc[:][rich_30d_updated.columns[1]],
                                               y=rich_30d_updated.loc[:][rich_30d_updated.columns[2]],
                                               mode="markers",
                                               marker=dict(
                                                   color=rich_30d_updated.loc[:][rich_30d_updated.columns[2]], colorscale='reds_r'),
                                               hovertext=rich_30d_updated.loc[:][rich_30d_updated.columns[0]],
                                               name=f"{name}Richest",
                                               legendgroup="1",
                                               visible=False
                                               ))   
        
        fig_rv_updated.add_hline(y=0, line_color="red", row=1, col=1)
        fig_rv_updated.update_traces(marker_size=25)

        fig_rv_updated.for_each_xaxis(lambda x: x.update(showgrid=False))
        fig_rv_updated.for_each_yaxis(lambda x: x.update(showgrid=False))

        fig_rv_updated.update_layout(
            template="plotly_dark", legend_tracegroupgap=280)
        fig_rv_updated.update_xaxes(title_text="Maturity")
        fig_rv_updated.update_yaxes(title_text="Z_SCORE")

        fig_rv_updated.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="right",
                    x=0.7,
                    y=1.2,
                    showactive=True,
                    buttons=list(
                        [
                            dict(
                                label="1D",
                                method="update",
                                args=[{"visible": [True, True, False, False, False, False, False, False]}],
                            ),
                            dict(
                                label="3D",
                                method="update",
                                args=[{"visible": [False, False, True, True, False, False, False, False]}],
                            ),

                            dict(
                                label="15D",
                                method="update",
                                args=[{"visible": [False, False, False, False, True, True, False, False]}],
                            ),
                            dict(
                                label="30D",
                                method="update",
                                args=[{"visible": [False, False, False, False,False, False, True, True]}],
                            )
                        ]
                    )
                )
            ]
        )
        
    return fig_rv_updated

@app.callback([Output(component_id = "backtesting_stats", component_property = 'columns'),
              Output(component_id="backtesting_plot", component_property="src")],
              Input(component_id = 'run_backtesting', component_property = "n_clicks"),
              State(component_id = 'backtested_security', component_property = "value"),
              prevent_initial_update = True)

def update_stats(n_clicks , value):

    if value == [] and n_clicks > 0:

        raise PreventUpdate
    
    else:

        the_bond_no_spcace = value 
        the_bond_no_spcace = the_bond_no_spcace.replace(" ","_")
        the_bond_no_spcace = the_bond_no_spcace.replace("/","_")
        
        new_link = f'assets/plots4bk/{the_bond_no_spcace}.html'

        columns =[{"id" : "Description" , "name" : "Description"},{"id" : f"{value}", "name" : f"{value}"}]
    
    return columns, new_link



if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)
