from numba import jit, prange
import numpy as np
from scipy.stats import linregress
from dash import dcc

import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.neighbors import KernelDensity
import matplotlib.pylab as plt
from scipy.optimize import minimize
from scipy.linalg import block_diag
from sklearn.covariance import LedoitWolf
from sklearn.metrics import mutual_info_score, log_loss
import numpy as np,scipy.stats as ss
from sklearn.model_selection import KFold, RepeatedKFold
from sklearn.metrics import silhouette_samples
import numpy as np,pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from joblib import Parallel, delayed
from itertools import combinations
from sklearn.model_selection import StratifiedKFold, TimeSeriesSplit
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score, mean_squared_error

@jit(nopython=True, cache=True)
def ols_regression(y, X):
    n, k = X.shape

    # Compute OLS coefficients
    beta = np.linalg.inv(X.T @ X) @ X.T @ y

    # Compute residuals
    e = y - X @ beta

    # Residual sum of squares
    RSS = np.sum(e**2)

    # Degrees of freedom
    dof = n - k

    # Residual standard error
    RSE = np.sqrt(RSS / dof)

    # Covariance matrix of beta
    cov_beta = np.linalg.inv(X.T @ X) * RSE**2

    # Standard errors of coefficients
    se_beta = np.sqrt(np.diag(cov_beta))

    # t-values
    t_values = beta / se_beta

    return beta, se_beta, t_values

@jit(nopython=True, cache=True)
def tValLinR(close):
    n = close.shape[0]
    X = np.column_stack((np.ones(n), np.arange(n)))
    y = close.astype(np.float64)  # Convert to native type for Numba compatibility

    # Perform OLS regression
    beta, se_beta, t_values = ols_regression(y, X)
    slope = beta[1]
    return t_values[1], slope  # Return t-value for the second coefficient (excluding intercept)


@jit(nopython=True, cache=True)
def getBinsFromTrend(close,span,threshold,slope_threshold):
    '''
    Derive labels from the sign of t-value of linear trend
    Output includes:
    - t1: End time for the identified trend
    - tVal: t-value associated with the estimated trend coefficient - bin: Sign of the trend
    '''
    max_length = len(close)
    hrzns=prange(*span)
    out= np.zeros(max_length)
    t_values= np.zeros(max_length)
    slopes = np.zeros(max_length)
    for idx in prange(max_length):
        if idx+max(hrzns)>max_length:continue
        max_tvalue = -np.inf
        selected_tvalue=0
        best_t_val = 0.0
        best_slope = 0.0
        for hrzn in hrzns: 
            end_idx = hrzn+idx
            t_value, slope =tValLinR(close[idx:end_idx])
            if np.isinf(t_value) or np.isnan(t_value):
                t_value=0
                slope=0
            abs_tvalue =  abs(t_value)
            max_tvalue = max(abs_tvalue, max_tvalue)
            if max_tvalue ==abs_tvalue and abs_tvalue>=threshold and slope_threshold <=abs(slope):
                selected_tvalue=end_idx*np.sign(t_value)
                best_t_val = t_value
                best_slope = slope

        out[idx] = selected_tvalue
        t_values[idx] = best_t_val
        slopes[idx] =best_slope
    return out, t_values, slopes

def find_graph(component):
    if isinstance(component, dcc.Graph):
        return component.figure
    if hasattr(component, "children"):
        children = component.children
        if isinstance(children, list):
            for child in children:
                result = find_graph(child)
                if result:
                    return result
        else:
            return find_graph(children)
    return None



def mpPDF(var, q, pts):
    eMin, eMax = var*(1-(1./q)**.5)**2, var*(1+(1./q)**.5)**2 # calc lambda_minus, lambda_plus
    eVal = np.linspace(eMin, eMax, pts) #Return evenly spaced numbers over a specified interval. eVal='lambda'
    #Note: 1.0/2*2 = 1.0 not 0.25=1.0/(2*2)
    pdf = q/(2*np.pi*var*eVal)*((eMax-eVal)*(eVal-eMin))**.5 #np.allclose(np.flip((eMax-eVal)), (eVal-eMin))==True
    pdf = pd.Series(pdf, index=eVal)
    return pdf

