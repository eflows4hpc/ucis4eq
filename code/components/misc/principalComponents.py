#!/usr/bin/env python3

# Encode and parse the query string params
# This module is part of the Automatic Alert System (AAS) solution

# Author:  Jose Carlos Carrasco 
# Contact: jose.carrasco@bsc.es

# ###############################################################################
#       BSD 3-CLAUSE, aka BSD NEW, aka BSD REVISED, aka MODIFIED BSD LICENSE

# Copyright 2023,2024 Jośe Carlos Carrasco

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# 3. Neither the name(s) of the copyright holder(s) nor the name(s) of its
# contributor(s) may be used to endorse or promote products derived from this
# software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND CONTRIBUTOR(S) “AS
# IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S) OR CONTRIBUTOR(S) BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# ###############################################################################
# Module imports
from sklearn.decomposition import PCA
import pandas as pd
import numpy as np

# ###############################################################################
# Methods and classes

def extract_pca_components(data_df, num_components=None, var_threshold=0.99):
    """ Extract PCA components
    Extract principal components from PCA

    Parameters
    ----------
    data_df: pd.DataFrame
        data frame containg data
    num_components: int
        number of components to be returned
    
    Returns
    -------
    pcomp: pd.DataFrame
        data frame with selected number of principal components
    """
    
    print('entre_a_PCA')
    pca = PCA()
    pca.fit(data_df.T)
	
    pcomp = pca.components_
    pcomp = pcomp.T # take transopose in order to get as (n_features, n_components)
	
    if num_components is None:
    	num_components = pd.Series(pca.explained_variance_ratio_).cumsum()
    	num_components = num_components[num_components < var_threshold].size
	
    pcomp = pd.DataFrame(pcomp[:,:num_components])
    pcomp.index = data_df.index
	
    return pcomp
