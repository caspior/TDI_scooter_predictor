import dill
import pandas as pd
import statsmodels.api as sm
from datetime import date
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

# Trip estimator function
def trip_estimator(train, future, direction):
    
    #Generating a list of the census tracts
    tracts = list(train.GeoID.unique())
    
    #Defining the columns for the analysis
    cols = ['GeoID', 'Starts', 'Ends', 'temp', 'wspd', 'precip']
    time = range(19)
    cols.extend(time)
    
    #Creating analysis variables
    X = train[cols].dropna()
    F = future[cols].dropna()

    #Training:
    estimator = dict()
    bads = list()

    for tract in tracts:
        #Independent variables: Temprature, Wind speed, Percipitation, Month, Day of the week
        ind = X[X.GeoID==tract].drop(['GeoID', 'Starts', 'Ends'], axis=1).to_numpy()
        #Dependent variables: Starts/Ends
        dep = X[X.GeoID == tract][direction].to_numpy()
        #If all the trips equal to zero the model doesn't work
        try:
            #Estimating a Poisson model for count data
            estimator[tract] = sm.GLM(dep, ind, family=sm.families.Poisson()).fit()
        except:
            bads.append(tract)

    #Predicting:
    predicts = list()

    for i in range(len(F)):
        row = F[i:i+1] #go over the datafram row by row
        if row.GeoID.iloc[0] not in bads: #If there's a model. If not the prediction is zero
            predicts.append(int(estimator[row.GeoID.iloc[0]].predict(row.drop(['GeoID', 'Starts', 'Ends'], axis=1).to_numpy())))
        else:
            predicts.append(0)
    
    return predicts

if __name__ == '__main__':
    
    #Loading data generated with get_data.py
    data = dill.load(open('data.dill', 'rb'))

    #Extracting the month and the day of the week
    data['month'] = data.apply(lambda row: row.Date.month, axis=1)
    data['day'] = data.apply(lambda row: row.Date.weekday(), axis=1)

    #One hot encoding
    temp = data[['month', 'day']]

    ohe = OneHotEncoder(sparse=False)
    ohe_trans = ColumnTransformer([('ohe', ohe, ['month', 'day'])])

    new = ohe.fit_transform(temp)

    data = data.merge(pd.DataFrame(new), left_index=True, right_index=True)

    #Spliting to past and future datasets
    today = date.today().strftime('%Y-%m-%d')

    train = data[data.Date < today]
    future = data[data.Date >= today]
    
    #Predicting future trips
    start_predict = trip_estimator(train, future, 'Starts')
    end_predict = trip_estimator(train, future, 'Ends')
    
    #Applying the predictions to the dataset
    future['Starts'] = start_predict
    future['Ends'] = end_predict
    
    #Exporting the dataset for the Dash
    new_data = train.append(future)[['Starts', 'Ends', 'GeoID', 'Date']]
    dill.dump(new_data, open('new_data.dill', 'wb'))