def getPCA(matrix, column_names=None):
    """
    Perform PCA on the given matrix and return sorted eigenvalues, eigenvectors,
    and optionally sorted column names.
    
    Parameters:
    - matrix (np.ndarray): The input Hermitian matrix for PCA.
    - column_names (list or np.ndarray, optional): Column names corresponding to the input matrix.
    
    Returns:
    - eVal (np.ndarray): Diagonal matrix of sorted eigenvalues.
    - eVec (np.ndarray): Matrix of sorted eigenvectors.
    - sorted_column_names (list): Column names sorted to align with eigenvalues (if provided).
    """
    # Get eigenvalues and eigenvectors
    eVal, eVec = np.linalg.eig(matrix)
    
    # Sort indices by eigenvalues in descending order
    indices = eVal.argsort()[::-1]
    
    # Sort eigenvalues and eigenvectors
    eVal = eVal[indices]
    eVec = eVec[:, indices]
    eVal = np.diagflat(eVal)  # Convert to diagonal matrix
    
    # Sort column names if provided
    sorted_column_names = None
    if column_names is not None:
        sorted_column_names = np.array(column_names)[indices]
        sorted_column_names = sorted_column_names.tolist()  # Convert back to a list if necessary
    
    if column_names is not None:
        return eVal, eVec, sorted_column_names
    return eVal, eVec
    
def fitKDE(obs, bWidth=.15, kernel='gaussian', x=None):
    if len(obs.shape) == 1: obs = obs.reshape(-1,1)
    kde = KernelDensity(kernel = kernel, bandwidth = bWidth).fit(obs)
    if x is None: x = np.unique(obs).reshape(-1,1)
    if len(x.shape) == 1: x = x.reshape(-1,1)
    logProb = kde.score_samples(x) # log(density)
    pdf = pd.Series(np.exp(logProb), index=x.flatten())
    return pdf

def getRndCov(nCols, nFacts): #nFacts - contains signal out of nCols
    w = np.random.normal(size=(nCols, nFacts))
    cov = np.dot(w, w.T) #random cov matrix, however not full rank
    cov += np.diag(np.random.uniform(size=nCols)) #full rank cov
    return cov

def cov2corr(cov):
    # Derive the correlation matrix from a covariance matrix
    std = np.sqrt(np.diag(cov))
    corr = cov/np.outer(std,std)
    corr[corr<-1], corr[corr>1] = -1,1 #for numerical errors
    return corr
    
def corr2cov(corr, std):
    cov = corr * np.outer(std, std)
    return cov     
    
#snippet 2.4 - fitting the marcenko-pastur pdf - find variance
#Fit error
def errPDFs(var, eVal, q, bWidth, pts=1000):
    var = var[0]
    pdf0 = mpPDF(var, q, pts) #theoretical pdf
    pdf1 = fitKDE(eVal, bWidth, x=pdf0.index.values) #empirical pdf
    sse = np.sum((pdf1-pdf0)**2)
    return sse 

def findMaxEval(eVal, q, bWidth):
    out = minimize(lambda *x: errPDFs(*x), x0=np.array(0.5), args=(eVal, q, bWidth), bounds=((1E-5, 1-1E-5),))
    if out['success']: var = out['x'][0]
    else: var=1
    eMax = var*(1+(1./q)**.5)**2
    return eMax, var

def denoisedCorr(eVal, eVec, nFacts ):
    eVal_ = np.diag(eVal).copy()
    eVal_[nFacts:] = eVal_[nFacts:].sum()/float(eVal_.shape[0] - nFacts) #all but 0..i values equals (1/N-i)sum(eVal_[i..N]))
    eVal_ = np.diag(eVal_) #square matrix with eigenvalues as diagonal: eVal_.I
    corr1 = np.dot(eVec, eVal_).dot(eVec.T) #Eigendecomposition of a symmetric matrix: S = QΛQT
    corr1 = cov2corr(corr1) # Rescaling the correlation matrix to have 1s on the main diagonal
    return corr1

