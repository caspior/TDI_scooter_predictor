import pandas as pd
import requests
import datetime
import dill
from census import Census
from us import states


# Getting all the census tracts in Travis county, Texas
def get_ACS():
    
    Austin_counties = {'Travis': '453'}

    c = Census("bf7293bd6997b5ac079a45723172ea6929ed07de", year=2019)

    fips = ", ".join(list(Austin_counties.values()))
    ACS = pd.DataFrame(c.acs5.state_county_tract('B01003_001E', states.TX.fips, '453', Census.ALL))
    ACS['GeoID'] = ACS['state']+ACS['county']+ACS['tract']
    ACS = ACS.drop(['state','county','tract','B01003_001E'],axis=1)
    
    return ACS


# Getting the trips from Asutin's micromobility dataset
def get_trips(ACS):
    
    trips = pd.read_csv('https://data.austintexas.gov/api/views/7d8e-dm7r/rows.csv?accessType=DOWNLOAD')
    
    #Cleaning
    trips = trips[trips['Census Tract Start'] != 'OUT_OF_BOUNDS'].copy()
    trips = trips[trips['Census Tract End'] != 'OUT_OF_BOUNDS'].copy()
    
    #Getting scooter trips
    scooters = trips[trips['Vehicle Type']=='scooter'].copy()
    scooters['start_date'] = pd.to_datetime(scooters['Start Time'], format='%m/%d/%Y %I:%M:%S %p')
    scooters['end_date'] = pd.to_datetime(scooters['End Time'], format='%m/%d/%Y %I:%M:%S %p')
    
    #Aggregate by day 
    daily_starts = scooters.groupby([pd.Grouper(key='start_date',freq='D'),'Census Tract Start']).count()
    daily_starts = daily_starts.rename_axis(index=['date','tract'])
    daily_starts['Starts'] = daily_starts['ID']
    daily_starts = daily_starts[['Starts']].copy()

    daily_ends = scooters.groupby([pd.Grouper(key='end_date',freq='D'),'Census Tract End']).count()
    daily_ends = daily_ends.rename_axis(index=['date','tract'])
    daily_ends['Ends'] = daily_ends['ID']
    daily_ends = daily_ends[['Ends']].copy()

    daily_trips = daily_starts.merge(daily_ends, on=['date','tract'], how='outer')
    daily_trips = daily_trips.fillna(0)
    daily_trips['GeoID'] = daily_trips.index.get_level_values('tract')
    daily_trips['Date'] = daily_trips.index.get_level_values('date')
    
    #Filling tracts with no trips
    first_date = min(daily_trips.Date)
    last_date = datetime.date.today() + datetime.timedelta(days=15)
    date = first_date
    while date <= last_date:
        if  len(daily_trips[daily_trips['Date']==date])==0:
            new_day = {'Starts':0, 'Ends':0, 'GeoID':'48453000204', 'Date':date}
            daily_trips = daily_trips.append(new_day, ignore_index=True)
        df = daily_trips[daily_trips['Date']==date]
        df = df.merge(ACS, on='GeoID', how='right')
        df = df.fillna({'Starts': 0})
        df = df.fillna({'Ends': 0})
        df = df.fillna({'Date': date})
        if date == first_date:
            daily = df
        daily = daily.append(df, ignore_index=True)
        date += datetime.timedelta(days=1)

    daily = daily.iloc[:,:4].copy()
    
    return daily

#Getting historical and predicted weather from Visual Crossing
def get_weather():
    
    #Forecast
    url = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata/forecast?aggregateHours=24&combinationMethod=aggregate&contentType=json&unitGroup=metric&locationMode=single&key=ESEYE9SVTPPHS7KHRWJ7R7JDC&dataElements=default&locations=Austin%2C%20texas'
    response = requests.get(url)
    json = response.json()
    forecast = pd.DataFrame(json['location']['values'])
    #forecast['Date'] = pd.to_datetime(forecast['datetimeStr'])
    forecast = forecast[['temp', 'wspd', 'precip', 'datetimeStr']]
    
    #Historical data
    def get_history(start, end):
        url = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata/history?aggregateHours=24&combinationMethod=aggregate&startDateTime={}T00%3A00%3A00&endDateTime={}T00%3A00%3A00&maxStations=-1&maxDistance=-1&contentType=json&unitGroup=metric&locationMode=single&key=ESEYE9SVTPPHS7KHRWJ7R7JDC&dataElements=default&locations=Austin%2C%20texas'.format(start,end)
        response = requests.get(url)
        json = response.json()
        wthr = pd.DataFrame(json['location']['values'])
        wthr = wthr[['temp', 'wspd', 'precip', 'datetimeStr']]
        return wthr
    
    #The historical API is limited to 1000 records in batches of 100
    start_date = datetime.date.today() - datetime.timedelta(1000)
    end_date = start_date + datetime.timedelta(100)
    start = list()
    end = list()
    start.append(start_date)
    end.append(end_date)
    today = datetime.date.today()
    while (end_date <= today - datetime.timedelta(100)):
            start_date = end_date + datetime.timedelta(1)
            end_date = start_date + datetime.timedelta(100)
            start.append(start_date)
            end.append(end_date)
    start_date = end_date + datetime.timedelta(1)
    end_date = datetime.date.today() - datetime.timedelta(1)
    start.append(start_date)
    end.append(end_date)  
    
    weather_list = list()
    for i in range(len(start)):
        weather_list.append(get_history(start[i], end[i]))
    
    weather = weather_list[0]
    for i in range(1, len(weather_list)):
        weather = weather.append(weather_list[i])
    weather = weather.append(forecast)
    
    return weather


if __name__ == '__main__':
    
    ACS = get_ACS()
    daily = get_trips(ACS)
    daily['date_s'] = daily.Date.dt.strftime('%Y-%m-%d')
    
    weather = get_weather()
    weather['date_s'] = weather.datetimeStr.str[:10]

    data = daily.merge(weather, on='date_s', how='inner')
    data = data.drop(['date_s', 'datetimeStr'], axis=1)
    
    #Exporting the data for the prediction model
    dill.dump(data, open('data.dill', 'wb'))