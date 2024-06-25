import random
import wikipediaapi
import json
import re
import string
from bs4 import BeautifulSoup
import requests
from textblob import TextBlob
import nltk
import operator
from datetime import datetime
import asyncio
import python_weather
import os

wiki_wiki = wikipediaapi.Wikipedia('https://www.mediawiki.org/w/api.php')

with open('responses.json', 'r', encoding='utf-8') as file:
    responses = json.load(file)

with open('mood_words.json', 'r', encoding='utf-8') as file:
    mood_words = json.load(file)

nltk.download('punkt')

def get_page_html(title):
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=parse&section=0&prop=text&format=json&page={title}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        html_content = data['parse']['text']['*']
        return html_content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Wikipedia page: {e}")
        return None
    except KeyError as e:
        print(f"KeyError: {e}. JSON response does not contain expected structure.")
        return None

def get_first_infobox(html):
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.find_all(class_='infobox')
    if not results:
        raise LookupError('Page has no infobox')
    return results[0]

def clean_text(text):
    only_ascii = ''.join([char if char in string.printable else ' ' for char in text])
    no_dup_spaces = re.sub(' +', ' ', only_ascii)
    no_dup_newlines = re.sub('\n+', '\n', no_dup_spaces)
    return no_dup_newlines

def get_first_infobox_text(title):
    html = get_page_html(title)
    if html is None:
        return "Failed to retrieve Wikipedia page."
    
    try:
        infobox = get_first_infobox(html)
        infobox_text = clean_text(infobox.text)
        return infobox_text
    except Exception as e:
        print(f"Error processing infobox: {e}")
        return "An error occurred while processing the Wikipedia page."

def get_match(text, pattern, error_text="Page doesn't appear to have the property you're expecting"):
    p = re.compile(pattern, re.DOTALL | re.IGNORECASE)
    match = p.search(text)
    if not match:
        raise AttributeError(error_text)
    return match

def get_planet_radius(title):
    infobox_text = get_first_infobox_text(title)
    pattern = r'(?:Polar radius.*?)(?: ?[\d]+ )?(?P<radius>[\d,.]+)(?:.*?)km'
    error_text = "Page infobox has no polar radius information."
    match = get_match(infobox_text, pattern, error_text)
    return match.group('radius')

def get_birth_date(title):
    infobox_text = get_first_infobox_text(title)
    pattern = r'(?:Born\D*)(?P<birth>\d{4}-\d{2}-\d{2})'
    error_text = "Page infobox has no birth information. At least none in xxxx-xx-xx format"
    match = get_match(infobox_text, pattern, error_text)
    return match.group('birth')

def get_trial_ddate(title):
    infobox_text = get_first_infobox_text(title)
    pattern = r'Decided(\s+)(?P<ddate>[a-z]+\s[\d]{1,2},\s[\d]{4})'
    error_text = "Page infobox has no decision date information. At least none in Month-xx-xxxx format"
    match = get_match(infobox_text, pattern, error_text)
    return match.group('ddate')

def get_hex_triplet(title):
    infobox_text = get_first_infobox_text(title)
    pattern = r'(?P<color>#\w{6})'
    error_text = "Page infobox has no hex triplet information. At least none in the #xxxxxx format"
    match = get_match(infobox_text, pattern, error_text)
    return match.group('color')

def get_RGB(title):
    infobox_text = get_first_infobox_text(title)
    pattern = r'\(r, g, b\)\n(?P<RGB>\([\d]+, [\d]+, [\d]+\))'
    error_text = "Page infobox has no country information."
    match = get_match(infobox_text, pattern, error_text)
    return match.group('RGB')

def calculate_numbers(tokens):
    operators = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        '%': operator.mod
    }
    
    components = []
    current_number = ""
    
    for token in tokens[1:]:
        if token in operators:
            if current_number:
                components.append(float(current_number))
                current_number = ""
            components.append(token)
        else:
            current_number += token
    
    if current_number:
        components.append(float(current_number))
    
    try:
        result = components[0]
        
        for i in range(1, len(components), 2):
            operator = components[i]
            next_number = components[i + 1]
            result = operators[operator](result, next_number)
        
        return [str(result)]
    
    except (IndexError, KeyError, TypeError, ZeroDivisionError) as e:
        return ["Invalid calculation. Please try again."]

def chatbot_response_calculate(user_input):
    tokens = user_input.split()
    if tokens[0].lower() == "calculate":
        result = calculate_numbers(tokens)
        return " ".join(result)
    else:
        return "I can only perform calculations right now."

def get_wikipedia_summary(query):
    page = wiki_wiki.page(query)
    if page.exists():
        summary = page.summary
        if len(summary) >= 1000:
            return summary
        else:
            sentences = nltk.sent_tokenize(summary)
            truncated_summary = ''
            for sentence in sentences:
                if len(truncated_summary) + len(sentence) + 1 > 1000:
                    break
                truncated_summary += ' ' + sentence
            return truncated_summary.strip()
    else:
        return "Sorry, I couldn't find any information on that topic."