def detoned_corr(corr, eigenvalues, eigenvectors, market_component=1):
    """
    De-tones the de-noised correlation matrix by removing the market component.
    The input is the eigenvalues and the eigenvectors of the correlation matrix and the number
    of the first eigenvalue that is above the maximum theoretical eigenvalue and the number of
    eigenvectors related to a market component.
    :param corr: (np.array) Correlation matrix to detone.
    :param eigenvalues: (np.array) Matrix with eigenvalues on the main diagonal.
    :param eigenvectors: (float) Eigenvectors array.
    :param market_component: (int) Number of fist eigevectors related to a market component. (1 by default)
    :return: (np.array) De-toned correlation matrix.
    """
    
    # Getting the eigenvalues and eigenvectors related to market component
    eigenvalues_mark = eigenvalues[:market_component, :market_component]
    eigenvectors_mark = eigenvectors[:, :market_component]
    
    # Calculating the market component correlation
    corr_mark = np.dot(eigenvectors_mark, eigenvalues_mark).dot(eigenvectors_mark.T)
    
    # Removing the market component from the de-noised correlation matrix
    corr = corr - corr_mark
    
    # Rescaling the correlation matrix to have 1s on the main diagonal
    corr = cov2corr(corr)
    
    return corr
            
def numBins(nObs,corr=None):
# Optimal number of bins for discretization 
    if corr is None: # univariate case
        z=(8+324*nObs+12*(36*nObs+729*nObs**2)**.5)**(1/3.)
        b=round(z/6.+2./(3*z)+1./3) 
    else: # bivariate case
        if (1.-corr**2)==0:
            corr = np.sign(corr)*(np.abs(corr)-1e-5)  
        b=2**-.5*(1+(1+24*nObs/(1.-corr**2))**.5)**.5

        if not np.isfinite(b):
            return 2
        return min(max(2, int(round(b))), 2056)
#--------------------------------------------------- 
def varInfo_optBIn(x,y,norm=False): # Discretized and with optimal bin value
    # variation of information
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if len(x) == 0 or len(y) == 0:
        return 1
    corr = np.corrcoef(x, y)[0, 1]
    bXY = numBins(x.shape[0], corr=corr)

    cXY = np.histogram2d(x, y, bXY)[0]
    iXY = mutual_info_score(None, None, contingency=cXY)
    hX = ss.entropy(np.histogram(x, bXY)[0])  # marginal
    hY = ss.entropy(np.histogram(y, bXY)[0])  # marginal
    vXY = hX + hY - 2 * iXY  # variation of information
    if norm:
        hXY = hX + hY - iXY  # joint
        vXY /= hXY  # normalized variation of information
    return vXY


def varInfo_matrix(df, norm=True, n_jobs=-1):
    """
    Compute a matrix of variation of information (varInfo) for all column pairs
    using NumPy arrays only to reduce RAM usage.
    """
    columns = df.columns
    vi_matrix = pd.DataFrame(index=columns, columns=columns)

    def compute_vi(col1, col2):
        df_temp = df[[col1, col2]].dropna()
        x = df_temp[col1].values
        y = df_temp[col2].values
        vXY = varInfo_optBIn(x=x, y=y, norm=norm)
        return col1, col2, vXY

    pairs = list(combinations(columns, 2))
    results = Parallel(n_jobs=n_jobs)(
        delayed(compute_vi)(col1, col2) for col1, col2 in tqdm(pairs, desc="Computing VI matrix (parallel)")
    )

    for col1, col2, vXY in results:
        vi_matrix.loc[col1, col2] = vXY
        vi_matrix.loc[col2, col1] = vXY

    np.fill_diagonal(vi_matrix.values, 0.0)
    return vi_matrix


def get_eVec(dot, varThres):
    """
    compute eVec from dot prod matrix, reduce dimension
    :params dot:
    :params varThres:
    :return
        + eVal: eigen values
        + eVec: eigen vectors
    """
    #1) compute eVec and eVal from dot
    eVal, eVec = np.linalg.eigh(dot)
    idx = eVal.argsort()[ : :-1] # arguments for sorting eVal desc
    eVal, eVec = eVal[idx], eVec[ : , idx]
    #2) only positive eVals
    # eigen values are put into a pd.series, rank from most important to the least important
    eVal = pd.Series(eVal, index = ['PC_' + str(i + 1) for i in range(eVal.shape[0])])
    # eigen vectors are put into a pd.df, index = dot, columns = eVal
    eVec = pd.DataFrame(eVec, index = dot.index, columns = eVal.index)
    # ? in case there are additional columns, discard them all
    eVec = eVec.loc[:, eVal.index]
    #3) reduce dimension, form PCs
    # calculate and standardise the cumsum of the eval
    cumVar = eVal.cumsum() / eVal.sum()  
    # find the index of last cumsum that < varThres
    dim = cumVar.values.searchsorted(varThres)
    # [0: dim] are the eVal and eVec important
    eVal, eVec = eVal.iloc[: dim + 1], eVec.iloc[ : , : dim + 1]
    return eVal, eVec

def orthoFeats(dfX, varThres = .95):
    """
    Given a dataframe dfX of features, compute orthofeatures dfP
    :params dfX: pd.df, features
    :params varThres: float, threshold to select the significant Principal components

    :return
        dfP: pd.df, orthofeatures
    """
    # standardized features
    dfZ = dfX.sub(dfX.mean(), axis = 1).div(dfX.std(), axis = 1)
    # calculate the ZZ`(dot)
    dot = pd.DataFrame(np.dot(dfZ.T, dfZ), index = dfX.columns, columns = dfX.columns)
    # find the (significant) eVal and eVec
    eVal, eVec = get_eVec(dot, varThres)
    # get the orthofeatures
    dfP = np.dot(dfZ, eVec)
    return dfP


def groupMeanStd(df0,clstrs):
    out=pd.DataFrame(columns=['mean','std'])
    for i,j in clstrs.items(): 
        df1=df0[j].sum(axis=1)
        out.loc['C_'+str(i),'mean']=df1.mean()
        out.loc['C_'+str(i),'std']=df1.std()*df1.shape[0]**-.5
    
    return out


def featImpMDI_Clustered(fit,featNames,clstrs): 
    df0={i:tree.feature_importances_ for i,tree in  enumerate(fit.estimators_)} 
    df0=pd.DataFrame.from_dict(df0,orient='index') 
    df0.columns=featNames 
    df0=df0.replace(0,np.nan) # because max_features=1     
    imp=groupMeanStd(df0,clstrs) 
    imp/=imp['mean'].sum()
    return imp



