from flask import Flask, render_template
import requests
import datetime as dt
import pandas as pd
import json

app = Flask(__name__)

# moon data
moon_URL = 'https://aa.usno.navy.mil/api/moon/phases/date?date=2023-10-24&nump=50'
moon_phases = requests.get(moon_URL).json()

# Filter the data for the year 2023
filtered_data = [phase for phase in moon_phases['phasedata'] if phase['year'] == 2023]

# weather data
base_url = 'https://api.meteomatics.com'

# Cloud forecast for 10 days from October 13, 2023
# Available levels: low, medium, high, effective, total
# Available measures: mean
# Available intervals: 1h, 2h, 6h, 12h, 24h
# Available units: octas, p

current_date = dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
validdatetime = f"{current_date}P10D:PT12H"

location = '39.952583,-75.165222'  #Philadelphia as defalut 
format='json'
#format = 'html'
optionals = 'source=mix'
username = 'upenn_whang_sungim'
password = 'OD4p6y7qO5'

cloud_levels = ["low", "medium", "high", "effective", "total"]
all_cloud_data = {}

for level in cloud_levels :
    parameters = f'{level}_cloud_cover_mean_12h:p'

    cloud_url = f'{base_url}/{validdatetime}/{parameters}/{location}/{format}?{optionals}'
    response = requests.get(cloud_url, auth=(username, password))
    cloud_data = response.json()
    all_cloud_data[level] = cloud_data

# Function to convert to dataframes
def process_cloud_data(cloud_data, level):
    cloud_df = pd.DataFrame(cloud_data)
    cloud_df['date'] = pd.to_datetime(cloud_df['date'])
    cloud_df.set_index('date', inplace=True)
    cloud_df.index = cloud_df.index.strftime('%Y-%m-%d %H:%M')
    cloud_df.rename(columns={'value': f'{level} cloud cover mean'}, inplace=True)
    return cloud_df

cloud_data_frames = []

for i, level in enumerate(cloud_levels):
    cloud_data_frames.append(process_cloud_data(all_cloud_data[level]['data'][0]['coordinates'][0]['dates'], level))

# Merge the DataFrames
combined_df = cloud_data_frames[0]
for i in range(1, len(cloud_data_frames)):
    combined_df = pd.merge(combined_df, cloud_data_frames[i], on='date')   

# Convert the combined DataFrame to JSON
combined_json = combined_df.to_json(orient='split')    

# Define a route for the home page
@app.route('/')
def home():
    return render_template('index.html', data={'phasedata': filtered_data, 'weather_data': combined_json})

if __name__ == '__main__':
    app.run(debug=True)