def birthDate(argList):
    person = ' '.join(argList)
    return [get_birth_date(person)]

def polarRadius(argList):
    planet = ' '.join(argList)
    return [get_planet_radius(planet)]

def ddate(argList):
    trialcase = ' '.join(argList)
    return [get_trial_ddate(trialcase)]

def hextriplet(argList):
    color = ' '.join(argList)
    return [get_hex_triplet(color)]

def RGB(argList):
    color = ' '.join(argList)
    return [get_RGB(color)]

def byeAction(dummy):
    raise KeyboardInterrupt

def get_current_time():
    now = datetime.now()
    return [now.strftime("The current date and time is %Y-%m-%d %H:%M:%S")]

def timeAction(dummy):
    return get_current_time()

async def get_weather(city):
    try:
        async with python_weather.Client(unit=python_weather.Unit.METRIC) as client:
            weather = await client.find(city)
            
            if not weather.current:
                current_temp = "N/A"
            else:
                current_temp = weather.current.temperature

            daily_forecasts = []

            for daily in weather.forecasts:
                day = daily.date.strftime('%A')
                low_temp = daily.low
                high_temp = daily.high
                condition = daily.sky_text
                daily_forecasts.append(f"{day}: Low of {low_temp}°C, High of {high_temp}°C - {condition}")

            weather_info = f"Current temperature in {city}: {current_temp}°C\n"
            weather_info += "\n".join(daily_forecasts)

            return weather_info

    except python_weather.APIException as e:
        return f"Error retrieving weather: {e}"

    except Exception as e:
        return f"An error occurred: {e}"

def weatherAction(argList):
    city = ' '.join(argList)
    return [asyncio.run(get_weather(city))]

def tell_joke():
    return random.choice(responses["jokes"])

def jokeAction(dummy):
    return [tell_joke()]

def match(pattern, source):
    pind, sind = 0, 0
    matches = []
    accumulator = ""
    accumulating = False
    while True:
        if len(pattern) == pind and len(source) == sind:
            if accumulating:
                matches.append(accumulator.lstrip())
            return matches
        elif len(pattern) == pind:
            if accumulating:
                accumulator += " " + source[sind]
                sind += 1
            else:
                return None
        elif pattern[pind].startswith('[') and pattern[pind].endswith(']'):
            accumulating = True
            accumulator = ""
            pind += 1
        elif len(source) == sind:
            return None
        elif pattern[pind] == source[sind]:
            if accumulating:
                accumulating = False
                matches.append(accumulator.lstrip())
            pind += 1
            sind += 1
        else:
            if accumulating:
                accumulator += " " + source[sind]
                sind += 1
            else:
                return None

def searchPAList(user_input):
    for pattern, action in paList:
        try:
            matches = match(pattern, user_input)
            if matches is not None:
                return action(matches)
        except AttributeError:
            continue
    return ["I don't understand."]

def detect_mood(user_input):
    analysis = TextBlob(user_input)
    polarity = analysis.sentiment.polarity
    if polarity > 0.1:
        return "positive"
    elif polarity < -0.1:
        return "negative"
    else:
        return "neutral"

def chatbot_response(user_input):
    input_lower = user_input.lower().strip()
    
    if input_lower.startswith("search for"):
        query = input_lower.replace("search for", "").strip()
        if query:
            return get_wikipedia_summary(query)
        else:
            return "Please specify what you want to search for."
    else:
        tokens = nltk.word_tokenize(input_lower)
        response = searchPAList(tokens)
        if response == ["I don't understand."]:
            mood = detect_mood(user_input)
            if mood in responses["mood"]:
                return random.choice(responses["mood"][mood])
            else:
                return random.choice(responses["fallback"])
        else:
            return ' '.join(response)
        
paList = [
    ('when was [PERSON] born'.split(),                     birthDate),
    ('what is the polar radius of [PLANET]'.split(),       polarRadius),
    ('what is the decision date of case [CASE]'.split(),   ddate),
    ('what is the hex triplet of [COLOR]'.split(),         hextriplet),
    ('what is the rgb value of [COLOR]'.split(),           RGB),
    ('calculate [EXPRESSION]'.split(),                     chatbot_response_calculate),
    ('what is the weather in [CITY]'.split(),              weatherAction),
    ('what time is it'.split(),                            timeAction),
    ('tell me a joke'.split(),                             jokeAction),
    (['bye'],                                              byeAction)
]

if __name__ == "__main__":
    print("Hi, I'm Biblio.")
    print("Type 'search for [topic]' to get information from Wikipedia or ask specific questions.")
    print("for the weather function to work either have your own api + key or use one from outside.")
    print("Type 'bye' to exit.")
    
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Biblio:", random.choice(responses["goodbye"]))
            break
        
        response = chatbot_response(user_input)
        print("Biblio:", response)