def featImpMDA_Clustered(clf, X, y, clstrs, n_splits=10, n_jobs=-1, random_state=42, eps=1e-15):
    y = pd.Series(y).values.ravel()
    labels_target = np.array([0, 1, 2])
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    cvGen = list(skf.split(X=X, y=y))

    def align_proba(proba, classes_):
        df = pd.DataFrame(proba, columns=list(classes_))
        df = df.reindex(columns=labels_target, fill_value=eps)
        s = df.sum(axis=1).replace(0.0, 1.0)
        return (df.div(s, axis=0)).values

    def process_fold(i, train, test):
        X0, y0 = X.iloc[train, :], y[train]
        X1, y1 = X.iloc[test, :], y[test]
        fit = clf.fit(X0, y0)
        prob = align_proba(fit.predict_proba(X1), fit.classes_)
        base_score = -log_loss(y1, prob, labels=labels_target)
        row = {}
        for j in clstrs:
            X1_ = X1.copy(deep=True)
            for k in clstrs[j]:
                np.random.shuffle(X1_[k].values)
            prob_j = align_proba(fit.predict_proba(X1_), fit.classes_)
            row[j] = -log_loss(y1, prob_j, labels=labels_target)
        return i, base_score, row

    results = Parallel(n_jobs=n_jobs)(
        delayed(process_fold)(i, tr, te) for i, (tr, te) in enumerate(tqdm(cvGen, desc="MDA Clusters (parallel)"))
    )

    scr0 = pd.Series(index=range(n_splits), dtype=float)
    scr1 = pd.DataFrame(index=range(n_splits), columns=list(clstrs.keys()), dtype=float)
    for i, base_score, row in results:
        scr0.loc[i] = base_score
        for j in row:
            scr1.loc[i, j] = row[j]

    imp = (-1.0 * scr1).add(scr0, axis=0)
    imp = imp / (-1.0 * scr1)
    imp = pd.concat({'mean': imp.mean(), 'std': imp.std() * imp.shape[0] ** -0.5}, axis=1)
    imp.index = ['C_' + str(i) for i in imp.index]
    return imp


def featImpMDA_Clustered_Regression(reg, X, y, clstrs, n_splits=10, n_jobs=-1, random_state=42):
    y = pd.Series(y).values.ravel()
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    cvGen = list(kf.split(X=X, y=y))

    def process_fold(i, train, test):
        X0, y0 = X.iloc[train, :], y[train]
        X1, y1 = X.iloc[test, :], y[test]
        fit = reg.fit(X0, y0)
        pred = fit.predict(X1)
        base_score = -mean_squared_error(y1, pred)
        
        row = {}
        for j in clstrs:
            X1_ = X1.copy(deep=True)
            for k in clstrs[j]:
                vals = X1_[k].values.copy() 
                np.random.shuffle(vals)
                X1_[k] = vals
            
            pred_j = fit.predict(X1_)
            row[j] = -mean_squared_error(y1, pred_j)
        return i, base_score, row

    results = Parallel(n_jobs=n_jobs)(
        delayed(process_fold)(i, tr, te) for i, (tr, te) in enumerate(tqdm(cvGen, desc="MDA Clusters Regression"))
    )

    scr0 = pd.Series(index=range(n_splits), dtype=float)
    scr1 = pd.DataFrame(index=range(n_splits), columns=list(clstrs.keys()), dtype=float)
    
    for i, base_score, row in results:
        scr0.loc[i] = base_score
        for j in row:
            scr1.loc[i, j] = row[j]

    imp = (scr0.values[:, None] - scr1) / np.abs(scr0.values[:, None])

    imp = pd.concat({'mean': imp.mean(), 'std': imp.std() * imp.shape[0] ** -0.5}, axis=1)
    imp.index = ['C_' + str(i) for i in imp.index]
    return imp


def featImpMDA_Repeated_Clustered(reg, X, y, clstrs, n_splits=5, n_repeats=10, n_jobs=-1, random_state=42):
    """
    Repeated K-Fold MDA for stability on small datasets.
    n_splits * n_repeats = total iterations (e.g., 5 * 10 = 50 folds).
    """
    y = pd.Series(y).values.ravel()
    
    # Use RepeatedKFold to stabilize the results
    rkf = RepeatedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=random_state)
    cvGen = list(rkf.split(X=X, y=y))
    total_folds = len(cvGen)

    def process_fold(i, train, test):
        X0, y0 = X.iloc[train, :], y[train]
        X1, y1 = X.iloc[test, :], y[test]
        
        # Fit the regressor
        fit = reg.fit(X0, y0)
        
        # Base Score
        pred = fit.predict(X1)
        base_score = -mean_squared_error(y1, pred)
        
        row = {}
        for j in clstrs:
            X1_ = X1.copy(deep=True)
            for k in clstrs[j]:
                vals = X1_[k].values.copy() 
                np.random.shuffle(vals)
                X1_[k] = vals
            
            pred_j = fit.predict(X1_)
            row[j] = -mean_squared_error(y1, pred_j)
            
        return i, base_score, row

    # Parallel Execution across all repeated folds
    results = Parallel(n_jobs=n_jobs)(
        delayed(process_fold)(i, tr, te) for i, (tr, te) in enumerate(tqdm(cvGen, desc="Repeated MDA"))
    )

    scr0 = pd.Series(index=range(total_folds), dtype=float)
    scr1 = pd.DataFrame(index=range(total_folds), columns=list(clstrs.keys()), dtype=float)
    
    for i, base_score, row in results:
        scr0.loc[i] = base_score
        for j in row:
            scr1.loc[i, j] = row[j]

    # Importance: % Increase in error
    imp = (scr0.values[:, None] - scr1) / np.abs(scr0.values[:, None])

    # Final importance with standardized error
    imp = pd.concat({'mean': imp.mean(), 'std': imp.std() * imp.shape[0] ** -0.5}, axis=1)
    imp.index = ['C_' + str(i) for i in imp.index]
    return imp

