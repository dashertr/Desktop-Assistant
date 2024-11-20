#!/usr/bin/env python
# coding: utf-8

#  ignore

# In[15]:


#imports

import pyttsx3 #text to speech
import speech_recognition as sr
import datetime
import webbrowser
import os
import smtplib
import pyautogui #simulate mouse movements
import time
import requests  #to interact with the weather API
from nba_api.stats.endpoints import scoreboardv2
from nba_api.stats.static import teams
from datetime import datetime, timedelta
import threading


# In[2]:


#Initialize the TTS engine
engine = pyttsx3.init('nsss')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[19].id)


# In[3]:


#Uses the pyttsx3 library to convert text to spoken audio.
def speak(audio):
    engine.say(audio)
    engine.runAndWait()


# In[4]:


#Greets the user based on time of day
def greet():
    hour = int(datetime.now().hour)  # Use datetime.now() directly
    if 0 <= hour < 12:
        speak("Good Morning!")
    elif 12 <= hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")
    speak("How can I help you?")


# In[5]:


#Takes voice input
def Command():
    r = sr.Recognizer() #initializes an instance of the Recognizer class from the speech_recognition module. Used to recognize speech and convert it into text.
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)

    try:
        print("Recognizing...")
        message = r.recognize_google(audio, language='en-in') #The recognize_google() method sends the recorded audio to the Google Web Speech API and returns the recognized text
        print(f"User said: {message}\n")
    except Exception as e:
        print("Say that again please...")
        return "None"
    return message


# In[6]:


#Opens and plays a given piece of music on spotify (for macOS)
def playSpotifyPlaylist(music):
    speak(f"Opening Spotify and playing {music}")
    os.system("open -a Spotify") #macos command to open spotify
    time.sleep(3)
    pyautogui.hotkey('command', 'l')
    time.sleep(2)
    pyautogui.typewrite(music)
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.press('tab', presses=2)
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.click(x=486, y=319)
    speak(f"Playing {music} on Spotify")


# In[7]:


#Sends myself a reminder via email
def sendEmail(subject, content):
    sender_email = 'troydasher02@gmail.com'
    to = sender_email
    app_password = 'fbdx rsbo ojvu mxrh'
    server = smtplib.SMTP('smtp.gmail.com', 587) #creates an SMTP object to connect to Gmail's SMTP server at smtp.gmail.com on port 587
    server.ehlo() #establishes communication between the client and server
    server.starttls() #makes it more secure
    try:
        server.login(sender_email, app_password)
        message = f'Subject: {subject}\n\n{content}'
        server.sendmail(sender_email, to, message)
        server.close()
        print("Reminder email sent successfully.")
        speak("Reminder has been sent successfully.")
    except Exception as e:
        print(f"Failed to send reminder: {e}")
        speak("I couldn't send the reminder due to an error.")


# In[8]:


#Accesses NBA API to retrieve the games from yesterday and give the user every score
def lookup_nba_games_yesterday():
    # Get the list of all NBA teams and map them by their IDs
    nba_teams = teams.get_teams()
    team_id_map = {team['id']: team['full_name'] for team in nba_teams}

    # Calculate yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y-%m-%d')  # Format as YYYY-MM-DD

    try:
        #Get the NBA scoreboard data for yesterday
        scoreboard = scoreboardv2.ScoreboardV2(game_date=yesterday.strftime('%m/%d/%Y'))
        game_header = scoreboard.game_header.get_dict()
        line_score = scoreboard.line_score.get_dict()

        if game_header['data']:
            games_summary = []

            #Iterate over the games
            for game in game_header['data']:
                game_id = game[2]  #Extract the game ID
                home_team_id = game[6]  #Home team ID
                away_team_id = game[7]  #Away team ID

                home_team = team_id_map.get(home_team_id, "Unknown Team")
                away_team = team_id_map.get(away_team_id, "Unknown Team")

                home_score = None
                away_score = None

                for score in line_score['data']:
                    if score[2] == game_id: 
                        if score[3] == home_team_id:
                            home_score = score[22]  #Home team score
                        elif score[3] == away_team_id:
                            away_score = score[22]  #Away team score

                # Construct the game summary
                if home_score is not None and away_score is not None:
                    summary = f"The {home_team} played against the {away_team}. The final score was {home_team} {home_score}, {away_team} {away_score}."
                    games_summary.append(summary)
                    print(summary)
                    speak(summary)

            if not games_summary:
                print("No games were found for yesterday.")
                speak("I couldn't find any NBA games for yesterday.")
        else:
            print("No games found or there was an issue with the data.")
            speak("I couldn't find any NBA scores for yesterday.")
    except Exception as e:
        print(f"An error occurred: {e}")
        speak("There was an error retrieving NBA scores.")


# In[12]:


#Gets users current latitude and longitude in order to run weather function
def get_lat_lon():
    try:
        response = requests.get('https://ipinfo.io')
        data = response.json()
        #Parse the loc field, which contains the latitude and longitude as a comma-separated string
        location = data['loc'].split(',')
        latitude = location[0]
        longitude = location[1]
        return latitude, longitude
    except Exception as e:
        print(f"Failed to retrieve geolocation data: {e}")
        return None, None


# In[9]:


#Accesses a weather API to retrieve the current weather+forecast for rest of day at users coordinates
def get_weather():
    api_key = "495974593c0787d564cada77701b4a87"  
    lat, lon = get_lat_lon()
    
    if lat and lon:
        base_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&units=imperial&appid={api_key}"
        response = requests.get(base_url)
        weather_data = response.json() #parses the JSON-encoded content of the response body into a Python dictionary
        
        if 'current' in weather_data and 'daily' in weather_data:
            try:
                current_temp = weather_data['current']['temp']
                description = weather_data['current']['weather'][0]['description']
                speak(f"The current temperature is {current_temp} degrees Farenheit with {description}.")
                
                #Extract today's forecast
                daily_forecast = weather_data['daily'][0]  
                
                temp_morning = daily_forecast['temp']['morn']
                temp_afternoon = daily_forecast['temp']['day']
                temp_evening = daily_forecast['temp']['eve']

                #Classify
                def classify_weather(description):
                    if "clear" in description:
                        return "clear skies"
                    elif "partly" in description or "few clouds" in description:
                        return "partly cloudy"
                    elif "clouds" in description and "overcast" not in description:
                        return "cloudy"
                    elif "overcast" in description:
                        return "overcast skies"
                    else:
                        return description  

                morning_weather = classify_weather(daily_forecast['weather'][0]['description'])
                afternoon_weather = classify_weather(daily_forecast['weather'][0]['description'])
                evening_weather = classify_weather(daily_forecast['weather'][0]['description'])
                
                rain_message = ""
                if 'rain' in daily_forecast:
                    rain_amount = daily_forecast['rain']
                    if rain_amount < 2.5:
                        rain_intensity = "light rain"
                    elif 2.5 <= rain_amount < 7.5:
                        rain_intensity = "moderate rain"
                    elif 7.5 <= rain_amount < 50:
                        rain_intensity = "heavy rain"
                    rain_message = f"Expect {rain_intensity} throughout the day with approximately {rain_amount} mm of rain."
                
                snow_message = ""
                if 'snow' in daily_forecast:
                    snow_amount = daily_forecast['snow']
                    snow_message = f"Snowfall expected with approximately {snow_amount} mm of snow."

                #Combine all information
                speak(f"The forecast for the rest of the day is: "
                      f"{temp_morning} degrees in the morning with {morning_weather}, "
                      f"{temp_afternoon} degrees in the afternoon with {afternoon_weather}, "
                      f"and {temp_evening} degrees in the evening with {evening_weather}.")
                if rain_message:
                    speak(rain_message)
                if snow_message:
                    speak(snow_message)
            except KeyError as e: #Catches errors that occur when trying to access missing keys in the JSON response
                print(f"Key error while parsing JSON: {e}")
                speak("There was an issue parsing the weather data.")
        else:
            print("JSON response does not contain 'current' or 'daily' keys.")
            speak("I couldn't retrieve the weather information at the moment.")
    else:
        speak("I couldn't determine your location.")
        


# In[16]:


def listen_for_keyword():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for the keyword 'LeBron'...")
        while True:
            try:
                audio = recognizer.listen(source, timeout=None)  # Continuous listening
                detected_text = recognizer.recognize_google(audio, language='en-in').lower()
                print(f"Detected: {detected_text}")
                if 'lebron' in detected_text:
                    print("Keyword 'LeBron' detected!")
                    speak("Activating main logic.")
                    main_logic()  # Call your main logic function
            except sr.UnknownValueError:
                continue  # Continue listening if speech was not understood
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                break
                


# In[17]:


#Main logic for the bot, when it hears certain words it will call the correlated function
def main_logic():
    greet()
    while True:
        message = Command().lower()
        if 'exit' in message or 'stop' in message:
            speak("Goodbye!")
            break
        elif 'open youtube' in message:
            webbrowser.open("https://youtube.com")
        elif 'open google' in message:
            webbrowser.open("https://google.com")
        elif 'play spotify' in message:
            speak("What would you like me to play?")
            playlist_name = Command().lower()
            if playlist_name != "none":
                playSpotifyPlaylist(playlist_name)
            else:
                speak("I didn't catch that. Please try again.")
        elif 'the time' in message:
            strTime = datetime.datetime.now().strftime("%H:%M")
            speak(f"The time is {strTime}")
        elif 'remind myself' in message:
            try:
                speak("What should I say?")
                content = Command()
                sendEmail("Reminder", content)
            except Exception as e:
                print(e)
                speak("Sorry, I can't send this email.")
        elif 'basketball' in message:
            lookup_nba_games_yesterday()
        elif 'weather' in message:
            get_weather()


# In[19]:


#runs the bot
if __name__ == "__main__":
    main_logic()


# In[ ]:




