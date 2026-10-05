import requests
import re
import json

url = 'https://app.ticketexito.com/main-MF3EVVE2.js'
js = requests.get(url).text
match = re.search(r'api_key:\"(.*?)\"', js)
if match:
    api_key = match.group(1)
    r = requests.get('https://api.ticketexito.com/web/events/trenalausi', headers={'x-api-key': api_key})
    data = r.json()
    with open('event_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
