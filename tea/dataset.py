from .ast import Variable, DataType

import attr
import pandas as pd
import os
import csv
from typing import Dict
from pathlib import Path
from urllib.parse import urlparse
import requests

BASE_PATH = os.getcwd()

def _dir_exists(path):
    return os.path.isdir(path) and os.path.exists(path)

@attr.s(hash=True)
class Dataset(object): 
    dfile = attr.ib() # path name 
    variables = attr.ib() # list of Variable objects <-- TODO: may not need this in new implementation....
    pid_col_name = attr.ib() # name of column in pandas DataFrame that has participant ids
    row_pids = attr.ib(init=False) # list of unique participant ids
    data = attr.ib(init=False) # pandas DataFrame
    
    @staticmethod
    def load(path, name):
        home = Path.home()
        tea_path = home / '.tea'
        if not _dir_exists(tea_path):
            os.mkdir(tea_path)
        data_path = tea_path / 'data'
        if not _dir_exists(data_path):
            os.mkdir(data_path)
        
        url = urlparse(path)
        csv_name = name if '.csv' in name else str(name + '.csv')
        csv_path = data_path / csv_name

        # URL
        if url.scheme != '':
            data = requests.get(path)

            with open(csv_path, 'w') as f:
                writer = csv.writer(f)
                reader = csv.reader(data.text.splitlines())

                for row in reader:
                    writer.writerow(row)
                # import pdb; pdb.set_trace()
        else: 
            with open(path, 'r') as readfile: 
                import pdb; pdb.set_trace()
                reader = csv.reader(readfile)
                with open(csv_path, 'w') as writefile:
                    writer = csv.writer(writefile)

                    for row in reader:
                        writer.writerow(row)

        

    def __attrs_post_init__(self): 
        if self.dfile: 
            self.data = pd.read_csv(self.dfile)

        # Reindex DataFrame indices to be pids
        self.data.set_index(self.pid_col_name, inplace=True)

    @classmethod
    def from_arr_numeric(cls, y: list, x: list):

        data = {'X': x, 'Y': y}
        df = pd.DataFrame.from_dict(data)

        x_var = Variable('X', dtype=DataType.INTERVAL, categories=None, drange=None)
        y_var = Variable('Y', dtype=DataType.INTERVAL, categories=None, drange=None)

        return cls(dfile='', variables=[x_var,y_var], data=df)

    
    def __getitem__(self, var_name: str):
        for v in self.variables: # checks that the Variable is known to the Dataset object
            if v.name == var_name: 
                return self.data[var_name] # returns the data, not the variable object

    def get_variable_data(self, var_name: str):
        for v in self.variables: 
            if v.name == var_name:
                return { 'dtype': v.dtype, 
                        'categories': v.categories} 


    # SQL style select
    def select(self, col: str, where: list = None):
        # TODO should check that the query is valid (no typos, etc.) before build

        def build_query(where: list):
            query = ''

            #build up query based on where clauses 
            for i, e in enumerate(where):
                query += e
                
                if (i+1 < len(where)):
                    query += '&'
            return query

        df = self.data
        if where: # not None
            query = build_query(where)
            res = df.query(query)[col] # makes a copy
        else: 
            res = df[col]

        return res