def clusterKMeansBase(corr0,maxNumClusters=10,n_init=10):
    x,silh=((1-corr0.fillna(0))/2.)**.5,pd.Series()# observations matrix
    for init in range(n_init):
        for i in range(2,maxNumClusters+1):
            kmeans_=KMeans(n_clusters=i,n_init=1)
            kmeans_=kmeans_.fit(x)
            silh_=silhouette_samples(x,kmeans_.labels_)
            stat=(silh_.mean()/silh_.std(),silh.mean()/silh.std())
        if np.isnan(stat[1]) or stat[0]>stat[1]:
            silh,kmeans=silh_,kmeans_
    newIdx=np.argsort(kmeans.labels_)
    corr1=corr0.iloc[newIdx] # reorder rows
    corr1=corr1.iloc[:,newIdx] # reorder columns
    
    clstrs={i:corr0.columns[np.where(kmeans.labels_==i)[0]].tolist() for i in np.unique(kmeans.labels_) } # cluster members
    silh=pd.Series(silh,index=x.index)
    return corr1,clstrs,silh

def makeNewOutputs(corr0,clstrs,clstrs2):
    clstrsNew={}
    for i in clstrs.keys():
        clstrsNew[len(clstrsNew.keys())]=list(clstrs[i])
    for i in clstrs2.keys():
        clstrsNew[len(clstrsNew.keys())]=list(clstrs2[i])
    newIdx=[j for i in clstrsNew for j in clstrsNew[i]]
    corrNew=corr0.loc[newIdx,newIdx]
    x=((1-corr0.fillna(0))/2.)**.5
    kmeans_labels=np.zeros(len(x.columns))
    for i in clstrsNew.keys():
        idxs=[x.index.get_loc(k) for k in clstrsNew[i]]
        kmeans_labels[idxs]=i
    silhNew=pd.Series(silhouette_samples(x,kmeans_labels),index=x.index)
    
    return corrNew,clstrsNew,silhNew

def clusterKMeansTop(corr0,maxNumClusters=None,n_init=10):
    if maxNumClusters==None:
        maxNumClusters=corr0.shape[1]-1
    corr1,clstrs,silh=clusterKMeansBase(corr0,maxNumClusters= min(maxNumClusters,corr0.shape[1]-1),n_init=n_init)
    clusterTstats={i:np.mean(silh[clstrs[i]])/ np.std(silh[clstrs[i]]) for i in clstrs.keys()} 
    tStatMean=sum(clusterTstats.values())/len(clusterTstats)
    redoClusters=[i for i in clusterTstats.keys() if clusterTstats[i]<tStatMean]
    if len(redoClusters)<=1:
        return corr1,clstrs,silh
    else:
        keysRedo=[j for i in redoClusters for j in clstrs[i]]
        corrTmp=corr0.loc[keysRedo,keysRedo]
        tStatMean=np.mean([clusterTstats[i] for i in redoClusters])
        corr2,clstrs2,silh2=clusterKMeansTop(corrTmp, maxNumClusters=min(maxNumClusters, corrTmp.shape[1]-1),n_init=n_init)
        corrNew,clstrsNew,silhNew=makeNewOutputs(corr0, {i:clstrs[i] for i in clstrs.keys() if i not in redoClusters}, clstrs2)
        newTstatMean=np.mean([np.mean(silhNew[clstrsNew[i]])/ np.std(silhNew[clstrsNew[i]]) for i in clstrsNew.keys()])
        if newTstatMean<=tStatMean:
            return corr1,clstrs,silh
        else:
            return corrNew,clstrsNew,silhNew
        

