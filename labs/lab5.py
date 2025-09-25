import streamlit as st
import requests
from openai import OpenAI

# Streamlit app title
st.title("🌤️ Travel Weather & Suggestion Bot")

# ----------------------
# WEATHER FUNCTION
# ----------------------
def get_current_weather(location, api_key):
    if "," in location:
        location = location.split(",")[0].strip()

    urlbase = "https://api.openweathermap.org/data/2.5/"
    urlweather = f"weather?q={location}&appid={api_key}"
    url = urlbase + urlweather

    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return {"error": data.get("message", "Could not fetch weather")}

    # Extract temperatures & convert Kelvin → Celsius
    temp = data['main']['temp'] - 273.15
    feels_like = data['main']['feels_like'] - 273.15
    temp_min = data['main']['temp_min'] - 273.15
    temp_max = data['main']['temp_max'] - 273.15
    humidity = data['main']['humidity']
    description = data['weather'][0]['description'].capitalize()

    return {
        "location": location,
        "temperature": round(temp, 2),
        "feels_like": round(feels_like, 2),
        "temp_min": round(temp_min, 2),
        "temp_max": round(temp_max, 2),
        "humidity": humidity,
        "description": description
    }

# ----------------------
# LLM SUGGESTION FUNCTION
# ----------------------
def get_clothing_suggestion(weather):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # Build a natural language prompt with the weather info
    weather_context = (
        f"Location: {weather['location']}\n"
        f"Temperature: {weather['temperature']}°C\n"
        f"Feels Like: {weather['feels_like']}°C\n"
        f"Condition: {weather['description']}\n"
        f"Humidity: {weather['humidity']}%\n"
    )

    prompt = (
        f"Here is today's weather:\n{weather_context}\n\n"
        f"Based on this, suggest:\n"
        f"1. What clothes to wear today.\n"
        f"2. Whether it's a good day for a picnic.\n"
    )

    response = client.chat.completions.create(
        model="gpt-5-mini",  # you can swap with mistral, gemini, etc.
        messages=[
            {"role": "system", "content": "You are a helpful travel and clothing suggestion assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# ----------------------
# STREAMLIT UI
# ----------------------
API_KEY = st.secrets["openweather_API_KEY"]

city = st.text_input("Enter a city (default = Syracuse, NY):")

if st.button("Get Weather & Suggestions"):
    if not city:
        city = "Syracuse, NY"  # default

    weather = get_current_weather(city, API_KEY)

    if "error" in weather:
        st.error(weather["error"])
    else:
        st.subheader(f"Weather in {city}")
        st.write(f"🌡️ Temperature: {weather['temperature']} °C")
        st.write(f"🤔 Feels like: {weather['feels_like']} °C")
        st.write(f"📉 Min: {weather['temp_min']} °C | 📈 Max: {weather['temp_max']} °C")
        st.write(f"💧 Humidity: {weather['humidity']}%")
        st.write(f"🌥️ Condition: {weather['description']}")

        # Call the LLM for clothing + picnic advice
        suggestion = get_clothing_suggestion(weather)
        st.markdown("### What to Wear & Picnic Advice")
        st.write(suggestion)
