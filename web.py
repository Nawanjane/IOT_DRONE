import streamlit as st
import plotly.graph_objs as go
import firebase_admin
from firebase_admin import credentials, db
import sqlite3
import time
import uuid

# Firebase setup - Initialize Firebase Admin SDK
cred = credentials.Certificate("sdk.json")  # Replace with your Firebase JSON path
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://drone-59950-default-rtdb.firebaseio.com/'  # Replace with your Firebase database URL
})

# SQLite setup - connect to SQLite database (it will create the file if it doesn't exist)
conn = sqlite3.connect("sensor_data.db")
cursor = conn.cursor()

# Ensure that the necessary tables exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS sensor_data (
    id TEXT PRIMARY KEY,
    timestamp TEXT,
    temperature REAL,
    humidity REAL
)
''')
conn.commit()

# Streamlit configuration
st.title("Real-Time Temperature and Humidity Monitor")

# Firebase reference
ref = db.reference('sensors')

# Function to store new sensor data into SQLite with unique ID
def store_new_data(timestamp, temperature, humidity):
    try:
        unique_id = str(uuid.uuid4())  # Generate a unique ID for each entry
        timestamp = str(timestamp)      # Convert timestamp to string
        temperature = float(temperature) if temperature is not None else 0.0  # Default to 0.0 if None
        humidity = float(humidity) if humidity is not None else 0.0           # Default to 0.0 if None

        cursor.execute('''
        INSERT OR REPLACE INTO sensor_data (id, timestamp, temperature, humidity)
        VALUES (?, ?, ?, ?)
        ''', (unique_id, timestamp, temperature, humidity))
        conn.commit()

    except Exception as e:
        st.error(f"Failed to store data: {e}")

# Function to fetch the last 20 data points from the database
def get_last_20_data_points():
    cursor.execute('SELECT * FROM (SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 20) ORDER BY timestamp ASC')
    data = cursor.fetchall()
    
    timestamps = [entry[1] for entry in data]  # Timestamp as x-axis
    temperatures = [entry[2] for entry in data]  # Temperature
    humidities = [entry[3] for entry in data]  # Humidity
    
    return timestamps, temperatures, humidities

# Real-time data fetching and display
st.write("Monitoring temperature and humidity levels...")

# Use container to allow for dynamic updating of the same chart without unique keys
with st.container():
    while True:
        # Get new data from Firebase
        data = ref.get()

        if data:
            # Handle Firebase data as either list or dictionary
            if isinstance(data, list) and data:
                latest_entry = data[-1]  # Get the last item in the list
            elif isinstance(data, dict):
                latest_entry = list(data.values())[-1]
            else:
                st.error("Unexpected data format from Firebase.")
                continue

            # Extract timestamp, temperature, and humidity
            timestamp = latest_entry.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
            temperature = latest_entry.get("temperature", 0.0)
            humidity = latest_entry.get("humidity", 0.0)

            # Store the new data into SQLite with a unique ID
            store_new_data(timestamp, temperature, humidity)

            # Fetch the most recent 20 data points for display
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

            # Plot the humidity chart
            humidity_trace = go.Scatter(x=timestamps_for_chart, y=humidities_for_chart, mode="lines+markers", name="Humidity (%)", line=dict(color='blue'))
            humidity_layout = go.Layout(
                title="Humidity Over Time",
                xaxis=dict(title="Timestamp"),
                yaxis=dict(title="Humidity (%)"),
                template="plotly_dark"
            )
            humidity_fig = go.Figure(data=[humidity_trace], layout=humidity_layout)

            # Update charts in Streamlit container
            st.plotly_chart(temp_fig, use_container_width=True)
            st.plotly_chart(humidity_fig, use_container_width=True)

            # Display the live values with Streamlit metrics
            st.metric("Live Temperature", f"{temperature:.2f}°C")
            st.metric("Live Humidity", f"{humidity:.2f}%")

        # Pause for 5 seconds before the next update
        time.sleep(5)
