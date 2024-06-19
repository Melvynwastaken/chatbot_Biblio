import random
import wikipediaapi
import json
import re
import string
from bs4 import BeautifulSoup
import requests

# Initialize Wikipedia object
wiki_wiki = wikipediaapi.Wikipedia('https://en.wikipedia.org/w/api.php')

# Set user-agent globally
wiki_wiki.user_agent = "Biblio (https://github.com/Melvynwastaken/chatbot_Biblio)"

# Load predefined responses from a JSON file
with open('responses.json', 'r', encoding='utf-8') as file:
    responses = json.load(file)

# Function to get a Wikipedia summary for a given query
def get_wikipedia_summary(query):
    page = wiki_wiki.page(query)
    if page.exists():
        return page.summary[:500]  # Limit to the first 500 characters
    else:
        return "Sorry, I couldn't find any information on that topic."

# Functions for fetching and parsing Wikipedia pages
def get_page_html(title):
    return requests.get(f"https://en.wikipedia.org/w/api.php?action=parse&section=0&prop=text&format=json&page={title}").json()['parse']['text']['*']

def get_first_infobox_text(title):
    html = get_page_html(title)
    return clean_text(get_first_infobox(html).text)

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

# Actions associated with each pattern
def birthDate(argList):
    person = ' '.join(argList)
    return [get_birth_date(person)]

def polarRadius(argList):
    planet = argList[0]
    return [get_planet_radius(planet)]

def ddate(argList):
    trialcase = ' '.join(argList)
    return [get_trial_ddate(trialcase)]

def hextriplet(argList):
    color = argList[0]
    return [get_hex_triplet(color)]

def RGB(argList):
    color = argList[0]
    return [get_RGB(color)]

def byeAction(dummy):
    raise KeyboardInterrupt

# Pattern-action list for the natural language query system
paList = [
    ('when was % born'.split(),                     birthDate),
    ('what is the polar radius of %'.split(),       polarRadius),
    ('what is the decision date of case %'.split(), ddate),
    ('what is the hex triplet of %'.split(),        hextriplet),
    ('what is the rgb value of %'.split(),          RGB),
    (['bye'],                                       byeAction)
]

# Function to match patterns and perform actions
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
        elif pattern[pind] == "%":
            accumulating = True
            accumulator = ""
            pind += 1
        elif len(source) == sind:
            return None
        elif pattern[pind] == "_":
            matches.append(source[sind])
            pind += 1
            sind += 1
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

def searchPAList(src):
    numMatches = 0
    resultList = []
    for pat, act in paList:
        mat = match(pat, src)
        if mat is not None:
            numMatches += 1
            resultList += act(mat)
    if not numMatches:
        return ["I don't understand."]
    elif not resultList:
        return ["None."]
    else:
        return resultList

def chatbot_response(user_input):
    input_lower = user_input.lower().strip()
    
    if input_lower.startswith("search for"):
        query = input_lower.replace("search for", "").strip()
        if query:
            return get_wikipedia_summary(query)
        else:
            return "Please specify what you want to search for."
    
    elif input_lower.startswith("hello") or input_lower.startswith("hi") or input_lower.startswith("hey"):
        return random.choice(responses["greetings"])
    
    else:
        tokens = input_lower.split()
        response = searchPAList(tokens)
        if response == ["I don't understand."]:
            if input_lower in responses:
                return responses[input_lower]
            else:
                return random.choice(list(responses.values()))
        else:
            return ' '.join(response)

if __name__ == "__main__":
    print("Hi, I'm Biblio.")
    print("Type 'search for [topic]' to get information from Wikipedia or ask specific questions.")
    print("For example, 'When was Albert Einstein born?' or 'What is the polar radius of Earth?'")
    print("Type 'bye' to exit.")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Biblio:", responses["goodbye"])
            break
        
        response = chatbot_response(user_input)
        print("Biblio:", response)
