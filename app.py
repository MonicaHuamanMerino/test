
# Import modules
from dash import Dash, html, dcc, Input, Output, dash_table
from dash.dependencies import State
import pandas as pd
import numpy as np
import pysftp
import io
import base64
import psycopg2
import dash_auth
from datetime import datetime
import time
time.clock = time.time

# Import dictionaries
from dict_ca import dict_ca 
from dict_ca_types import dict_ca_types
from dict_categories import dict_ca_name_n
from dict_rename_cols import dict_div_rename

# Import functions
from functions_tool import parse_contents_files
from functions_tool import upload_files_to_sftp
from functions_tool import parse_contents
from functions_tool import status_pdf

# App
app = Dash(__name__)

# Create the initial data frame for dividends
df = pd.DataFrame(index=range(5),columns=dict_ca['Dividends'])

# Create the structure of the app
app.layout = html.Div([
                    html.Div([
                        # Text: "INSERT NEW CORPORATE ACTIONS"
                        html.Div([
                                    html.H5("INSERT NEW CORPORATE ACTIONS")
                                    ])
                            ]),
                    # Dropdown for corporate action categories
                    html.Div([
                        dcc.Dropdown(id = 'type_corp_act',
                                     multi = False,
                                     value = 'Dividends',
                                     options = list(dict_ca.keys())
                                     )
                            ]),
                    # Data Table
                    html.Div([
                            dash_table.DataTable(
                                id='tbl',
                                data=df.to_dict('records'),
                                columns = [{"name": i, "id": i, "presentation": "dropdown", "type": dict_ca_types[i]} if i in ['Scope Affected','Corporate Action Status'] else {"name": i, "id": i, "type": dict_ca_types[i]} for i in df.columns],
                                editable=True,
                                dropdown={
                                    'Scope Affected': {
                                        'options': [ {'label': i, 'value': i} for i in ["1","2","3"] ]
                                        },
                                    'Corporate Action Status': {
                                        'options': [ {'label': i, 'value': i} for i in ["N"] ]
                                        }
                                    },
                                row_deletable=True
                                ),
                            html.Div(id='tbl-container')
                            ]),
                    # Button: Add Row (to add new rows for insert into)
                    html.Div(
                            [
                                html.Button('Add Row', id='editing-rows-button', n_clicks=0),
                                ]
                            ),
                    # Button: Insert Data (to insert data)
                    html.Div(
                            [
                                html.Button('Insert Data', id='tbl-button-insertinto', n_clicks=0),
                                html.Div(id = 'tbl-text-status')
                                ]
                            ),
                    # Drag and drop .pdf, .xlsx, .csv, .doc, .png files
                    html.Div(
                            [
                                dcc.Upload(
                                            id = 'upload_doc',
                                            children = html.Div([
                                                                 'Drag and Drop or ',
                                                                 html.A('Select Files')
                                                                ]),
                                            style = {
                                                    'width': '20%',
                                                    'height': '60px',
                                                    'lineHeight': '60px',
                                                    'borderWidth': '1px',
                                                    'borderStyle': 'dashed',
                                                    'borderRadius': '5px',
                                                    'textAlign': 'center',
                                                    'margin': '10px'
                                                    }
                                            )
                                ]
                            ),
                    # Show the message "Done" when upload the document
                    html.Div(id='output-data-upload'),
                    html.Div([
                                # Box to rename the document
                                dcc.Textarea(
                                             id = 'textarea-state-example',
                                             value = 'Name of the document to save in SFTP',
                                             style = {'width': '30%', 'height': 20},
                                             ),
                                # Send to SFTP
                                html.Button(
                                            'Submit',
                                            id = 'textarea-state-example-button',
                                            n_clicks = 0
                                            ),
                                # Show the message "Done"
                                html.Div(
                                         id = 'textarea-state-example-output'
                                         )
                            ]),
                    # Box to rename the document
                    html.Div([
                        # Text: "UPDATE CORPORATE ACTIONS"
                        html.Div([
                                    html.H5("UPDATE CORPORATE ACTIONS")
                                    ])
                            ]),
                    html.Div([
                        # Dropdown for corporate action categories
                        dcc.Dropdown(id = 'type_corp_act_2',
                                     multi = False,
                                     value = 'Dividends',
                                     options = list(dict_ca.keys())
                                     )
                            ]),
                    # Data Table
                    html.Div([
                            dash_table.DataTable(
                                id='tbl2',
                                data=df.to_dict('records'),
                                columns = [{"name": i, "id": i, "presentation": "dropdown", "type": dict_ca_types[i]} if i in ['Scope Affected','Corporate Action Status'] else {"name": i, "id": i, "type": dict_ca_types[i]} for i in df.columns],
                                editable=True,
                                dropdown={
                                    'Scope Affected': {
                                        'options': [ {'label': i, 'value': i} for i in ["1","2","3"] ]
                                        },
                                    'Corporate Action Status': {
                                        'options': [ {'label': i, 'value': i} for i in ["M"] ]
                                        }
                                    },
                                row_deletable=True
                                ),
                            html.Div(id='tbl-container2')
                            ]),
                    # Button: Add Row (to add new rows for insert into)
                    html.Div(
                            [
                                html.Button('Add Row', id='editing-rows-button2', n_clicks=0),
                                ]
                            ),
                    # Button: Get data by "id"
                    html.Div(
                            [
                                html.Button('Get data by id', id='tbl-button-selectupd', n_clicks=0)
                                ]
                            ),
                    # Button: Execute the update (to update data by id)
                    html.Div(
                            [
                                html.Button('Update Data', id='tbl-button-exec_update', n_clicks=0),
                                html.Div(id = 'tbl-text-status2')
                                ]
                            )
                    ])

