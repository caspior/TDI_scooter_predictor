# Scooter sharing trip predictor - Austin, Texas
## [This app](https://scooter-predict.herokuapp.com/) is my capstone project for [The Data Incubator](https://www.thedataincubator.com) program

The app using scooter sharing trip history and weather data to predict the number of scooter trip departing and arriving at each census tract in Austin in the following two weeks.

### Data sources
* Trip logs were retrieved from the [City of Austin's open data portal](https://data.austintexas.gov/Transportation-and-Mobility/Shared-Micromobility-Vehicle-Trips/7d8e-dm7r).
* Historical and forecasted weather data retrieved from the [Visual Crossing weather api](https://www.visualcrossing.com/weather-api).
* Information regarding census tracts in Travis County obtained with the [U.S. Census' python library](https://pypi.org/project/census/).
* Polygons for Travis County's census tracts were downloaded from [TIGER](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) and converted to json file.
* See [get_data.py](https://github.com/caspior/scooter_predictor/blob/master/get_data.py) for full script.

### Predictive model
* The predictive model is based on [Statsmodel GLM Poisson regression](https://www.statsmodels.org/stable/glm.html).
* The explanatory variables include the month of the year, the day of the week, and the average daily temperature, wind speed, and precipitation.
* See [model.py](https://github.com/caspior/scooter_predictor/blob/master/model.py) for full script.

### Web-app
* The web app created using the [Dash](https://dash.plotly.com/) library with [Plotly](https://plotly.com/python/) visualizations.
* The design of my web-app is based on [this Dash example](https://github.com/plotly/dash-sample-apps/tree/master/apps/dash-study-browser).
* The app was deployed on [Heroku](https://www.heroku.com/) server.
* See [app.py](https://github.com/caspior/scooter_predictor/blob/master/app.py) for full script.
