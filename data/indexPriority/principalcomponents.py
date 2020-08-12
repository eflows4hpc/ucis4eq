#####################################
## Written by Jose Carlos Carrasco 
## 07-10-2019
#####################################
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import pandas as pd
import numpy as np

def pca_feat_select(data_df, v_threshold = 0.99):
    """ PCA Feature Selection
    Principal Component Analysis for Feature Selection

    Parameters
    ----------
    data_df: pd.DataFrame
        data frame containg data
    v_threshold: float
        variance threshold used to select the amount of principal components that collec that amount of variance
    Returns
    -------
    new_feature_df: pd.DataFrame
        data frame containing data with less number of original columns
    """
    pca= PCA(n_components=data_df.shape[1]).fit(data_df)
    cumm_sum_var = pd.Series(pca.explained_variance_ratio_).cumsum()
    var_num = sum(cumm_sum_var < v_threshold) - 1

    rot_mat = pd.DataFrame(pca.components_.T)

    indices_vector = rot_mat.apply( lambda x : any(abs(x[:var_num]) > 1E-1)).tolist()

    new_feature_df = data_df.T.loc[indices_vector].T

    return new_feature_df

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
	

def describe_principal_components(data_y, title, cor_threshold = 0.5, num_components=-1):
    """ Describe principal components
    Describe principal components

    Parameters
    ----------
    data_y: pd.DataFrame
        data frame containg data
    title: str
        title of the plot
    cor_threshold: float
        correlation threshold from which we consider a variable to be highly correlated with a principal component
    num_components: int
        number of components to be returned. Return all if -1

    Returns
    -------
    ax: matplotlib.axes
        matplotliba axes
    general_report: dict
        general report of the principal component visualization
    component_feature: dict
        highest positively and negatively correlated features of each principal component
    """
    pca = PCA(n_components=data_y.shape[1]).fit(data_y.T)

    ## principal components
    pcomp = pca.components_
    pcomp = pcomp.T
    
    ## explained variance (used for viz)
    cumm_sum_var = pd.Series(pca.explained_variance_ratio_).cumsum()
    var_num = sum(cumm_sum_var < 0.99) - 1
    
    correlations_y = np.zeros((data_y.shape[1], pcomp.shape[1]))
    for r in range(data_y.shape[1]):
        for c in range(pcomp.shape[1]):
            correlations_y[r,c] = np.corrcoef(data_y.iloc[:,r], pcomp[:,c])[1,0]

    ## convert to data frame
    correlations_y = pd.DataFrame(correlations_y)
    correlations_y.columns = range(pcomp.shape[1])
    correlations_y.index = data_y.columns.values

    ## check for each component, which variables have high correlation
    high_cor = correlations_y.apply(func= lambda x: x[x.abs() > cor_threshold])
    
    ## report characteristics of input and principal components
    general_report = dict()
    general_report['obs'] = str(data_y.shape[0])
    general_report['features'] = str(data_y.shape[1])
    general_report['explained_variance'] = pca.explained_variance_ratio_.tolist()
    general_report['cumulative_sum_explained_variance'] = cumm_sum_var.values.tolist()
    
    ## most important features
    selected_features_df = pca_feat_select(data_y)
    general_report['num_features_99_perc_variance'] = selected_features_df.shape[1]
    general_report['features_99_perc_variance'] = selected_features_df.columns.values.tolist()
    
    ## report for each component
    component_feature = dict()
    
    first_n_components = high_cor.shape[1] if num_components == -1 else (num_components if num_components <= high_cor.shape[1] else high_cor.shape[1])
    
    for i in range(first_n_components):
        x =  high_cor.loc[:,i]

        ## drop all NaN from correlations
        important_cors = x[x.notna()]

        #print(important_cors)

        ## get only positive correlations
        positive_cors = important_cors[important_cors > 0]
        highest_pos = positive_cors.sort_values(ascending=False).index[0:3].tolist() if positive_cors.size > 0  else ['']
            
        ## get only negative correlations
        negative_cors = important_cors[important_cors < 0]
        highest_neg = negative_cors.sort_values(ascending=False).index[0:3].tolist() if negative_cors.size > 0 else ['']
        

        component_feature['pc'+str(i)] = {'positive':positive_cors.index.tolist(), 'negative':negative_cors.index.tolist(), 
                                'highest_pos': highest_pos, 
                                'highest_neg': highest_neg}
    
    ## save heatmap
    cmap = sns.diverging_palette(250, 15, s=75, l=40, n=9)
    plt.figure(figsize=(10,6))
    ax = sns.heatmap(correlations_y.iloc[:, :var_num], linewidths=1.0, vmin=-1.0, vmax=1.0, annot=False, cmap=cmap)
    ax.set_title(title)
    plt.tight_layout()
    plt.autoscale()
    plt.show()

    return ax, general_report, component_feature
