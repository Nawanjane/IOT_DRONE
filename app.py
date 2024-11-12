import sqlite3
import numpy as np
import streamlit as st
import plotly.graph_objs as go
import time

# SQLite setup - connect to SQLite database (it will create the file if it doesn't exist)
conn = sqlite3.connect("sensor_data.db")
cursor = conn.cursor()

# Ensure that the necessary tables exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    temperature REAL,
    humidity REAL
)
''')
conn.commit()

# Streamlit configuration
st.title("Real-Time Temperature and Humidity Monitor")

# Placeholder for dynamic charts and live meters
temp_placeholder = st.empty()
humidity_placeholder = st.empty()
live_temp_placeholder = st.empty()
live_humidity_placeholder = st.empty()

# Function to store new sensor data into SQLite
def store_new_data(timestamp, temperature, humidity):
    cursor.execute('''
    INSERT INTO sensor_data (timestamp, temperature, humidity)
    VALUES (?, ?, ?)
    ''', (timestamp, temperature, humidity))
    conn.commit()

# Function to fetch the most recent 20 data points from the SQLite database
def get_last_20_data_points():
    cursor.execute('SELECT * FROM sensor_data ORDER BY id DESC LIMIT 20')
    data = cursor.fetchall()
    
    timestamps = [entry[1] for entry in data]  # Timestamp as x-axis
    temperatures = [entry[2] for entry in data]  # Temperature
    humidities = [entry[3] for entry in data]  # Humidity
    
    return timestamps, temperatures, humidities

# Function to delete the oldest record from SQLite to maintain the last 20 records
def delete_oldest_record():
    cursor.execute('''
    DELETE FROM sensor_data
    WHERE id = (SELECT MIN(id) FROM sensor_data)
    ''')
    conn.commit()

# Real-time value update
st.write("Monitoring temperature and humidity levels...")

# Live meter: Show live temperature and humidity
while True:
    # Get new sensor data (replace with actual data collection logic)
    # Example values for testing, replace with actual sensor data
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    temperature = np.random.uniform(20, 30)  # Simulating temperature data
    humidity = np.random.uniform(30, 70)  # Simulating humidity data
    
    # Store the new data into SQLite
    store_new_data(timestamp, temperature, humidity)

    # Delete the oldest record if more than 20 entries exist
    cursor.execute('SELECT COUNT(*) FROM sensor_data')
    count = cursor.fetchone()[0]
    if count > 20:
        delete_oldest_record()

    # Fetch the most recent 20 data points from SQLite
    timestamps_for_chart, temperatures_for_chart, humidities_for_chart = get_last_20_data_points()

    # Plot the temperature chart
    temp_trace = go.Scatter(x=timestamps_for_chart, y=temperatures_for_chart, mode="lines+markers", name="Temperature (°C)", line=dict(color='orange'))
    temp_layout = go.Layout(
        title="Temperature Over Time",
        xaxis=dict(title="Timestamp"),
        yaxis=dict(title="Temperature (°C)"),
        template="plotly_dark"
    )
    temp_fig = go.Figure(data=[temp_trace], layout=temp_layout)
    temp_placeholder.plotly_chart(temp_fig, use_container_width=True)

    # Plot the humidity chart
    humidity_trace = go.Scatter(x=timestamps_for_chart, y=humidities_for_chart, mode="lines+markers", name="Humidity (%)", line=dict(color='blue'))
    humidity_layout = go.Layout(
        title="Humidity Over Time",
        xaxis=dict(title="Timestamp"),
        yaxis=dict(title="Humidity (%)"),
        template="plotly_dark"
    )
    humidity_fig = go.Figure(data=[humidity_trace], layout=humidity_layout)
    humidity_placeholder.plotly_chart(humidity_fig, use_container_width=True)

    # Display the live values with meters
    live_temp_placeholder.metric("Live Temperature", f"{temperature:.2f}°C")
    live_humidity_placeholder.metric("Live Humidity", f"{humidity:.2f}%")

    # Pause for 5 seconds before the next update
    time.sleep(5)