def featImpMDA_Clustered_TS(
    clf, X, y, clstrs,
    n_splits=5, test_size=None, gap=0,
    n_jobs=-1, eps=1e-15
):
    y = pd.Series(y).values.ravel()
    labels_target = np.array([0, 1, 2])

    tscv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size, gap=gap)
    cvGen = list(tscv.split(X))

    def align_proba(proba, classes_):
        df = pd.DataFrame(proba, columns=list(classes_))
        df = df.reindex(columns=labels_target, fill_value=eps)
        s = df.sum(axis=1).replace(0.0, 1.0)
        return (df.div(s, axis=0)).values

    def process_fold(i, train, test):
        X0, y0 = X.iloc[train, :], y[train]
        X1, y1 = X.iloc[test, :], y[test]

        fit = clf.fit(X0, y0)
        prob = align_proba(fit.predict_proba(X1), fit.classes_)
        base_score = -log_loss(y1, prob, labels=labels_target)

        row = {}
        for j in clstrs:
            X1_ = X1.copy(deep=True)
            for k in clstrs[j]:
                arr = X1_[k].values.copy()
                np.random.shuffle(arr)
                X1_[k] = arr
            prob_j = align_proba(fit.predict_proba(X1_), fit.classes_)
            row[j] = -log_loss(y1, prob_j, labels=labels_target)

        return i, base_score, row

    results = Parallel(n_jobs=n_jobs)(
        delayed(process_fold)(i, tr, te)
        for i, (tr, te) in enumerate(tqdm(cvGen, desc="MDA Clusters (TS, no look-ahead)"))
    )

    scr0 = pd.Series(index=range(len(cvGen)), dtype=float)
    scr1 = pd.DataFrame(index=range(len(cvGen)), columns=list(clstrs.keys()), dtype=float)

    for i, base_score, row in results:
        scr0.loc[i] = base_score
        for j in row:
            scr1.loc[i, j] = row[j]

    imp = (-1.0 * scr1).add(scr0, axis=0)
    imp = imp / (-1.0 * scr1)
    imp = pd.concat({'mean': imp.mean(), 'std': imp.std() * imp.shape[0] ** -0.5}, axis=1)
    imp.index = ['C_' + str(i) for i in imp.index]
    return imp

def mutualInfo(x,y,norm=False): # mutual information     
    bXY=numBins(x.shape[0],corr=np.corrcoef(x,y)[0,1]) 
    cXY=np.histogram2d(x,y,bXY)[0] 
    iXY=mutual_info_score(None,None,contingency=cXY)
    if norm:
        hX=ss.entropy(np.histogram(x,bXY)[0]) # marginal         
        hY=ss.entropy(np.histogram(y,bXY)[0]) # marginal         
        iXY/=min(hX,hY) # normalized mutual information        
    return iXY