# --------
# Callback: Upload documents 
# --------
@app.callback(Output('output-data-upload', 'children'),
              Input('upload_doc', 'contents'),
              Input('upload_doc', 'filename'))
def update_output(filecontent, filename):
    if filecontent is not None:
        children = [parse_contents(filename)]
        return children

# --------
# Callback: Add row 
# --------
@app.callback(
    Output('tbl', 'data'),
    Input('editing-rows-button', 'n_clicks'),
    State('tbl', 'data'),
    State('tbl', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

# --------
# Callback: Modify data table when select the ca category in the dropdown 
# --------
@app.callback(Output('tbl', 'columns'),
              Input('type_corp_act', 'value'))
def actualize_db(type_layout):
    return [{"name": i, "id": i, "presentation":"dropdown"} if i in ['Scope Affected',"Corporate Action Status"] else {"name": i, "id": i} for i in dict_ca[type_layout]]

# --------
# Callback: Modify data table when select the ca category in the dropdown 
# --------
@app.callback(Output('tbl2', 'columns'),
              Input('type_corp_act_2', 'value'))
def actualize_db_2(type_layout):
    return [{"name": i, "id": i, "presentation":"dropdown"} if i in ['Scope Affected',"Corporate Action Status"] else {"name": i, "id": i} for i in dict_ca[type_layout]]

# --------
# Callback: Send files with a click by SFTP 
# --------
@app.callback(
    Output('textarea-state-example-output', 'children'),
    Input('textarea-state-example-button', 'n_clicks'),
    Input('upload_doc', 'contents'),
    Input('upload_doc', 'filename'),
    State('textarea-state-example', 'value')
)
def update_output_2(n_clicks, filecontent, filename, value):
    if n_clicks > 0:
        return html.Div([
                        upload_files_to_sftp(filecontent, filename, value)
                        ])

# --------
# Callback: Insert into information using the upper table
# --------
@app.callback(
    Output('tbl-text-status', 'children'),
    Input('tbl-button-insertinto', 'n_clicks'),
    Input('type_corp_act', 'value'),
    [Input('tbl', 'data'),
      Input('tbl', 'columns')])
def insert_into_ca(n_clicks, type_of_ca, data, cols):

    if n_clicks > 0:

        if type_of_ca == 'Dividends':
            
            # Create the data frame
            df = pd.DataFrame(data, columns=[ c['name'] for c in cols])
            df = df.drop(['Corporate Action Status','If modification id'],axis=1)
            df.columns = [dict_div_rename[type_of_ca][i] for i in df.columns]
            df['ficad00000'] = 'N'

            # Type of corporate actions
            df['fica000004'] = "1"

            # Timestamp
            datetime_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.000")
            df['fica000008'] = datetime_now
            
            # Divide the data frame between:
            # Insert-into
            df_new = df.copy()

            print([i[10] for i in df_new.to_numpy()])
            print([i[11] for i in df_new.to_numpy()])
            print([None if (pd.isna(i[10]) or i[10]=="") else float(i[10].replace(",",".").strip()) if isinstance(i[10],str) else float(str(i[10]).replace(",",".").strip()) for i in df_new.to_numpy()])
            print([None if (pd.isna(i[11]) or i[11]=="") else float(i[11].replace(",",".").strip()) if isinstance(i[11],str) else float(str(i[11]).replace(",",".").strip()) for i in df_new.to_numpy()])
            
            # Conditional
            if len(df_new) > 0:
            
                # Insert-into
                list_insert_into = [ (str(i[0]).strip() if isinstance(i[0],int) else i[0].strip(),
                                      int(i[1].strip()) if isinstance(i[1],str) else int(i[1]),
                                      str(i[2]).strip() if isinstance(i[2],int) else i[2].strip(),
                                      str(i[3]).strip() if isinstance(i[3],int) else i[3].strip(),
                                      str(i[4]).strip() if isinstance(i[4],int) else i[4].strip(),
                                      str(i[5]).strip() if isinstance(i[5],int) else i[5].strip(),
                                      str(i[6]).strip() if isinstance(i[6],int) else i[6].strip(),
                                      str(i[7]).strip() if isinstance(i[7],int) else i[7].strip(),
                                      str(i[8]).strip() if isinstance(i[8],int) else i[8].strip(),
                                      str(i[9]).strip() if isinstance(i[9],int) else i[9].strip(),
                                      None if (pd.isna(i[10]) or i[10] == "")  else float(i[10].replace(",",".").strip()) if isinstance(i[10],str) else float(str(i[10]).replace(",",".").strip()),
                                      None if (pd.isna(i[11]) or i[11] == "") else float(i[11].replace(",",".").strip()) if isinstance(i[11],str) else float(str(i[11]).replace(",",".").strip()),
                                      str(i[12]).strip() if isinstance(i[12],int) else i[12].strip(),
                                      str(i[13]).strip() if isinstance(i[13],int) else i[13].strip(),
                                      int(i[14].strip()) if isinstance(i[14],str) else int(i[14]),
                                      str(i[15]).strip() if isinstance(i[15],int) else i[15].strip()) for i in df_new.to_numpy()]
    
                # New Backend (POSTGRES)
                newbackend_ca_db = psycopg2.connect(host = "db-dev-cluster.cdv9yi5xuzxq.eu-west-3.rds.amazonaws.com",
                                                    database = "corporate actions",
                                                    user = "postgres",
                                                    password = "934m$b&QnCrk")
                cursor = newbackend_ca_db.cursor() 
                cursor.executemany(' INSERT INTO dividends ' + "(" + ",".join(df_new.columns) + ")" +\
                                    ' VALUES ' + "(" + ",".join(["%s" for i in df_new.columns]) + ")",
                                    list_insert_into)
                newbackend_ca_db.commit()
                cursor.close()
        
        else:
    
            # Create the data frame
            df = pd.DataFrame(data, columns=[ c['name'] for c in cols])
            df = df.drop(['Corporate Action Status','If modification id'],axis=1)
            df.columns = [dict_div_rename[type_of_ca][i] for i in df.columns]
            df['ficad00000'] = 'N'

            # Type of corporate actions
            df['fica000004'] = dict_ca_name_n[type_of_ca]

            # Timestamp
            datetime_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.000")
            df['fica000008'] = datetime_now

            # New Backend (POSTGRES)
            newbackend_ca_db = psycopg2.connect(host = "db-dev-cluster.cdv9yi5xuzxq.eu-west-3.rds.amazonaws.com",
                                                database = "corporate actions",
                                                user = "postgres",
                                                password = "934m$b&QnCrk")

            # Get information
            df_get_ids = pd.read_sql_query('SELECT fica000007 FROM corporate_action_rows',newbackend_ca_db)
            available_ids = [i for i in range(1,300000) if i not in df_get_ids['fica000007'].tolist()]
            
            # Include available 'ids'
            df['fica000007'] = available_ids[:len(df)]

            # Columns
            list_cols_ca_rows = ["ficad00000", "fica000007", "ficad00001", "fica000001", "fica000002", "ficad00003", "fica000005", "fica000004", "fica000008", "fiad00004"]
            
            # Create the data frame for corporate action rows
            df_new_ca_rows = df[list_cols_ca_rows]
            # Create the data frame for corporate action data
            df_new_ca_data = df[["fica000007"] + [ i for i in df.columns if i not in list_cols_ca_rows]]
            df_new_ca_data = pd.melt(df_new_ca_data,id_vars='fica000007').rename(columns={'variable':'fica000009','value':'fica000011'})
            df_new_ca_data['fica000009'] = df_new_ca_data['fica000009'].astype(str)
            df_new_ca_data['fica000011'] = df_new_ca_data['fica000011'].astype(str)
            df_new_ca_data = df_new_ca_data[~pd.isna(df_new_ca_data['fica000011'])]

            filt_01 = df_new_ca_data['fica000011'] == 'nan'
            filt_02 = df_new_ca_data['fica000011'].apply(lambda x: x.strip() == '')
            df_new_ca_data = df_new_ca_data[~(filt_01|filt_02)]

            # Conditional to upload corporate_action_rows
            if len(df_new_ca_rows) > 0:
            
                # Insert-into
                list_insert_into = [ (str(i[0]).strip() if isinstance(i[0],int) else i[0].strip(),
                                      int(i[1].strip()) if isinstance(i[1],str) else int(i[1]),
                                      None if pd.isna(i[2]) else str(i[2]).strip() if isinstance(i[2],int) else i[2].strip(),
                                      int(i[3].strip()) if isinstance(i[3],str) else int(i[3]),
                                      str(i[4]).strip() if isinstance(i[4],int) else i[4].strip(),
                                      None if pd.isna(i[5]) else str(i[5]).strip() if isinstance(i[5],int) else i[5].strip(),
                                      None if pd.isna(i[6]) else str(i[6]).strip() if isinstance(i[6],int) else i[6].strip(),
                                      int(i[7].strip()) if isinstance(i[7],str) else int(i[7]),
                                      str(i[8]).strip() if isinstance(i[8],int) else i[8].strip(),
                                      None if pd.isna(i[9]) else str(i[9]).strip() if isinstance(i[9],int) else i[9].strip()) for i in df_new_ca_rows.to_numpy()]
    
                # New Backend (POSTGRES)
                newbackend_ca_db = psycopg2.connect(host = "db-dev-cluster.cdv9yi5xuzxq.eu-west-3.rds.amazonaws.com",
                                                    database = "corporate actions",
                                                    user = "postgres",
                                                    password = "934m$b&QnCrk")
                cursor = newbackend_ca_db.cursor()
                cursor.executemany(' INSERT INTO corporate_action_rows ' + "(" + ",".join(df_new_ca_rows.columns) + ")" +\
                                   ' VALUES ' + "(" + ",".join(["%s" for i in df_new_ca_rows.columns]) + ")",
                                   list_insert_into)
                newbackend_ca_db.commit()
                cursor.close()

            # Conditional to upload corporate_action_data
            if len(df_new_ca_data) > 0:
            
                # Insert-into
                list_insert_into = [ (int(i[0].strip()) if isinstance(i[0],str) else int(i[0]),
                                      str(i[1]).strip() if isinstance(i[1],int) else i[1].strip(),
                                      str(i[2]).strip() if isinstance(i[2],int) else i[2].strip()) for i in df_new_ca_data.to_numpy()]
    
                # New Backend (POSTGRES)
                newbackend_ca_db = psycopg2.connect(host = "db-dev-cluster.cdv9yi5xuzxq.eu-west-3.rds.amazonaws.com",
                                                    database = "corporate actions",
                                                    user = "postgres",
                                                    password = "934m$b&QnCrk")
                cursor = newbackend_ca_db.cursor() 
                cursor.executemany(' INSERT INTO corporate_action_data ' + "(" + ",".join(df_new_ca_data.columns) + ")" +\
                                   ' VALUES ' + "(" + ",".join(["%s" for i in df_new_ca_data.columns]) + ")",
                                    list_insert_into)
                newbackend_ca_db.commit()
                cursor.close()
            
    
    return html.Div([
                    html.H5("Done")
                    ])

# --------
# Callback: Get by ids 
# --------
@app.callback(
    Output('tbl2', 'data'),
    Input('tbl-button-selectupd', 'n_clicks'),
    Input('type_corp_act_2', 'value'),
    [State('tbl2', 'data'),
     State('tbl2', 'columns')])
def select_ca(n_clicks, type_of_ca, data, cols):

    if n_clicks > 0:

        if type_of_ca == "Dividends":
            
            # Create the data frame
            df = pd.DataFrame(data, columns=[ c['name'] for c in cols])
            df.columns = [dict_div_rename[type_of_ca][i] for i in df.columns]
            select_ids = df['fica000007'][df['fica000007'] != ""].dropna()
            if len(select_ids) == 1:
                select_ids = "(" + str(select_ids.tolist()[0]) + ")"
            else:
                select_ids = tuple(select_ids)
            
            # New Backend (POSTGRES)
            newbackend_ca_db = psycopg2.connect(host = "db-dev-cluster.cdv9yi5xuzxq.eu-west-3.rds.amazonaws.com",
                                                database = "corporate actions",
                                                user = "postgres",
                                                password = "934m$b&QnCrk")
            
            # Get information
            dict_temp = dict(zip(list(dict_div_rename[type_of_ca].values()),list(dict_div_rename[type_of_ca].keys())))
            df_get_info = pd.read_sql_query(f'SELECT * FROM dividends WHERE fica000007 in {select_ids}', newbackend_ca_db)[list(dict_temp.keys())]
            df_get_info.columns = [dict_temp[i] for i in df_get_info.columns]
            
            # Return
            return df_get_info.to_dict('records')

        else:

            # Create the data frame
            df = pd.DataFrame(data, columns=[ c['name'] for c in cols])
            df.columns = [dict_div_rename[type_of_ca][i] for i in df.columns]
            select_ids = df['fica000007'][df['fica000007'] != ""].dropna()
            if len(select_ids) == 1:
                select_ids = "(" + str(select_ids.tolist()[0]) + ")"
            else:
                select_ids = tuple(select_ids)

            # New Backend (POSTGRES)
            newbackend_ca_db = psycopg2.connect(host = "db-dev-cluster.cdv9yi5xuzxq.eu-west-3.rds.amazonaws.com",
                                                database = "corporate actions",
                                                user = "postgres",
                                                password = "934m$b&QnCrk")
            
            # Get information
            dict_temp = dict(zip(list(dict_div_rename[type_of_ca].values()),list(dict_div_rename[type_of_ca].keys())))
            
            # Corporate Action Rows
            df_ca_rows = pd.read_sql_query(f'SELECT * FROM corporate_action_rows WHERE fica000007 in {select_ids}',
                                            newbackend_ca_db)
            df_ca_rows = df_ca_rows[[i for i in df_ca_rows.columns if i in list(dict_temp.keys())]]
            
            # Corporate Action Data
            df_ca_data = pd.read_sql_query(f'SELECT * FROM corporate_action_data WHERE fica000007 in {select_ids}',
                                            newbackend_ca_db)
            df_ca_data = df_ca_data.pivot(columns='fica000009',index="fica000007").reset_index()
            df_ca_data.index = df_ca_data['fica000007']
            df_ca_data = df_ca_data.drop('fica000007',axis=1)
            df_ca_data.columns = [i[1] for i in df_ca_data.columns]
            df_ca_data = df_ca_data.reset_index()

            # Merge
            df_get_info = pd.merge(df_ca_rows,
                                   df_ca_data,
                                   how = 'left',
                                   on = 'fica000007')
            
            # Include additional columns which are not included
            for each_key in list(dict_temp.keys()):
                if each_key not in df_get_info.columns:
                    df_get_info[each_key] = ""

            # Change columns
            df_get_info.columns = [dict_temp[i] for i in df_get_info.columns]
        
    else:

        # Create the data frame
        df = pd.DataFrame(data, columns=[ c['name'] for c in cols])
        df = df.drop('If modification id',axis=1)
        df_get_info = df.copy()

    return df_get_info.to_dict('records')

# --------
# Callback: Update 
# --------
@app.callback(
    Output('tbl-text-status2', 'children'),
    Input('tbl-button-exec_update', 'n_clicks'),
    Input('type_corp_act_2', 'value'),
    [State('tbl2', 'data'),
     State('tbl2', 'columns')])
def update_ca(n_clicks, type_of_ca, data, cols):

    if n_clicks > 0:

        if type_of_ca == 'Dividends':
            
            # Create the data frame
            df = pd.DataFrame(data, columns=[ c['name'] for c in cols])
            df = df.drop(['Corporate Action Status'],axis=1)
            df.columns = [dict_div_rename[type_of_ca][i] for i in df.columns]
            df['ficad00000'] = "M"

            # Type of corporate actions
            df['fica000004'] = "1"

            # Timestamp
            datetime_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.000")
            df['fica000008'] = datetime_now
            
            # Divide the data frame between:
            # Update
            df_modified = df.copy()            
            df_modified = df_modified.astype(str)
            
            # Conditional
            if len(df_modified) > 0:
            
                # Update
                list_update = [(str(i[1]).strip() if isinstance(i[1],int) else i[1].strip(),
                                int(i[2].strip()) if isinstance(i[2],str) else int(i[2]),
                                str(i[3]).strip() if isinstance(i[3],int) else i[3].strip(),
                                str(i[4]).strip() if isinstance(i[4],int) else i[4].strip(),
                                str(i[5]).strip() if isinstance(i[5],int) else i[5].strip(),
                                str(i[6]).strip() if isinstance(i[6],int) else i[6].strip(),
                                str(i[7]).strip() if isinstance(i[7],int) else i[7].strip(),
                                str(i[8]).strip() if isinstance(i[8],int) else i[8].strip(),
                                str(i[9]).strip() if isinstance(i[9],int) else i[9].strip(),
                                str(i[10]).strip() if isinstance(i[10],int) else i[10].strip(),
                                float(i[11].replace(",",".").strip()) if isinstance(i[11],str) else float(i[11]),
                                float(i[12].replace(",",".").strip()) if isinstance(i[12],str) else float(i[12]),
                                str(i[13]).strip() if isinstance(i[13],int) else i[13].strip(),
                                str(i[14]).strip() if isinstance(i[14],int) else i[14].strip(),
                                int(i[15].strip()) if isinstance(i[15],str) else int(i[15]),
                                str(i[16]).strip() if isinstance(i[16],int) else i[16].strip(),
                                int(i[0].strip()) if isinstance(i[0],str) else int(i[0])) for i in df_modified.to_numpy()]
                
                # # New Backend (POSTGRES)
                newbackend_ca_db = psycopg2.connect(host = "db-dev-cluster.cdv9yi5xuzxq.eu-west-3.rds.amazonaws.com",
                                                    database = "corporate actions",
                                                    user = "postgres",
                                                    password = "934m$b&QnCrk")
                cursor = newbackend_ca_db.cursor() 
                cursor.executemany('UPDATE dividends'
                                   ' SET ' +  " = %s,".join(df_modified.columns[1:]) + " = %s" +\
                                   ' WHERE fica000007 = %s',
                                   list_update)
                newbackend_ca_db.commit()
                cursor.close()

            text_to_show = "Done"

        else:
            
            # Create the data frame
            df = pd.DataFrame(data, columns=[ c['name'] for c in cols])
            df = df.drop(['Corporate Action Status'],axis=1)
            df.columns = [dict_div_rename[type_of_ca][i] for i in df.columns]
            df['ficad00000'] = "M"

            # Type of corporate actions
            df['fica000004'] = dict_ca_name_n[type_of_ca]

            # Timestamp
            datetime_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.000")
            df['fica000008'] = datetime_now
            
            # Divide the data frame between:
            # Update
            df_modified = df.copy()
            df_modified = df_modified.astype(str)
            
            # Create mandatory fields for corporate action rows
            list_cols_ca_rows = ["ficad00000", "fica000007", "ficad00001", "fica000001", "fica000002", "ficad00003", "fica000005", "fica000004", "fica000008", "fiad00004"]

            # Create corporate_action_rows
            df_ca_rows_upd = df_modified[list_cols_ca_rows]
            
            # Create corporate_action_data
            df_ca_data_upd = df_modified[['fica000007'] + [i for i in df_modified.columns if i not in list_cols_ca_rows]]
            df_ca_data_upd = pd.melt(df_ca_data_upd, id_vars = 'fica000007')
            df_ca_data_upd = df_ca_data_upd.rename(columns={'variable':'fica000009','value':'fica000011'})
            df_ca_data_upd['fica000009'] = df_ca_data_upd['fica000009'].astype(str)
            df_ca_data_upd['fica000011'] = df_ca_data_upd['fica000011'].astype(str)
            
            # Conditional for "corporate_action_rows"
            if len(df_ca_rows_upd) > 0:
            
                # Update
                
                # df_ca_rows_upd.to_excel("df_ca_rows_upd.xlsx")
                list_update = [(str(i[1]).strip() if isinstance(i[1],int) else i[1].strip(),
                                None if i[2]=="nan" else int(i[2].strip()) if isinstance(i[2],str) else int(i[2]),
                                str(i[3]).strip() if isinstance(i[3],int) or isinstance(i[3],float) else i[3].strip(),
                                str(i[4]).strip() if isinstance(i[4],int) or isinstance(i[4],float) else i[4].strip(),
                                None if i[5]=="nan" else str(i[5]).strip() if isinstance(i[5],int) or isinstance(i,float) else i[5].strip(),
                                None if i[6]=="nan" else str(i[6]).strip() if isinstance(i[6],int) or isinstance(i,float) else i[6].strip(),
                                str(i[7]).strip() if isinstance(i[7],int) or isinstance(i[7],float) else i[7].strip(),
                                str(i[8]).strip() if isinstance(i[8],int) or isinstance(i[8],float) else i[8].strip(),
                                str(i[9]).strip() if isinstance(i[9],int) or isinstance(i[9],float) else i[9].strip(),
                                int(i[0].strip()) if isinstance(i[0],str) else int(i[0])) for i in df_ca_rows_upd.to_numpy()]

                
                # # New Backend (POSTGRES)
                newbackend_ca_db = psycopg2.connect(host = "db-dev-cluster.cdv9yi5xuzxq.eu-west-3.rds.amazonaws.com",
                                                    database = "corporate actions",
                                                    user = "postgres",
                                                    password = "934m$b&QnCrk")
                cursor = newbackend_ca_db.cursor() 
                cursor.executemany('UPDATE corporate_action_rows'
                                   ' SET ' +  " = %s,".join(df_ca_rows_upd.columns[1:]) + " = %s" +\
                                   ' WHERE fica000007 = %s',
                                   list_update)
                newbackend_ca_db.commit()
                cursor.close()

            # Conditional for "corporate_action_rows"
            if len(df_ca_data_upd) > 0:
            
                # Update
                
                # df_ca_rows_upd.to_excel("df_ca_rows_upd.xlsx")
                list_update = [(str(i[2]).strip() if isinstance(i[2],int) else i[2].strip(),
                                str(i[1]).strip() if isinstance(i[1],int) else i[1].strip(),
                                int(i[0].strip()) if isinstance(i[0],str) else int(i[0])) for i in df_ca_data_upd.to_numpy()]
                
                # # New Backend (POSTGRES)
                newbackend_ca_db = psycopg2.connect(host = "db-dev-cluster.cdv9yi5xuzxq.eu-west-3.rds.amazonaws.com",
                                                    database = "corporate actions",
                                                    user = "postgres",
                                                    password = "934m$b&QnCrk")
                cursor = newbackend_ca_db.cursor() 
                cursor.executemany('UPDATE corporate_action_data'
                                   ' SET fica000011 = %s' +\
                                   ' WHERE fica000009 = %s and fica000007 = %s',
                                   list_update)
                newbackend_ca_db.commit()
                cursor.close()


            text_to_show = "Done"

    else:
        
        text_to_show = ""
    
    return html.Div([
                    html.H5(text_to_show)
                    ])

# ---------
# Execution
# ---------

if __name__ == '__main__':
    app.run_server(debug=True)
