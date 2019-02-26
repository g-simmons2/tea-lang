from .ast import *
from .dataset import Dataset
from .evaluate_data_structures import VarData, CombinedData, ResData # runtime data structures
from .evaluate_helper_methods import assign_roles, compute_data_properties, compute_combined_data_properties, execute_test

import attr
from typing import Any
from types import SimpleNamespace # allows for dot notation access for dictionaries

from scipy import stats # Stats library used
import statsmodels.api as sm
import statsmodels.formula.api as smf
import numpy as np # Use some stats from numpy instead
import pandas as pd
# import bootstrapped as bs

# TODO: Pass effect size and alpha values as part of experimental design -- these are used to optimize for power
# TODO: Pass participant_id as part of experimental design, not load_data
def evaluate(dataset: Dataset, expr: Node, design: Dict[str, str]=None):
    if isinstance(expr, Variable):
        dataframe = dataset[expr.name] # I don't know if we want this. We may want to just store query (in metadata?) and
        # then use query to get raw data later....(for user, not interpreter?)
        metadata = dataset.get_variable_data(expr.name) # (dtype, categories)
        if expr.name == 'strategy':
            import pdb; pdb.set_trace()
        metadata['var_name'] = expr.name
        metadata['query'] = ''
        return VarData(metadata)

    elif isinstance(expr, Literal):
        data = pd.Series([expr.value] * len(dataset.data), index=dataset.data.index) # Series filled with literal value
        # metadata = None # metadata=None means literal
        metadata = dict() # metadata=None means literal
        metadata['var_name'] = '' # because not a var in the dataset 
        metadata['query'] = ''
        metadata['value'] = expr.value
        return VarData(data, metadata)

    elif isinstance(expr, Equal):
        lhs = evaluate(dataset, expr.lhs)
        rhs = evaluate(dataset, expr.rhs)
        assert isinstance(lhs, VarData)
        assert isinstance(rhs, VarData)
        
        
        dataframe = lhs.dataframe[lhs.dataframe == rhs.dataframe]
        metadata = lhs.metadata
        if (isinstance(expr.rhs, Literal)):
            metadata['query'] = f" == \'{rhs.metadata['value']}\'" # override lhs metadata for query
        elif (isinstance(expr.rhs, Variable)): 
            metadata['query'] = f" == {rhs.metadata['var_name']}"
        else: 
            raise ValueError(f"Not implemented for {rhs}")
        
        return VarData(metadata)

    elif isinstance(expr, NotEqual): 
        rhs = evaluate(dataset, expr.rhs)
        lhs = evaluate(dataset, expr.lhs)
        assert isinstance(rhs, VarData)
        assert isinstance(lhs, VarData)
        
        dataframe = lhs.dataframe[lhs.dataframe != rhs.dataframe]
        metadata = lhs.metadata
        if (isinstance(expr.rhs, Literal)):
            metadata['query'] = " != \'\'" # override lhs metadata for query
        elif (isinstance(expr.rhs, Variable)): 
            metadata['query'] = f" != {rhs.metadata['var_name']}"
        else: 
            raise ValueError(f"Not implemented for {rhs}")
        return VarData(metadata)

    elif isinstance(expr, LessThan):
        lhs = evaluate(dataset, expr.lhs)
        rhs = evaluate(dataset, expr.rhs)
        assert isinstance(lhs, VarData)
        assert isinstance(rhs, VarData)

        dataframe = None
        metadata = rhs.metadata
        
        if (not lhs.metadata):
            raise ValueError('Malformed Relation. Filter on Variables must have variable as rhs')
        elif (lhs.metadata['dtype'] is DataType.NOMINAL):
            raise ValueError('Cannot compare nominal values with Less Than')
        elif (lhs.metadata['dtype'] is DataType.ORDINAL):
            # TODO May want to add a case should RHS and LHS both be variables
            # assert (rhs.metadata is None) 
            comparison = rhs.dataframe.iloc[0]
            if (isinstance(comparison, str)):
                categories = lhs.metadata['categories'] # OrderedDict
                # Get raw Pandas Series indices for desired data
                ids  = [i for i,x in enumerate(lhs.dataframe) if categories[x] < categories[comparison]]
                # Get Pandas Series set indices for desired data
                p_ids = [lhs.dataframe.index.values[i] for i in ids]
                # Create new Pandas Series with only the desired data, using set indices
                dataframe = pd.Series(lhs.dataframe, p_ids)
                dataframe.index.name = dataset.pid_col_name
                
            elif (np.issubdtype(comparison, np.integer)):
                categories = lhs.metadata['categories'] # OrderedDict
                # Get raw Pandas Series indices for desired data
                ids  = [i for i,x in enumerate(lhs.dataframe) if categories[x] < comparison]
                # Get Pandas Series set indices for desired data
                p_ids = [lhs.dataframe.index.values[i] for i in ids]
                # Create new Pandas Series with only the desired data, using set indices
                dataframe = pd.Series(lhs.dataframe, p_ids)
                dataframe.index.name = dataset.pid_col_name                

            else: 
                raise ValueError(f"Cannot compare ORDINAL variables to {type(rhs.dataframe.iloc[0])}")


        elif (lhs.metadata['dtype'] is DataType.INTERVAL or lhs.metadata['dtype'] is DataType.RATIO):
            comparison = rhs.dataframe.iloc[0]
             # Get raw Pandas Series indices for desired data
            ids  = [i for i,x in enumerate(lhs.dataframe) if x < comparison]
            # Get Pandas Series set indices for desired data
            p_ids = [lhs.dataframe.index.values[i] for i in ids]
            # Create new Pandas Series with only the desired data, using set indices
            dataframe = pd.Series(lhs.dataframe, p_ids)
            dataframe.index.name = dataset.pid_col_name   

        else:
            raise Exception(f"Invalid Less Than Operation:{lhs} < {rhs}")

        if (isinstance(expr.rhs, Literal)):
            metadata['query'] = " < \'\'" # override lhs metadata for query
        elif (isinstance(expr.rhs, Variable)): 
            metadata['query'] = f" < {rhs.metadata['var_name']}"
        else: 
            raise ValueError(f"Not implemented for {rhs}")
        return VarData(metadata)

    elif isinstance(expr, LessThanEqual):
        lhs = evaluate(dataset, expr.lhs)
        rhs = evaluate(dataset, expr.rhs)
        assert isinstance(lhs, VarData)
        assert isinstance(rhs, VarData)


        dataframe = None
        metadata = rhs.metadata
        
        if (not lhs.metadata):
            raise ValueError('Malformed Relation. Filter on Variables must have variable as rhs')
        elif (lhs.metadata['dtype'] is DataType.NOMINAL):
            raise ValueError('Cannot compare nominal values with Less Than')
        elif (lhs.metadata['dtype'] is DataType.ORDINAL):
            # TODO May want to add a case should RHS and LHS both be variables
            # assert (rhs.metadata is None)
            comparison = rhs.dataframe.iloc[0]
            if (isinstance(comparison, str)):
                categories = lhs.metadata['categories'] # OrderedDict
                # Get raw Pandas Series indices for desired data
                ids  = [i for i,x in enumerate(lhs.dataframe) if categories[x] <= categories[comparison]]
                # Get Pandas Series set indices for desired data
                p_ids = [lhs.dataframe.index.values[i] for i in ids]
                # Create new Pandas Series with only the desired data, using set indices
                dataframe = pd.Series(lhs.dataframe, p_ids)
                dataframe.index.name = dataset.pid_col_name
                
            elif (np.issubdtype(comparison, np.integer)):
                categories = lhs.metadata['categories'] # OrderedDict
                # Get raw Pandas Series indices for desired data
                ids  = [i for i,x in enumerate(lhs.dataframe) if categories[x] <= comparison]
                # Get Pandas Series set indices for desired data
                p_ids = [lhs.dataframe.index.values[i] for i in ids]
                # Create new Pandas Series with only the desired data, using set indices
                dataframe = pd.Series(lhs.dataframe, p_ids)
                dataframe.index.name = dataset.pid_col_name                

            else: 
                raise ValueError(f"Cannot compare ORDINAL variables to {type(rhs.dataframe.iloc[0])}")


        elif (lhs.metadata['dtype'] is DataType.INTERVAL or lhs.metadata['dtype'] is DataType.RATIO):
            comparison = rhs.dataframe.iloc[0]
             # Get raw Pandas Series indices for desired data
            ids  = [i for i,x in enumerate(lhs.dataframe) if x <= comparison]
            # Get Pandas Series set indices for desired data
            p_ids = [lhs.dataframe.index.values[i] for i in ids]
            # Create new Pandas Series with only the desired data, using set indices
            dataframe = pd.Series(lhs.dataframe, p_ids)
            dataframe.index.name = dataset.pid_col_name   

        else:
            raise Exception(f"Invalid Less Than Equal Operation:{lhs} <= {rhs}")


        if (isinstance(expr.rhs, Literal)):
            metadata['query'] = " <= \'\'" # override lhs metadata for query
        elif (isinstance(expr.rhs, Variable)): 
            metadata['query'] = f" <= {rhs.metadata['var_name']}"
        else: 
            raise ValueError(f"Not implemented for {rhs}")

        return VarData(metadata)
    
    elif isinstance(expr, GreaterThan):
        lhs = evaluate(dataset, expr.lhs)
        rhs = evaluate(dataset, expr.rhs)
        assert isinstance(lhs, VarData)
        assert isinstance(rhs, VarData)


        dataframe = None
        metadata = rhs.metadata
        
        if (not lhs.metadata):
            raise ValueError('Malformed Relation. Filter on Variables must have variable as rhs')
        elif (lhs.metadata['dtype'] is DataType.NOMINAL):
            raise ValueError('Cannot compare nominal values with Greater Than')
        elif (lhs.metadata['dtype'] is DataType.ORDINAL):
            # TODO May want to add a case should RHS and LHS both be variables
            # assert (rhs.metadata is None) 
            comparison = rhs.dataframe.iloc[0]
            if (isinstance(comparison, str)):
                categories = lhs.metadata['categories'] # OrderedDict
                # Get raw Pandas Series indices for desired data
                ids  = [i for i,x in enumerate(lhs.dataframe) if categories[x] > categories[comparison]]
                # Get Pandas Series set indices for desired data
                p_ids = [lhs.dataframe.index.values[i] for i in ids]
                # Create new Pandas Series with only the desired data, using set indices
                dataframe = pd.Series(lhs.dataframe, p_ids)
                dataframe.index.name = dataset.pid_col_name
                
            elif (np.issubdtype(comparison, np.integer)):
                categories = lhs.metadata['categories'] # OrderedDict
                # Get raw Pandas Series indices for desired data
                ids  = [i for i,x in enumerate(lhs.dataframe) if categories[x] > comparison]
                # Get Pandas Series set indices for desired data
                p_ids = [lhs.dataframe.index.values[i] for i in ids]
                # Create new Pandas Series with only the desired data, using set indices
                dataframe = pd.Series(lhs.dataframe, p_ids)
                dataframe.index.name = dataset.pid_col_name                

            else: 
                raise ValueError(f"Cannot compare ORDINAL variables to {type(rhs.dataframe.iloc[0])}")


        elif (lhs.metadata['dtype'] is DataType.INTERVAL or lhs.metadata['dtype'] is DataType.RATIO):
            comparison = rhs.dataframe.iloc[0]
             # Get raw Pandas Series indices for desired data
            ids  = [i for i,x in enumerate(lhs.dataframe) if x > comparison]
            # Get Pandas Series set indices for desired data
            p_ids = [lhs.dataframe.index.values[i] for i in ids]
            # Create new Pandas Series with only the desired data, using set indices
            dataframe = pd.Series(lhs.dataframe, p_ids)
            dataframe.index.name = dataset.pid_col_name   

        else:
            raise Exception(f"Invalid Greater Than Operation:{lhs} > {rhs}")

        if (isinstance(expr.rhs, Literal)):
            metadata['query'] = " > \'\'" # override lhs metadata for query
        elif (isinstance(expr.rhs, Variable)): 
            metadata['query'] = f" > {rhs.metadata['var_name']}"
        else: 
            raise ValueError(f"Not implemented for {rhs}")

        return VarData(metadata) 
   
    elif isinstance(expr, GreaterThanEqual):
        lhs = evaluate(dataset, expr.lhs)
        rhs = evaluate(dataset, expr.rhs)
        assert isinstance(lhs, VarData)
        assert isinstance(rhs, VarData)


        dataframe = None
        metadata = rhs.metadata
        
        if (not lhs.metadata):
            raise ValueError('Malformed Relation. Filter on Variables must have variable as rhs')
        elif (lhs.metadata['dtype'] is DataType.NOMINAL):
            raise ValueError('Cannot compare nominal values with Greater Than Equal')
        elif (lhs.metadata['dtype'] is DataType.ORDINAL):
            # TODO May want to add a case should RHS and LHS both be variables
            # assert (rhs.metadata is None) 
            comparison = rhs.dataframe.iloc[0]
            if (isinstance(comparison, str)):
                categories = lhs.metadata['categories'] # OrderedDict
                # Get raw Pandas Series indices for desired data
                ids  = [i for i,x in enumerate(lhs.dataframe) if categories[x] >= categories[comparison]]
                # Get Pandas Series set indices for desired data
                p_ids = [lhs.dataframe.index.values[i] for i in ids]
                # Create new Pandas Series with only the desired data, using set indices
                dataframe = pd.Series(lhs.dataframe, p_ids)
                dataframe.index.name = dataset.pid_col_name
                
            elif (np.issubdtype(comparison, np.integer)):
                categories = lhs.metadata['categories'] # OrderedDict
                # Get raw Pandas Series indices for desired data
                ids  = [i for i,x in enumerate(lhs.dataframe) if categories[x] >= comparison]
                # Get Pandas Series set indices for desired data
                p_ids = [lhs.dataframe.index.values[i] for i in ids]
                # Create new Pandas Series with only the desired data, using set indices
                dataframe = pd.Series(lhs.dataframe, p_ids)
                dataframe.index.name = dataset.pid_col_name                

            else: 
                raise ValueError(f"Cannot compare ORDINAL variables to {type(rhs.dataframe.iloc[0])}")


        elif (lhs.metadata['dtype'] is DataType.INTERVAL or lhs.metadata['dtype'] is DataType.RATIO):
            comparison = rhs.dataframe.iloc[0]
             # Get raw Pandas Series indices for desired data
            ids  = [i for i,x in enumerate(lhs.dataframe) if x >= comparison]
            # Get Pandas Series set indices for desired data
            p_ids = [lhs.dataframe.index.values[i] for i in ids]
            # Create new Pandas Series with only the desired data, using set indices
            dataframe = pd.Series(lhs.dataframe, p_ids)
            dataframe.index.name = dataset.pid_col_name   

        else:
            raise Exception(f"Invalid Greater Than Equal Operation:{lhs} >= {rhs}")


        if (isinstance(expr.rhs, Literal)):
            metadata['query'] = " >= \'\'" # override lhs metadata for query
        elif (isinstance(expr.rhs, Variable)): 
            metadata['query'] = f" >= {rhs.metadata['var_name']}"
        else: 
            raise ValueError(f"Not implemented for {rhs}")
        return VarData(metadata) 

    elif isinstance(expr, Relate):    
        vars = []

        for v in expr.vars: 
            eval_v = evaluate(dataset, v, design)         
            assert isinstance(eval_v, VarData)

            vars.append(eval_v)

        # list of CombinedData objects that contains the data and properties that we are interested in...
        vars = assign_roles(vars, design)
        vars = compute_data_properties(dataset, vars)

        agg = compute_combined_data_properties(dataset, vars, design)
        # data_props = compute_data_properties(dataset, vars, expr.predictions, design) 


        # data_props has the data that is needed (already filtered and ready) for analyses
        import pdb; pdb.set_trace()
        # TODO execute_test needs to be able to handle list of CombinedData 
        # TODO split into find and execute test
        # res_data = execute_test(dataset, data_props, iv, dv, expr.predictions, design) # design contains info about between/within subjects AND Power parameters (alpha, effect size, sample size - which can be calculated)
        res_data = execute_test(dataset, agg) #????
        # return res_data


    elif isinstance(expr, Mean):
        var = evaluate(dataset, expr.var)
        assert isinstance(var, VarData)

        # bs.bootstrap(var.dataframe, stat_func=
        # bs_stats.mean)
        raise Exception('Not implemented Mean')