def getCleanRelationshipMatrix(data, relationship='corr', denoise=False):
    tmp = data.copy(deep=True)
    scaler = StandardScaler()
    column_names = tmp.columns 
    tmp=tmp.astype('float64')
    data_standardized = pd.DataFrame(scaler.fit_transform(tmp[column_names].values), columns=column_names)
    data_standardized = data_standardized.dropna()

    if relationship=='corr':
        relationship_matrix = np.corrcoef(data_standardized, rowvar=0)
    elif relationship=='variation_information':
        relationship_matrix = varInfo_matrix(data_standardized, norm=True)
    
    relationship_matrix = np.nan_to_num(relationship_matrix, nan=0.0)

    if denoise:
        eVal, eVec, column_names = getPCA(relationship_matrix, column_names)
        q = len(data_standardized)/len(data_standardized.columns)

        eMax, var = findMaxEval(np.diag(eVal), q, bWidth=0.1)
        nFacts = eVal.shape[0]-np.diag(eVal)[::-1].searchsorted(eMax)

        print(f'Nfacts: {nFacts}')

        corr_denoised = denoisedCorr(eVal, eVec, nFacts)

        corr_denoised = pd.DataFrame(corr_denoised)
        corr_denoised.columns=column_names
        corr_denoised.index=column_names
        return corr_denoised
    else:
        relationship_matrix = pd.DataFrame(relationship_matrix )
        relationship_matrix.columns=column_names
        relationship_matrix.index=column_names
        return relationship_matrix

def num_bins(nObs,corr):
    # Optimal number of bins for discretization  see A binning formula of bi-histogram for joint entropy estimation using mean square error minimization https://www.sciencedirect.com/science/article/abs/pii/S0167865517304142
    corr = np.clip(corr, -0.9999, 0.9999)
    if corr is None: # univariate case
        z=(8+324*nObs+12*(36*nObs+729*nObs**2)**.5)**(1/3.)
        b=round(z/6.+2./(3*z)+1./3) 
    else: # bivariate case
        if (1.-corr**2)==0:
            corr = np.sign(corr)*(np.abs(corr)-1e-5)  
           
        b=round(2**-.5*(1+(1+24*nObs/(1.-corr**2))**.5)**.5) 
    return int(b)

def get_optimal_bins(x, y=None):
    if y is not None:
        if np.std(x) == 0 or np.std(y) == 0:
            return 0.0 
        corr = np.corrcoef(x, y)[0, 1]

    else: 
        # Univariate Case
        corr = None
    
    bXY = num_bins(x.shape[0], corr=corr)
    return bXY

def mutual_info(x, y, optimal_bins, norm=False):
    cXY = np.histogram2d(x, y, optimal_bins)[0]
    iXY = mutual_info_score(None, None, contingency=cXY)

    if norm:
        hX = ss.entropy(np.histogram(x, optimal_bins)[0])
        hY = ss.entropy(np.histogram(y, optimal_bins)[0])
        iXY /= min(hX, hY) if min(hX, hY) > 0 else 1

    return iXY


def build_mi_distance_matrix(X, n_jobs=-1, dtype=np.float64):
    n_samples = X.shape[0]
    dist_matrix = np.ones((n_samples, n_samples), dtype=dtype)  # Start filled with 1s (worst-case distance)

    # Upper triangle only (i < j)
    pairs = [(i, j) for i in range(n_samples) for j in range(i + 1, n_samples)]

    def compute_pair(i, j):
        opt_bin =  get_optimal_bins(x=X[i], y=X[j])
        if opt_bin <1: 
            opt_bin=2
        mi = mutual_info(X[i], X[j], optimal_bins=opt_bin, norm=True)
        
        # avoid precision problem causing negative value
        dist = np.clip(1.-mi, 0.0, 1.0)
        return i, j, dtype(dist)

    results = Parallel(n_jobs=n_jobs, backend="loky")(
        delayed(compute_pair)(i, j) for i, j in tqdm(pairs, desc="Building MI Distance Matrix")
    )

    for i, j, dist in results:
        dist_matrix[i, j] = dist
        dist_matrix[j, i] = dist

    np.fill_diagonal(dist_matrix, 0.0)

    return dist_matrix


def score_for_k_with_progress(k, dist_matrix):
    model = AgglomerativeClustering(
        n_clusters=k,
        metric='precomputed',
        linkage='average'
    )
    labels = model.fit_predict(dist_matrix)
    score = silhouette_score(dist_matrix, labels, metric='precomputed')
    return score