# Import modules
from dash import html
import pandas as pd
import numpy as np
import pysftp
import io
import base64
from datetime import datetime
import time
time.clock = time.time

# Import dictionaries
from dict_ca import dict_ca 
from dict_ca_types import dict_ca_types
from dict_categories import dict_ca_name_n
from dict_rename_cols import dict_div_rename

# --------------
# Parse Contents
# --------------

def parse_contents_files(contents, filename):

    if contents is not None:

        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        try:
            
            if 'csv' in filename[-3:].lower():
                # CSV file
                io_obj = io.StringIO(decoded.decode('utf-8'))
                
            elif 'xlsx' in filename[-4:].lower():
                # Excel file
                io_obj = io.BytesIO(decoded)

            elif 'pdf' in filename[-3:].lower():
                # pdf file
                io_obj = io.BytesIO(decoded)

            elif 'png' in filename[-3:].lower():
                # pdf file
                io_obj = io.BytesIO(decoded)

            elif 'docx' in filename[-4:].lower():
                # pdf file
                io_obj = io.BytesIO(decoded)
                
        except:
            
            io_obj = io.StringIO("Error")
    
        return io_obj

# --------------------------------
# Function to upload files to SFTP
# --------------------------------

def upload_files_to_sftp(file,filename_initial,filename_mod):

    # Connection Credentials.
    host="13.36.102.82"
    port=22
    username="fundiftp9A5"
    password="Y2xwPSWv6v"
    
    # Connection to sftp server
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    conn = pysftp.Connection(host = host,
                             username = username,
                             password = password,
                             cnopts = cnopts,
                             port = port)
    
    io_obj = parse_contents_files(file, filename_initial)    
    
    file_extension = filename_initial.split(".")[-1]
    
    try:
        conn.putfo(io_obj, "corporate-action/" + filename_mod + "." + file_extension)
        status_upload = "Done"
        
    except:
        status_upload = "Error"        
    
    return status_upload

# --------------------------------
# Function to upload files to SFTP
# --------------------------------

def parse_contents(filename):

    return html.Div([
                    html.H5(filename)
                    ])

# --------------------------------
# status_pdf
# --------------------------------

def status_pdf(filename):
    return html.Div([
                    html.H5(filename)
                    ])
