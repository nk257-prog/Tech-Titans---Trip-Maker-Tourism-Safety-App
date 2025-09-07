from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import requests
import json
import os
import random
from datetime import datetime, timedelta
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuration
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
NOMINATIM_API_URL = "https://nominatim.openstreetmap.org/search"

# In-memory storage (replace with database in production)
users = {}
ratings = []
alerts = []
behavior_history = {}
active_sessions = {}
verification_codes = {}
blockchain_hashes = {}

# Tourist hotspots storage
tourist_locations = {}  # {user_id: {'lat': float, 'lng': float, 'timestamp': str, 'name': str}}
hotspots = []  # List of active hotspots

# Local language database
LOCAL_LANGUAGES = {
    # India
    'agra': {'language': 'Hindi', 'code': 'hi', 'script': 'Devanagari', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaad'},
    'delhi': {'language': 'Hindi', 'code': 'hi', 'script': 'Devanagari', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaad'},
    'mumbai': {'language': 'Hindi/Marathi', 'code': 'hi/mr', 'script': 'Devanagari', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaad'},
    'kolkata': {'language': 'Bengali', 'code': 'bn', 'script': 'Bengali', 'greeting': 'Nomoskar', 'thank_you': 'Dhonyobad'},
    'chennai': {'language': 'Tamil', 'code': 'ta', 'script': 'Tamil', 'greeting': 'Vanakkam', 'thank_you': 'Nandri'},
    'bangalore': {'language': 'Kannada', 'code': 'kn', 'script': 'Kannada', 'greeting': 'Namaskara', 'thank_you': 'Dhanyavaada'},
    'hyderabad': {'language': 'Telugu', 'code': 'te', 'script': 'Telugu', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaadulu'},
    'pune': {'language': 'Marathi', 'code': 'mr', 'script': 'Devanagari', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaad'},
    'ahmedabad': {'language': 'Gujarati', 'code': 'gu', 'script': 'Gujarati', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaad'},
    'jaipur': {'language': 'Hindi/Rajasthani', 'code': 'hi', 'script': 'Devanagari', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaad'},

    # South Indian States and Cities
    'tamil nadu': {'language': 'Tamil', 'code': 'ta', 'script': 'Tamil', 'greeting': 'Vanakkam', 'thank_you': 'Nandri'},
    'kerala': {'language': 'Malayalam', 'code': 'ml', 'script': 'Malayalam', 'greeting': 'Namaskaram', 'thank_you': 'Nanni'},
    'karnataka': {'language': 'Kannada', 'code': 'kn', 'script': 'Kannada', 'greeting': 'Namaskara', 'thank_you': 'Dhanyavaada'},
    'andhra pradesh': {'language': 'Telugu', 'code': 'te', 'script': 'Telugu', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaadulu'},
    'telangana': {'language': 'Telugu', 'code': 'te', 'script': 'Telugu', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaadulu'},

    # Major South Indian Cities
    'chennai': {'language': 'Tamil', 'code': 'ta', 'script': 'Tamil', 'greeting': 'Vanakkam', 'thank_you': 'Nandri'},
    'coimbatore': {'language': 'Tamil', 'code': 'ta', 'script': 'Tamil', 'greeting': 'Vanakkam', 'thank_you': 'Nandri'},
    'madurai': {'language': 'Tamil', 'code': 'ta', 'script': 'Tamil', 'greeting': 'Vanakkam', 'thank_you': 'Nandri'},
    'tiruchirappalli': {'language': 'Tamil', 'code': 'ta', 'script': 'Tamil', 'greeting': 'Vanakkam', 'thank_you': 'Nandri'},
    'salem': {'language': 'Tamil', 'code': 'ta', 'script': 'Tamil', 'greeting': 'Vanakkam', 'thank_you': 'Nandri'},
    'tirunelveli': {'language': 'Tamil', 'code': 'ta', 'script': 'Tamil', 'greeting': 'Vanakkam', 'thank_you': 'Nandri'},

    # Kerala Cities
    'thiruvananthapuram': {'language': 'Malayalam', 'code': 'ml', 'script': 'Malayalam', 'greeting': 'Namaskaram', 'thank_you': 'Nanni'},
    'kochi': {'language': 'Malayalam', 'code': 'ml', 'script': 'Malayalam', 'greeting': 'Namaskaram', 'thank_you': 'Nanni'},
    'kannur': {'language': 'Malayalam', 'code': 'ml', 'script': 'Malayalam', 'greeting': 'Namaskaram', 'thank_you': 'Nanni'},
    'kollam': {'language': 'Malayalam', 'code': 'ml', 'script': 'Malayalam', 'greeting': 'Namaskaram', 'thank_you': 'Nanni'},
    'thrissur': {'language': 'Malayalam', 'code': 'ml', 'script': 'Malayalam', 'greeting': 'Namaskaram', 'thank_you': 'Nanni'},

    # Karnataka Cities
    'mysore': {'language': 'Kannada', 'code': 'kn', 'script': 'Kannada', 'greeting': 'Namaskara', 'thank_you': 'Dhanyavaada'},
    'mangalore': {'language': 'Kannada', 'code': 'kn', 'script': 'Kannada', 'greeting': 'Namaskara', 'thank_you': 'Dhanyavaada'},
    'hubli': {'language': 'Kannada', 'code': 'kn', 'script': 'Kannada', 'greeting': 'Namaskara', 'thank_you': 'Dhanyavaada'},
    'belgaum': {'language': 'Kannada', 'code': 'kn', 'script': 'Kannada', 'greeting': 'Namaskara', 'thank_you': 'Dhanyavaada'},

    # Andhra Pradesh Cities
    'visakhapatnam': {'language': 'Telugu', 'code': 'te', 'script': 'Telugu', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaadulu'},
    'vijayawada': {'language': 'Telugu', 'code': 'te', 'script': 'Telugu', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaadulu'},
    'guntur': {'language': 'Telugu', 'code': 'te', 'script': 'Telugu', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaadulu'},
    'nellore': {'language': 'Telugu', 'code': 'te', 'script': 'Telugu', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaadulu'},

    # Telangana Cities
    'warangal': {'language': 'Telugu', 'code': 'te', 'script': 'Telugu', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaadulu'},
    'nizamabad': {'language': 'Telugu', 'code': 'te', 'script': 'Telugu', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaadulu'},
    'karimnagar': {'language': 'Telugu', 'code': 'te', 'script': 'Telugu', 'greeting': 'Namaste', 'thank_you': 'Dhanyavaadulu'},

    # International
    'paris': {'language': 'French', 'code': 'fr', 'script': 'Latin', 'greeting': 'Bonjour', 'thank_you': 'Merci'},
    'london': {'language': 'English', 'code': 'en', 'script': 'Latin', 'greeting': 'Hello', 'thank_you': 'Thank you'},
    'tokyo': {'language': 'Japanese', 'code': 'ja', 'script': 'Japanese', 'greeting': 'Konnichiwa', 'thank_you': 'Arigatou'},
    'beijing': {'language': 'Mandarin Chinese', 'code': 'zh', 'script': 'Chinese', 'greeting': 'Ni hao', 'thank_you': 'Xie xie'},
    'moscow': {'language': 'Russian', 'code': 'ru', 'script': 'Cyrillic', 'greeting': 'Privet', 'thank_you': 'Spasibo'},
    'cairo': {'language': 'Arabic', 'code': 'ar', 'script': 'Arabic', 'greeting': 'Marhaba', 'thank_you': 'Shukran'},
    'istanbul': {'language': 'Turkish', 'code': 'tr', 'script': 'Latin', 'greeting': 'Merhaba', 'thank_you': 'Teşekkürler'},
    'rio': {'language': 'Portuguese', 'code': 'pt', 'script': 'Latin', 'greeting': 'Olá', 'thank_you': 'Obrigado'},
    'sydney': {'language': 'English', 'code': 'en', 'script': 'Latin', 'greeting': 'Hello', 'thank_you': 'Thank you'},
    'dubai': {'language': 'Arabic', 'code': 'ar', 'script': 'Arabic', 'greeting': 'Marhaba', 'thank_you': 'Shukran'},

    # Additional European cities
    'rome': {'language': 'Italian', 'code': 'it', 'script': 'Latin', 'greeting': 'Ciao', 'thank_you': 'Grazie'},
    'barcelona': {'language': 'Spanish/Catalan', 'code': 'es/ca', 'script': 'Latin', 'greeting': 'Hola', 'thank_you': 'Gracias'},
    'amsterdam': {'language': 'Dutch', 'code': 'nl', 'script': 'Latin', 'greeting': 'Hallo', 'thank_you': 'Dank u'},
    'venice': {'language': 'Italian', 'code': 'it', 'script': 'Latin', 'greeting': 'Ciao', 'thank_you': 'Grazie'},
    'berlin': {'language': 'German', 'code': 'de', 'script': 'Latin', 'greeting': 'Hallo', 'thank_you': 'Danke'},
    'prague': {'language': 'Czech', 'code': 'cs', 'script': 'Latin', 'greeting': 'Ahoj', 'thank_you': 'Děkuji'},
    'vienna': {'language': 'German', 'code': 'de', 'script': 'Latin', 'greeting': 'Hallo', 'thank_you': 'Danke'},

    # Additional Asian cities
    'bangkok': {'language': 'Thai', 'code': 'th', 'script': 'Thai', 'greeting': 'Sawatdee', 'thank_you': 'Khop khun'},
    'singapore': {'language': 'English/Malay/Chinese', 'code': 'en/ms/zh', 'script': 'Latin/Chinese', 'greeting': 'Hello', 'thank_you': 'Thank you'},
    'seoul': {'language': 'Korean', 'code': 'ko', 'script': 'Korean', 'greeting': 'Annyeonghaseyo', 'thank_you': 'Gamsahamnida'},
    'hong kong': {'language': 'Cantonese/English', 'code': 'zh/en', 'script': 'Chinese/Latin', 'greeting': 'Nei ho', 'thank_you': 'M\'goi'},
    'shanghai': {'language': 'Mandarin Chinese', 'code': 'zh', 'script': 'Chinese', 'greeting': 'Ni hao', 'thank_you': 'Xie xie'},
    'kuala lumpur': {'language': 'Malay', 'code': 'ms', 'script': 'Latin', 'greeting': 'Selamat pagi', 'thank_you': 'Terima kasih'},

    # Additional American cities
    'los angeles': {'language': 'English', 'code': 'en', 'script': 'Latin', 'greeting': 'Hello', 'thank_you': 'Thank you'},
    'mexico city': {'language': 'Spanish', 'code': 'es', 'script': 'Latin', 'greeting': 'Hola', 'thank_you': 'Gracias'},
    'toronto': {'language': 'English', 'code': 'en', 'script': 'Latin', 'greeting': 'Hello', 'thank_you': 'Thank you'},
    'sao paulo': {'language': 'Portuguese', 'code': 'pt', 'script': 'Latin', 'greeting': 'Olá', 'thank_you': 'Obrigado'},
    'buenos aires': {'language': 'Spanish', 'code': 'es', 'script': 'Latin', 'greeting': 'Hola', 'thank_you': 'Gracias'},

    # Additional Middle Eastern cities
    'jerusalem': {'language': 'Hebrew/Arabic', 'code': 'he/ar', 'script': 'Hebrew/Arabic', 'greeting': 'Shalom/Marhaban', 'thank_you': 'Todah/Shukran'},
    'tel aviv': {'language': 'Hebrew', 'code': 'he', 'script': 'Hebrew', 'greeting': 'Shalom', 'thank_you': 'Todah'},
    'riyadh': {'language': 'Arabic', 'code': 'ar', 'script': 'Arabic', 'greeting': 'Marhaba', 'thank_you': 'Shukran'},

    # Additional African cities
    'cape town': {'language': 'English/Afrikaans', 'code': 'en/af', 'script': 'Latin', 'greeting': 'Hello', 'thank_you': 'Thank you'},
    'johannesburg': {'language': 'English/Zulu', 'code': 'en/zu', 'script': 'Latin', 'greeting': 'Hello', 'thank_you': 'Thank you'},
    'nairobi': {'language': 'Swahili/English', 'code': 'sw/en', 'script': 'Latin', 'greeting': 'Hujambo', 'thank_you': 'Asante'},

    # Additional Oceanian cities
    'melbourne': {'language': 'English', 'code': 'en', 'script': 'Latin', 'greeting': 'Hello', 'thank_you': 'Thank you'},
    'auckland': {'language': 'English/Maori', 'code': 'en/mi', 'script': 'Latin', 'greeting': 'Hello', 'thank_you': 'Thank you'}
}

# Common tourist phrases in different languages
TOURIST_PHRASES = {
    'hi': {  # Hindi
        'where_is': 'Kahaan hai',
        'how_much': 'Kitna hai',
        'water': 'Paani',
        'food': 'Khana',
        'help': 'Madad',
        'bathroom': 'Bathroom',
        'taxi': 'Taxi',
        'hotel': 'Hotel'
    },
    'fr': {  # French
        'where_is': 'Où est',
        'how_much': 'Combien',
        'water': 'Eau',
        'food': 'Nourriture',
        'help': 'Aide',
        'bathroom': 'Toilettes',
        'taxi': 'Taxi',
        'hotel': 'Hôtel'
    },
    'ja': {  # Japanese
        'where_is': 'Doko desu ka',
        'how_much': 'Ikura desu ka',
        'water': 'Mizu',
        'food': 'Tabemono',
        'help': 'Tasukete',
        'bathroom': 'Toire',
        'taxi': 'Takushī',
        'hotel': 'Hoteru'
    },
    'zh': {  # Mandarin
        'where_is': 'Zài nǎlǐ',
        'how_much': 'Duōshǎo qián',
        'water': 'Shuǐ',
        'food': 'Shíwù',
        'help': 'Bāngmáng',
        'bathroom': 'Cèsuǒ',
        'taxi': 'Chūzūchē',
        'hotel': 'Fàndiàn'
    },
    'ar': {  # Arabic
        'where_is': 'Ayna',
        'how_much': 'Kam athaman',
        'water': 'Maa',
        'food': 'Taam',
        'help': 'Musaeada',
        'bathroom': 'Hammam',
        'taxi': 'Taxi',
        'hotel': 'Funduq'
    },
    'it': {  # Italian
        'where_is': 'Dove è',
        'how_much': 'Quanto costa',
        'water': 'Acqua',
        'food': 'Cibo',
        'help': 'Aiuto',
        'bathroom': 'Bagno',
        'taxi': 'Taxi',
        'hotel': 'Hotel'
    },
    'es': {  # Spanish
        'where_is': 'Dónde está',
        'how_much': 'Cuánto cuesta',
        'water': 'Agua',
        'food': 'Comida',
        'help': 'Ayuda',
        'bathroom': 'Baño',
        'taxi': 'Taxi',
        'hotel': 'Hotel'
    },
    'nl': {  # Dutch
        'where_is': 'Waar is',
        'how_much': 'Hoeveel kost',
        'water': 'Water',
        'food': 'Eten',
        'help': 'Help',
        'bathroom': 'Toilet',
        'taxi': 'Taxi',
        'hotel': 'Hotel'
    },
    'de': {  # German
        'where_is': 'Wo ist',
        'how_much': 'Wie viel kostet',
        'water': 'Wasser',
        'food': 'Essen',
        'help': 'Hilfe',
        'bathroom': 'Toilette',
        'taxi': 'Taxi',
        'hotel': 'Hotel'
    },
    'th': {  # Thai
        'where_is': 'Yù tîi nǎi',
        'how_much': 'Tao rai',
        'water': 'Nám',
        'food': 'A-hǎan',
        'help': 'Chûay dâi mǎi',
        'bathroom': 'Hông nám',
        'taxi': 'Tæksi',
        'hotel': 'Rong ræm'
    },
    'ko': {  # Korean
        'where_is': 'Eodisseoyo',
        'how_much': 'Eolmayeoyo',
        'water': 'Mul',
        'food': 'Eumsik',
        'help': 'Dowajuseyo',
        'bathroom': 'Hwajangsil',
        'taxi': 'Taeksi',
        'hotel': 'Hotel'
    },
    'pt': {  # Portuguese
        'where_is': 'Onde fica',
        'how_much': 'Quanto custa',
        'water': 'Água',
        'food': 'Comida',
        'help': 'Ajuda',
        'bathroom': 'Banheiro',
        'taxi': 'Táxi',
        'hotel': 'Hotel'
    },
    'he': {  # Hebrew
        'where_is': 'Eifo',
        'how_much': 'Kama ze oleh',
        'water': 'Mayim',
        'food': 'Ochla',
        'help': 'Ezra',
        'bathroom': 'Sherutim',
        'taxi': 'Mona',
        'hotel': 'Malon'
    },
    'cs': {  # Czech
        'where_is': 'Kde je',
        'how_much': 'Kolik stojí',
        'water': 'Voda',
        'food': 'Jídlo',
        'help': 'Pomoc',
        'bathroom': 'Toaleta',
        'taxi': 'Taxi',
        'hotel': 'Hotel'
    },
    'ms': {  # Malay
        'where_is': 'Di mana',
        'how_much': 'Berapa harganya',
        'water': 'Air',
        'food': 'Makanan',
        'help': 'Tolong',
        'bathroom': 'Tandas',
        'taxi': 'Teksi',
        'hotel': 'Hotel'
    },
    'sw': {  # Swahili
        'where_is': 'Iko wapi',
        'how_much': 'Ni bei gani',
        'water': 'Maji',
        'food': 'Chakula',
        'help': 'Msaada',
        'bathroom': 'Choo',
        'taxi': 'Teksi',
        'hotel': 'Hoteli'
    },
    'mi': {  # Maori
        'where_is': 'Kei hea',
        'how_much': 'E hia te utu',
        'water': 'Wai',
        'food': 'Kai',
        'help': 'Awhina',
        'bathroom': 'Wharepaku',
        'taxi': 'Tākihi',
        'hotel': 'Hōtēra'
    },
    'ta': {  # Tamil
        'where_is': 'Enga irukku',
        'how_much': 'Evalavu',
        'water': 'Thanni',
        'food': 'Sapadu',
        'help': 'Udavi',
        'bathroom': 'Kachavadi',
        'taxi': 'Taxi',
        'hotel': 'Hotel'
    },
    'te': {  # Telugu
        'where_is': 'Ekkada undi',
        'how_much': 'Enta',
        'water': 'Neellu',
        'food': 'Bhojanam',
        'help': 'Sahayam',
        'bathroom': 'Sulabh kendram',
        'taxi': 'Taxi',
        'hotel': 'Hotel'
    },
    'kn': {  # Kannada
        'where_is': 'Ellide',
        'how_much': 'Eshtu',
        'water': 'Neeru',
        'food': 'Oota',
        'help': 'Sahaya',
        'bathroom': 'Sulabh kendra',
        'taxi': 'Taxi',
        'hotel': 'Hotel'
    },
    'ml': {  # Malayalam
        'where_is': 'Evide',
        'how_much': 'Etta',
        'water': 'Vellam',
        'food': 'Bhojanam',
        'help': 'Sahayam',
        'bathroom': 'Sulabh kendram',
        'taxi': 'Taxi',
        'hotel': 'Hotel'
    }
}

# Weather code mappings
WEATHER_CODES = {
    0: {"description": "Clear sky", "icon": "☀️"},
    1: {"description": "Mainly clear", "icon": "🌤️"},
    2: {"description": "Partly cloudy", "icon": "⛅"},
    3: {"description": "Overcast", "icon": "☁️"},
    45: {"description": "Fog", "icon": "🌫️"},
    48: {"description": "Depositing rime fog", "icon": "🌫️"},
    51: {"description": "Light drizzle", "icon": "🌦️"},
    53: {"description": "Moderate drizzle", "icon": "🌦️"},
    55: {"description": "Dense drizzle", "icon": "🌦️"},
    56: {"description": "Light freezing drizzle", "icon": "🌨️"},
    57: {"description": "Dense freezing drizzle", "icon": "🌨️"},
    61: {"description": "Slight rain", "icon": "🌧️"},
    63: {"description": "Moderate rain", "icon": "🌧️"},
    65: {"description": "Heavy rain", "icon": "🌧️"},
    66: {"description": "Light freezing rain", "icon": "🌨️"},
    67: {"description": "Heavy freezing rain", "icon": "🌨️"},
    71: {"description": "Slight snow fall", "icon": "❄️"},
    73: {"description": "Moderate snow fall", "icon": "❄️"},
    75: {"description": "Heavy snow fall", "icon": "❄️"},
    77: {"description": "Snow grains", "icon": "❄️"},
    80: {"description": "Slight rain showers", "icon": "🌦️"},
    81: {"description": "Moderate rain showers", "icon": "🌦️"},
    82: {"description": "Violent rain showers", "icon": "🌧️"},
    85: {"description": "Slight snow showers", "icon": "❄️"},
    86: {"description": "Heavy snow showers", "icon": "❄️"},
    95: {"description": "Thunderstorm", "icon": "⛈️"},
    96: {"description": "Thunderstorm with slight hail", "icon": "⛈️"},
    99: {"description": "Thunderstorm with heavy hail", "icon": "⛈️"}
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/weather')
def get_weather():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)

    if not lat or not lng:
        return jsonify({'error': 'Latitude and longitude required'}), 400

    try:
        params = {
            'latitude': lat,
            'longitude': lng,
            'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m',
            'timezone': 'auto'
        }

        response = requests.get(WEATHER_API_URL, params=params)
        data = response.json()

        if 'current' in data:
            weather_info = WEATHER_CODES.get(data['current']['weather_code'],
                                            {'description': 'Unknown', 'icon': '❓'})

            weather_data = {
                'temperature': round(data['current']['temperature_2m']),
                'feels_like': round(data['current']['apparent_temperature']),
                'humidity': data['current']['relative_humidity_2m'],
                'wind_speed': data['current']['wind_speed_10m'],
                'precipitation': data['current']['precipitation'],
                'description': weather_info['description'],
                'icon': weather_info['icon'],
                'coordinates': f"{data['latitude']:.4f}, {data['longitude']:.4f}"
            }

            # Check for weather alerts
            alerts = check_weather_alerts(data['current'])
            if alerts:
                weather_data['alerts'] = alerts
                log_alert('weather_alert', f"Weather alerts at {weather_data['coordinates']}", {
                    'alerts': alerts,
                    'weather': weather_data
                })

            return jsonify(weather_data)
        else:
            return jsonify({'error': 'Weather data not available'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_wikipedia_info(location_name):
    """Get Wikipedia page information using Wikimedia REST API"""
    try:
        # Clean location name for Wikipedia
        clean_name = location_name.split(',')[0].strip()

        # Use Wikimedia REST API to get page summary
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_name.replace(' ', '_')}"

        response = requests.get(summary_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'title': data.get('title', clean_name),
                'url': f"https://en.wikipedia.org/wiki/{clean_name.replace(' ', '_')}",
                'description': data.get('extract', f'Learn more about {clean_name} on Wikipedia').split('.')[0] + '.',
                'thumbnail': data.get('thumbnail', {}).get('source') if data.get('thumbnail') else None
            }
        else:
            # Fallback: try with different capitalization or search
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={clean_name}&format=json&srlimit=1"
            search_response = requests.get(search_url, timeout=5)
            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data.get('query', {}).get('search'):
                    found_title = search_data['query']['search'][0]['title']
                    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{found_title.replace(' ', '_')}"
                    summary_response = requests.get(summary_url, timeout=5)
                    if summary_response.status_code == 200:
                        data = summary_response.json()
                        return {
                            'title': data.get('title', found_title),
                            'url': f"https://en.wikipedia.org/wiki/{found_title.replace(' ', '_')}",
                            'description': data.get('extract', f'Learn more about {found_title} on Wikipedia').split('.')[0] + '.',
                            'thumbnail': data.get('thumbnail', {}).get('source') if data.get('thumbnail') else None
                        }

        return None

    except Exception as e:
        print(f"Wikipedia API error: {e}")
        return None

def get_wikipedia_attractions(location):
    """Get tourist attractions for a location using Wikipedia search"""
    try:
        # Multiple search queries for better results
        search_queries = [
            f"tourist attractions in {location}",
            f"places to visit in {location}",
            f"landmarks in {location}",
            f"sights in {location}",
            f"points of interest in {location}"
        ]

        all_attractions = []
        seen_titles = set()

        for query in search_queries:
            search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=5&namespace=0&format=json"
            response = requests.get(search_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for title in data[1]:  # data[1] contains the list of page titles
                    # Filter out irrelevant results
                    if (title not in seen_titles and
                        not any(word in title.lower() for word in ['list of', 'category:', 'template:', 'wikipedia:', 'file:', 'portal:']) and
                        len(title) > 3):
                        all_attractions.append({
                            'name': title,
                            'url': f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                            'type': 'wikipedia'
                        })
                        seen_titles.add(title)

        # Add some popular attractions for major cities if we have few results
        if len(all_attractions) < 5:
            popular_attractions = get_popular_attractions(location)
            for attraction in popular_attractions:
                if attraction['name'] not in seen_titles:
                    all_attractions.append(attraction)
                    seen_titles.add(attraction['name'])

        return all_attractions[:10]  # Limit to 10 attractions
    except Exception as e:
        print(f"Wikipedia attractions error: {e}")
        return []

def get_popular_attractions(location):
    """Get popular attractions for major locations"""
    location_lower = location.lower()

    popular_spots = {
        # India
        'agra': [
            {'name': 'Taj Mahal', 'url': 'https://en.wikipedia.org/wiki/Taj_Mahal', 'type': 'popular'},
            {'name': 'Agra Fort', 'url': 'https://en.wikipedia.org/wiki/Agra_Fort', 'type': 'popular'},
            {'name': 'Fatehpur Sikri', 'url': 'https://en.wikipedia.org/wiki/Fatehpur_Sikri', 'type': 'popular'},
            {'name': 'Itmad-ud-Daula', 'url': 'https://en.wikipedia.org/wiki/Itmad-ud-Daula', 'type': 'popular'}
        ],
        'delhi': [
            {'name': 'Red Fort', 'url': 'https://en.wikipedia.org/wiki/Red_Fort', 'type': 'popular'},
            {'name': 'India Gate', 'url': 'https://en.wikipedia.org/wiki/India_Gate', 'type': 'popular'},
            {'name': 'Qutub Minar', 'url': 'https://en.wikipedia.org/wiki/Qutub_Minar', 'type': 'popular'},
            {'name': 'Lotus Temple', 'url': 'https://en.wikipedia.org/wiki/Lotus_Temple', 'type': 'popular'},
            {'name': 'Humayun\'s Tomb', 'url': 'https://en.wikipedia.org/wiki/Humayun%27s_Tomb', 'type': 'popular'}
        ],
        'mumbai': [
            {'name': 'Gateway of India', 'url': 'https://en.wikipedia.org/wiki/Gateway_of_India', 'type': 'popular'},
            {'name': 'Marine Drive', 'url': 'https://en.wikipedia.org/wiki/Marine_Drive,_Mumbai', 'type': 'popular'},
            {'name': 'Elephanta Caves', 'url': 'https://en.wikipedia.org/wiki/Elephanta_Caves', 'type': 'popular'},
            {'name': 'Chhatrapati Shivaji Terminus', 'url': 'https://en.wikipedia.org/wiki/Chhatrapati_Shivaji_Terminus', 'type': 'popular'},
            {'name': 'Juhu Beach', 'url': 'https://en.wikipedia.org/wiki/Juhu_Beach', 'type': 'popular'}
        ],
        'kolkata': [
            {'name': 'Victoria Memorial', 'url': 'https://en.wikipedia.org/wiki/Victoria_Memorial,_Kolkata', 'type': 'popular'},
            {'name': 'Howrah Bridge', 'url': 'https://en.wikipedia.org/wiki/Howrah_Bridge', 'type': 'popular'},
            {'name': 'Marble Palace', 'url': 'https://en.wikipedia.org/wiki/Marble_Palace,_Kolkata', 'type': 'popular'},
            {'name': 'South City Mall', 'url': 'https://en.wikipedia.org/wiki/South_City_Mall', 'type': 'popular'}
        ],
        'chennai': [
            {'name': 'Marina Beach', 'url': 'https://en.wikipedia.org/wiki/Marina_Beach', 'type': 'popular'},
            {'name': 'Kapaleeshwarar Temple', 'url': 'https://en.wikipedia.org/wiki/Kapaleeshwarar_Temple', 'type': 'popular'},
            {'name': 'Fort St. George', 'url': 'https://en.wikipedia.org/wiki/Fort_St._George,_India', 'type': 'popular'},
            {'name': 'San Thome Basilica', 'url': 'https://en.wikipedia.org/wiki/San_Thome_Basilica', 'type': 'popular'}
        ],
        'bangalore': [
            {'name': 'Bangalore Palace', 'url': 'https://en.wikipedia.org/wiki/Bangalore_Palace', 'type': 'popular'},
            {'name': 'Lalbagh Botanical Garden', 'url': 'https://en.wikipedia.org/wiki/Lalbagh', 'type': 'popular'},
            {'name': 'Cubbon Park', 'url': 'https://en.wikipedia.org/wiki/Cubbon_Park', 'type': 'popular'},
            {'name': 'Vidhana Soudha', 'url': 'https://en.wikipedia.org/wiki/Vidhana_Soudha', 'type': 'popular'}
        ],
        'hyderabad': [
            {'name': 'Charminar', 'url': 'https://en.wikipedia.org/wiki/Charminar', 'type': 'popular'},
            {'name': 'Golconda Fort', 'url': 'https://en.wikipedia.org/wiki/Golconda', 'type': 'popular'},
            {'name': 'Hussain Sagar', 'url': 'https://en.wikipedia.org/wiki/Hussain_Sagar', 'type': 'popular'},
            {'name': 'Salar Jung Museum', 'url': 'https://en.wikipedia.org/wiki/Salar_Jung_Museum', 'type': 'popular'}
        ],
        'pune': [
            {'name': 'Shaniwar Wada', 'url': 'https://en.wikipedia.org/wiki/Shaniwar_Wada', 'type': 'popular'},
            {'name': 'Aga Khan Palace', 'url': 'https://en.wikipedia.org/wiki/Aga_Khan_Palace', 'type': 'popular'},
            {'name': 'Sinhagad Fort', 'url': 'https://en.wikipedia.org/wiki/Sinhagad', 'type': 'popular'},
            {'name': 'Parvati Hill', 'url': 'https://en.wikipedia.org/wiki/Parvati_Hill', 'type': 'popular'}
        ],
        'jaipur': [
            {'name': 'Amber Fort', 'url': 'https://en.wikipedia.org/wiki/Amber_Fort', 'type': 'popular'},
            {'name': 'City Palace, Jaipur', 'url': 'https://en.wikipedia.org/wiki/City_Palace,_Jaipur', 'type': 'popular'},
            {'name': 'Hawa Mahal', 'url': 'https://en.wikipedia.org/wiki/Hawa_Mahal', 'type': 'popular'},
            {'name': 'Jantar Mantar, Jaipur', 'url': 'https://en.wikipedia.org/wiki/Jantar_Mantar,_Jaipur', 'type': 'popular'}
        ],

        # South Indian States and Cities
        'tamil nadu': [
            {'name': 'Marina Beach', 'url': 'https://en.wikipedia.org/wiki/Marina_Beach', 'type': 'popular'},
            {'name': 'Meenakshi Temple', 'url': 'https://en.wikipedia.org/wiki/Meenakshi_Temple', 'type': 'popular'},
            {'name': 'Brihadeeswarar Temple', 'url': 'https://en.wikipedia.org/wiki/Brihadeeswarar_Temple', 'type': 'popular'},
            {'name': 'Kanyakumari', 'url': 'https://en.wikipedia.org/wiki/Kanyakumari', 'type': 'popular'},
            {'name': 'Ooty', 'url': 'https://en.wikipedia.org/wiki/Ooty', 'type': 'popular'},
            {'name': 'Mahabalipuram', 'url': 'https://en.wikipedia.org/wiki/Mahabalipuram', 'type': 'popular'}
        ],
        'chennai': [
            {'name': 'Marina Beach', 'url': 'https://en.wikipedia.org/wiki/Marina_Beach', 'type': 'popular'},
            {'name': 'Kapaleeshwarar Temple', 'url': 'https://en.wikipedia.org/wiki/Kapaleeshwarar_Temple', 'type': 'popular'},
            {'name': 'Fort St. George', 'url': 'https://en.wikipedia.org/wiki/Fort_St._George,_India', 'type': 'popular'},
            {'name': 'San Thome Basilica', 'url': 'https://en.wikipedia.org/wiki/San_Thome_Basilica', 'type': 'popular'},
            {'name': 'Valluvar Kottam', 'url': 'https://en.wikipedia.org/wiki/Valluvar_Kottam', 'type': 'popular'}
        ],
        'coimbatore': [
            {'name': 'Marudamalai Temple', 'url': 'https://en.wikipedia.org/wiki/Marudamalai_Temple', 'type': 'popular'},
            {'name': 'Perur Pateeswarar Temple', 'url': 'https://en.wikipedia.org/wiki/Perur_Pateeswarar_Temple', 'type': 'popular'},
            {'name': 'VOC Park', 'url': 'https://en.wikipedia.org/wiki/VOC_Park_and_Zoo', 'type': 'popular'},
            {'name': 'Anamalai Tiger Reserve', 'url': 'https://en.wikipedia.org/wiki/Anamalai_Tiger_Reserve', 'type': 'popular'}
        ],
        'madurai': [
            {'name': 'Meenakshi Temple', 'url': 'https://en.wikipedia.org/wiki/Meenakshi_Temple', 'type': 'popular'},
            {'name': 'Thirumalai Nayakkar Mahal', 'url': 'https://en.wikipedia.org/wiki/Thirumalai_Nayakkar_Mahal', 'type': 'popular'},
            {'name': 'Gandhi Memorial Museum', 'url': 'https://en.wikipedia.org/wiki/Gandhi_Memorial_Museum,_Madurai', 'type': 'popular'},
            {'name': 'Vaigai Dam', 'url': 'https://en.wikipedia.org/wiki/Vaigai_Dam', 'type': 'popular'}
        ],
        'tiruchirappalli': [
            {'name': 'Sri Ranganathaswamy Temple', 'url': 'https://en.wikipedia.org/wiki/Sri_Ranganathaswamy_Temple', 'type': 'popular'},
            {'name': 'Rockfort', 'url': 'https://en.wikipedia.org/wiki/Rockfort,_Tiruchirappalli', 'type': 'popular'},
            {'name': 'Jambukeswarar Temple', 'url': 'https://en.wikipedia.org/wiki/Jambukeswarar_Temple,_Tiruchirappalli', 'type': 'popular'},
            {'name': 'St. Joseph\'s College', 'url': 'https://en.wikipedia.org/wiki/St._Joseph%27s_College,_Tiruchirappalli', 'type': 'popular'}
        ],

        # Kerala
        'kerala': [
            {'name': 'Backwaters of Kerala', 'url': 'https://en.wikipedia.org/wiki/Kerala_backwaters', 'type': 'popular'},
            {'name': 'Munnar', 'url': 'https://en.wikipedia.org/wiki/Munnar', 'type': 'popular'},
            {'name': 'Periyar National Park', 'url': 'https://en.wikipedia.org/wiki/Periyar_National_Park', 'type': 'popular'},
            {'name': 'Kovalam Beach', 'url': 'https://en.wikipedia.org/wiki/Kovalam', 'type': 'popular'},
            {'name': 'Wayanad Wildlife Sanctuary', 'url': 'https://en.wikipedia.org/wiki/Wayanad_Wildlife_Sanctuary', 'type': 'popular'},
            {'name': 'Alleppey', 'url': 'https://en.wikipedia.org/wiki/Alappuzha', 'type': 'popular'}
        ],
        'thiruvananthapuram': [
            {'name': 'Padmanabhaswamy Temple', 'url': 'https://en.wikipedia.org/wiki/Sree_Padmanabhaswamy_Temple', 'type': 'popular'},
            {'name': 'Kovalam Beach', 'url': 'https://en.wikipedia.org/wiki/Kovalam', 'type': 'popular'},
            {'name': 'Napier Museum', 'url': 'https://en.wikipedia.org/wiki/Napier_Museum', 'type': 'popular'},
            {'name': 'Shanghumukham Beach', 'url': 'https://en.wikipedia.org/wiki/Shanghumukham_Beach', 'type': 'popular'}
        ],
        'kochi': [
            {'name': 'Fort Kochi', 'url': 'https://en.wikipedia.org/wiki/Fort_Kochi', 'type': 'popular'},
            {'name': 'Chinese Fishing Nets', 'url': 'https://en.wikipedia.org/wiki/Chinese_fishing_nets', 'type': 'popular'},
            {'name': 'Maritime Museum', 'url': 'https://en.wikipedia.org/wiki/Indian_Navy_Maritime_Museum', 'type': 'popular'},
            {'name': 'Indo-Portuguese Museum', 'url': 'https://en.wikipedia.org/wiki/Indo-Portuguese_Museum', 'type': 'popular'}
        ],
        'kannur': [
            {'name': 'Muzhappilangad Beach', 'url': 'https://en.wikipedia.org/wiki/Muzhappilangad_Beach', 'type': 'popular'},
            {'name': 'St. Angelo Fort', 'url': 'https://en.wikipedia.org/wiki/St._Angelo_Fort', 'type': 'popular'},
            {'name': 'Payyambalam Beach', 'url': 'https://en.wikipedia.org/wiki/Payyambalam_Beach', 'type': 'popular'},
            {'name': 'Aralam Wildlife Sanctuary', 'url': 'https://en.wikipedia.org/wiki/Aralam_Wildlife_Sanctuary', 'type': 'popular'}
        ],

        # Karnataka
        'karnataka': [
            {'name': 'Mysore Palace', 'url': 'https://en.wikipedia.org/wiki/Mysore_Palace', 'type': 'popular'},
            {'name': 'Hampi', 'url': 'https://en.wikipedia.org/wiki/Hampi', 'type': 'popular'},
            {'name': 'Badami Caves', 'url': 'https://en.wikipedia.org/wiki/Badami_cave_temples', 'type': 'popular'},
            {'name': 'Gokarna', 'url': 'https://en.wikipedia.org/wiki/Gokarna,_Karnataka', 'type': 'popular'},
            {'name': 'Coorg', 'url': 'https://en.wikipedia.org/wiki/Coorg', 'type': 'popular'},
            {'name': 'Bandipur National Park', 'url': 'https://en.wikipedia.org/wiki/Bandipur_National_Park', 'type': 'popular'}
        ],
        'mysore': [
            {'name': 'Mysore Palace', 'url': 'https://en.wikipedia.org/wiki/Mysore_Palace', 'type': 'popular'},
            {'name': 'Chamundi Hill', 'url': 'https://en.wikipedia.org/wiki/Chamundi_Hill', 'type': 'popular'},
            {'name': 'St. Philomena\'s Cathedral', 'url': 'https://en.wikipedia.org/wiki/St._Philomena%27s_Cathedral,_Mysore', 'type': 'popular'},
            {'name': 'Brindavan Gardens', 'url': 'https://en.wikipedia.org/wiki/Brindavan_Gardens', 'type': 'popular'}
        ],
        'mangalore': [
            {'name': 'Panambur Beach', 'url': 'https://en.wikipedia.org/wiki/Panambur_Beach', 'type': 'popular'},
            {'name': 'Kadri Manjunath Temple', 'url': 'https://en.wikipedia.org/wiki/Kadri_Manjunath_Temple', 'type': 'popular'},
            {'name': 'Sultan Battery', 'url': 'https://en.wikipedia.org/wiki/Sultan_Battery', 'type': 'popular'},
            {'name': 'Tannirbhavi Beach', 'url': 'https://en.wikipedia.org/wiki/Tannirbhavi_Beach', 'type': 'popular'}
        ],

        # Andhra Pradesh
        'andhra pradesh': [
            {'name': 'Tirupati Temple', 'url': 'https://en.wikipedia.org/wiki/Tirupati', 'type': 'popular'},
            {'name': 'Lepakshi', 'url': 'https://en.wikipedia.org/wiki/Lepakshi', 'type': 'popular'},
            {'name': 'Amaravati', 'url': 'https://en.wikipedia.org/wiki/Amaravati,_Andhra_Pradesh', 'type': 'popular'},
            {'name': 'Araku Valley', 'url': 'https://en.wikipedia.org/wiki/Araku_Valley', 'type': 'popular'},
            {'name': 'Srisailam', 'url': 'https://en.wikipedia.org/wiki/Srisailam', 'type': 'popular'}
        ],
        'visakhapatnam': [
            {'name': 'RK Beach', 'url': 'https://en.wikipedia.org/wiki/RK_Beach', 'type': 'popular'},
            {'name': 'Kailasagiri', 'url': 'https://en.wikipedia.org/wiki/Kailasagiri', 'type': 'popular'},
            {'name': 'Simhachalam Temple', 'url': 'https://en.wikipedia.org/wiki/Simhachalam_Temple', 'type': 'popular'},
            {'name': 'Indira Gandhi Zoological Park', 'url': 'https://en.wikipedia.org/wiki/Indira_Gandhi_Zoological_Park', 'type': 'popular'}
        ],
        'vijayawada': [
            {'name': 'Kanakadurga Temple', 'url': 'https://en.wikipedia.org/wiki/Kanakadurga_Temple', 'type': 'popular'},
            {'name': 'Prakasam Barrage', 'url': 'https://en.wikipedia.org/wiki/Prakasam_Barrage', 'type': 'popular'},
            {'name': 'Undavalli Caves', 'url': 'https://en.wikipedia.org/wiki/Undavalli_Caves', 'type': 'popular'},
            {'name': 'Bhavani Island', 'url': 'https://en.wikipedia.org/wiki/Bhavani_Island', 'type': 'popular'}
        ],

        # Telangana
        'telangana': [
            {'name': 'Charminar', 'url': 'https://en.wikipedia.org/wiki/Charminar', 'type': 'popular'},
            {'name': 'Golconda Fort', 'url': 'https://en.wikipedia.org/wiki/Golconda', 'type': 'popular'},
            {'name': 'Hussain Sagar', 'url': 'https://en.wikipedia.org/wiki/Hussain_Sagar', 'type': 'popular'},
            {'name': 'Salar Jung Museum', 'url': 'https://en.wikipedia.org/wiki/Salar_Jung_Museum', 'type': 'popular'},
            {'name': 'Birla Mandir', 'url': 'https://en.wikipedia.org/wiki/Birla_Mandir,_Hyderabad', 'type': 'popular'}
        ],
        'warangal': [
            {'name': 'Warangal Fort', 'url': 'https://en.wikipedia.org/wiki/Warangal_Fort', 'type': 'popular'},
            {'name': 'Thousand Pillar Temple', 'url': 'https://en.wikipedia.org/wiki/Thousand_Pillar_Temple', 'type': 'popular'},
            {'name': 'Ramappa Temple', 'url': 'https://en.wikipedia.org/wiki/Ramappa_Temple', 'type': 'popular'},
            {'name': 'Bhadrakali Temple', 'url': 'https://en.wikipedia.org/wiki/Bhadrakali_Temple,_Warangal', 'type': 'popular'}
        ],

        # Europe
        'paris': [
            {'name': 'Eiffel Tower', 'url': 'https://en.wikipedia.org/wiki/Eiffel_Tower', 'type': 'popular'},
            {'name': 'Louvre Museum', 'url': 'https://en.wikipedia.org/wiki/Louvre', 'type': 'popular'},
            {'name': 'Notre-Dame de Paris', 'url': 'https://en.wikipedia.org/wiki/Notre-Dame_de_Paris', 'type': 'popular'},
            {'name': 'Champs-Élysées', 'url': 'https://en.wikipedia.org/wiki/Champs-%C3%89lys%C3%A9es', 'type': 'popular'},
            {'name': 'Arc de Triomphe', 'url': 'https://en.wikipedia.org/wiki/Arc_de_Triomphe', 'type': 'popular'},
            {'name': 'Montmartre', 'url': 'https://en.wikipedia.org/wiki/Montmartre', 'type': 'popular'}
        ],
        'london': [
            {'name': 'Big Ben', 'url': 'https://en.wikipedia.org/wiki/Big_Ben', 'type': 'popular'},
            {'name': 'Tower of London', 'url': 'https://en.wikipedia.org/wiki/Tower_of_London', 'type': 'popular'},
            {'name': 'British Museum', 'url': 'https://en.wikipedia.org/wiki/British_Museum', 'type': 'popular'},
            {'name': 'London Eye', 'url': 'https://en.wikipedia.org/wiki/London_Eye', 'type': 'popular'},
            {'name': 'Buckingham Palace', 'url': 'https://en.wikipedia.org/wiki/Buckingham_Palace', 'type': 'popular'},
            {'name': 'Tower Bridge', 'url': 'https://en.wikipedia.org/wiki/Tower_Bridge', 'type': 'popular'}
        ],
        'rome': [
            {'name': 'Colosseum', 'url': 'https://en.wikipedia.org/wiki/Colosseum', 'type': 'popular'},
            {'name': 'Roman Forum', 'url': 'https://en.wikipedia.org/wiki/Roman_Forum', 'type': 'popular'},
            {'name': 'Vatican City', 'url': 'https://en.wikipedia.org/wiki/Vatican_City', 'type': 'popular'},
            {'name': 'Trevi Fountain', 'url': 'https://en.wikipedia.org/wiki/Trevi_Fountain', 'type': 'popular'},
            {'name': 'Pantheon, Rome', 'url': 'https://en.wikipedia.org/wiki/Pantheon,_Rome', 'type': 'popular'}
        ],
        'barcelona': [
            {'name': 'Sagrada Família', 'url': 'https://en.wikipedia.org/wiki/Sagrada_Fam%C3%ADlia', 'type': 'popular'},
            {'name': 'Park Güell', 'url': 'https://en.wikipedia.org/wiki/Park_G%C3%BCell', 'type': 'popular'},
            {'name': 'La Rambla', 'url': 'https://en.wikipedia.org/wiki/La_Rambla,_Barcelona', 'type': 'popular'},
            {'name': 'Gothic Quarter, Barcelona', 'url': 'https://en.wikipedia.org/wiki/Gothic_Quarter,_Barcelona', 'type': 'popular'},
            {'name': 'Camp Nou', 'url': 'https://en.wikipedia.org/wiki/Camp_Nou', 'type': 'popular'}
        ],
        'amsterdam': [
            {'name': 'Rijksmuseum', 'url': 'https://en.wikipedia.org/wiki/Rijksmuseum', 'type': 'popular'},
            {'name': 'Anne Frank House', 'url': 'https://en.wikipedia.org/wiki/Anne_Frank_House', 'type': 'popular'},
            {'name': 'Vondelpark', 'url': 'https://en.wikipedia.org/wiki/Vondelpark', 'type': 'popular'},
            {'name': 'Canal ring', 'url': 'https://en.wikipedia.org/wiki/Amsterdam_canal_ring', 'type': 'popular'}
        ],
        'venice': [
            {'name': 'St. Mark\'s Square', 'url': 'https://en.wikipedia.org/wiki/St._Mark%27s_Square', 'type': 'popular'},
            {'name': 'St. Mark\'s Basilica', 'url': 'https://en.wikipedia.org/wiki/St._Mark%27s_Basilica', 'type': 'popular'},
            {'name': 'Doge\'s Palace', 'url': 'https://en.wikipedia.org/wiki/Doge%27s_Palace', 'type': 'popular'},
            {'name': 'Rialto Bridge', 'url': 'https://en.wikipedia.org/wiki/Rialto_Bridge', 'type': 'popular'}
        ],

        # Asia
        'tokyo': [
            {'name': 'Tokyo Tower', 'url': 'https://en.wikipedia.org/wiki/Tokyo_Tower', 'type': 'popular'},
            {'name': 'Senso-ji', 'url': 'https://en.wikipedia.org/wiki/Sens%C5%8D-ji', 'type': 'popular'},
            {'name': 'Meiji Shrine', 'url': 'https://en.wikipedia.org/wiki/Meiji_Shrine', 'type': 'popular'},
            {'name': 'Tokyo Skytree', 'url': 'https://en.wikipedia.org/wiki/Tokyo_Skytree', 'type': 'popular'},
            {'name': 'Shibuya Crossing', 'url': 'https://en.wikipedia.org/wiki/Shibuya_Crossing', 'type': 'popular'},
            {'name': 'Imperial Palace', 'url': 'https://en.wikipedia.org/wiki/Imperial_Palace', 'type': 'popular'}
        ],
        'beijing': [
            {'name': 'Great Wall of China', 'url': 'https://en.wikipedia.org/wiki/Great_Wall_of_China', 'type': 'popular'},
            {'name': 'Forbidden City', 'url': 'https://en.wikipedia.org/wiki/Forbidden_City', 'type': 'popular'},
            {'name': 'Tiananmen Square', 'url': 'https://en.wikipedia.org/wiki/Tiananmen_Square', 'type': 'popular'},
            {'name': 'Summer Palace', 'url': 'https://en.wikipedia.org/wiki/Summer_Palace', 'type': 'popular'},
            {'name': 'Temple of Heaven', 'url': 'https://en.wikipedia.org/wiki/Temple_of_Heaven', 'type': 'popular'}
        ],
        'bangkok': [
            {'name': 'Grand Palace', 'url': 'https://en.wikipedia.org/wiki/Grand_Palace', 'type': 'popular'},
            {'name': 'Wat Arun', 'url': 'https://en.wikipedia.org/wiki/Wat_Arun', 'type': 'popular'},
            {'name': 'Wat Phra Kaew', 'url': 'https://en.wikipedia.org/wiki/Wat_Phra_Kaew', 'type': 'popular'},
            {'name': 'Chatuchak Weekend Market', 'url': 'https://en.wikipedia.org/wiki/Chatuchak_Weekend_Market', 'type': 'popular'}
        ],
        'singapore': [
            {'name': 'Marina Bay Sands', 'url': 'https://en.wikipedia.org/wiki/Marina_Bay_Sands', 'type': 'popular'},
            {'name': 'Gardens by the Bay', 'url': 'https://en.wikipedia.org/wiki/Gardens_by_the_Bay', 'type': 'popular'},
            {'name': 'Sentosa Island', 'url': 'https://en.wikipedia.org/wiki/Sentosa', 'type': 'popular'},
            {'name': 'Singapore Zoo', 'url': 'https://en.wikipedia.org/wiki/Singapore_Zoo', 'type': 'popular'}
        ],
        'seoul': [
            {'name': 'Gyeongbokgung', 'url': 'https://en.wikipedia.org/wiki/Gyeongbokgung', 'type': 'popular'},
            {'name': 'Namsan Tower', 'url': 'https://en.wikipedia.org/wiki/Namsan_Tower', 'type': 'popular'},
            {'name': 'Myeongdong', 'url': 'https://en.wikipedia.org/wiki/Myeongdong', 'type': 'popular'},
            {'name': 'Bukchon Hanok Village', 'url': 'https://en.wikipedia.org/wiki/Bukchon_Hanok_Village', 'type': 'popular'}
        ],
        'moscow': [
            {'name': 'Red Square', 'url': 'https://en.wikipedia.org/wiki/Red_Square', 'type': 'popular'},
            {'name': 'Saint Basil\'s Cathedral', 'url': 'https://en.wikipedia.org/wiki/Saint_Basil%27s_Cathedral', 'type': 'popular'},
            {'name': 'Kremlin', 'url': 'https://en.wikipedia.org/wiki/Moscow_Kremlin', 'type': 'popular'},
            {'name': 'Bolshoi Theatre', 'url': 'https://en.wikipedia.org/wiki/Bolshoi_Theatre', 'type': 'popular'}
        ],
        'istanbul': [
            {'name': 'Hagia Sophia', 'url': 'https://en.wikipedia.org/wiki/Hagia_Sophia', 'type': 'popular'},
            {'name': 'Blue Mosque', 'url': 'https://en.wikipedia.org/wiki/Blue_Mosque', 'type': 'popular'},
            {'name': 'Topkapi Palace', 'url': 'https://en.wikipedia.org/wiki/Topkap%C4%B1_Palace', 'type': 'popular'},
            {'name': 'Grand Bazaar', 'url': 'https://en.wikipedia.org/wiki/Grand_Bazaar,_Istanbul', 'type': 'popular'}
        ],

        # Americas
        'new york': [
            {'name': 'Statue of Liberty', 'url': 'https://en.wikipedia.org/wiki/Statue_of_Liberty', 'type': 'popular'},
            {'name': 'Times Square', 'url': 'https://en.wikipedia.org/wiki/Times_Square', 'type': 'popular'},
            {'name': 'Central Park', 'url': 'https://en.wikipedia.org/wiki/Central_Park', 'type': 'popular'},
            {'name': 'Empire State Building', 'url': 'https://en.wikipedia.org/wiki/Empire_State_Building', 'type': 'popular'},
            {'name': 'Metropolitan Museum of Art', 'url': 'https://en.wikipedia.org/wiki/Metropolitan_Museum_of_Art', 'type': 'popular'},
            {'name': 'Brooklyn Bridge', 'url': 'https://en.wikipedia.org/wiki/Brooklyn_Bridge', 'type': 'popular'}
        ],
        'los angeles': [
            {'name': 'Hollywood Sign', 'url': 'https://en.wikipedia.org/wiki/Hollywood_Sign', 'type': 'popular'},
            {'name': 'Griffith Observatory', 'url': 'https://en.wikipedia.org/wiki/Griffith_Observatory', 'type': 'popular'},
            {'name': 'Santa Monica Pier', 'url': 'https://en.wikipedia.org/wiki/Santa_Monica_Pier', 'type': 'popular'},
            {'name': 'Walt Disney Concert Hall', 'url': 'https://en.wikipedia.org/wiki/Walt_Disney_Concert_Hall', 'type': 'popular'}
        ],
        'rio': [
            {'name': 'Christ the Redeemer', 'url': 'https://en.wikipedia.org/wiki/Christ_the_Redeemer_(statue)', 'type': 'popular'},
            {'name': 'Sugarloaf Mountain', 'url': 'https://en.wikipedia.org/wiki/Sugarloaf_Mountain', 'type': 'popular'},
            {'name': 'Copacabana Beach', 'url': 'https://en.wikipedia.org/wiki/Copacabana_(Rio_de_Janeiro)', 'type': 'popular'},
            {'name': 'Maracanã Stadium', 'url': 'https://en.wikipedia.org/wiki/Maracan%C3%A3_Stadium', 'type': 'popular'}
        ],
        'mexico city': [
            {'name': 'Teotihuacan', 'url': 'https://en.wikipedia.org/wiki/Teotihuacan', 'type': 'popular'},
            {'name': 'Chapultepec Castle', 'url': 'https://en.wikipedia.org/wiki/Chapultepec_Castle', 'type': 'popular'},
            {'name': 'National Palace', 'url': 'https://en.wikipedia.org/wiki/National_Palace_(Mexico)', 'type': 'popular'},
            {'name': 'Frida Kahlo Museum', 'url': 'https://en.wikipedia.org/wiki/Frida_Kahlo_Museum', 'type': 'popular'}
        ],

        # Middle East & Africa
        'dubai': [
            {'name': 'Burj Khalifa', 'url': 'https://en.wikipedia.org/wiki/Burj_Khalifa', 'type': 'popular'},
            {'name': 'Palm Jumeirah', 'url': 'https://en.wikipedia.org/wiki/Palm_Jumeirah', 'type': 'popular'},
            {'name': 'Dubai Mall', 'url': 'https://en.wikipedia.org/wiki/Dubai_Mall', 'type': 'popular'},
            {'name': 'Burj Al Arab', 'url': 'https://en.wikipedia.org/wiki/Burj_Al_Arab', 'type': 'popular'}
        ],
        'cairo': [
            {'name': 'Pyramids of Giza', 'url': 'https://en.wikipedia.org/wiki/Giza_pyramid_complex', 'type': 'popular'},
            {'name': 'Egyptian Museum', 'url': 'https://en.wikipedia.org/wiki/Egyptian_Museum', 'type': 'popular'},
            {'name': 'Khan el-Khalili', 'url': 'https://en.wikipedia.org/wiki/Khan_el-Khalili', 'type': 'popular'},
            {'name': 'Citadel of Cairo', 'url': 'https://en.wikipedia.org/wiki/Citadel_of_Cairo', 'type': 'popular'}
        ],
        'jerusalem': [
            {'name': 'Western Wall', 'url': 'https://en.wikipedia.org/wiki/Western_Wall', 'type': 'popular'},
            {'name': 'Church of the Holy Sepulchre', 'url': 'https://en.wikipedia.org/wiki/Church_of_the_Holy_Sepulchre', 'type': 'popular'},
            {'name': 'Dome of the Rock', 'url': 'https://en.wikipedia.org/wiki/Dome_of_the_Rock', 'type': 'popular'},
            {'name': 'Old City of Jerusalem', 'url': 'https://en.wikipedia.org/wiki/Old_City_(Jerusalem)', 'type': 'popular'}
        ],

        # Oceania
        'sydney': [
            {'name': 'Sydney Opera House', 'url': 'https://en.wikipedia.org/wiki/Sydney_Opera_House', 'type': 'popular'},
            {'name': 'Sydney Harbour Bridge', 'url': 'https://en.wikipedia.org/wiki/Sydney_Harbour_Bridge', 'type': 'popular'},
            {'name': 'Royal Botanic Gardens', 'url': 'https://en.wikipedia.org/wiki/Royal_Botanic_Gardens,_Sydney', 'type': 'popular'},
            {'name': 'Bondi Beach', 'url': 'https://en.wikipedia.org/wiki/Bondi_Beach', 'type': 'popular'}
        ]
    }

    return popular_spots.get(location_lower, [])

def detect_hotspots():
    """Detect tourist hotspots based on clustered locations"""
    global hotspots
    hotspots = []

    if len(tourist_locations) < 3:  # Need at least 3 tourists for a hotspot
        return hotspots

    # Convert locations to list for clustering
    locations = []
    for user_id, data in tourist_locations.items():
        # Only consider recent locations (within last 30 minutes)
        if datetime.now() - datetime.fromisoformat(data['timestamp']) < timedelta(minutes=30):
            locations.append({
                'user_id': user_id,
                'lat': data['lat'],
                'lng': data['lng'],
                'name': data['name']
            })

    if len(locations) < 3:
        return hotspots

    # Simple clustering algorithm - group tourists within 500m radius
    clusters = []
    processed = set()

    for i, loc1 in enumerate(locations):
        if loc1['user_id'] in processed:
            continue

        cluster = [loc1]
        processed.add(loc1['user_id'])

        for j, loc2 in enumerate(locations):
            if loc2['user_id'] in processed:
                continue

            distance = calculate_distance(loc1['lat'], loc1['lng'], loc2['lat'], loc2['lng'])
            if distance <= 0.5:  # 500 meters
                cluster.append(loc2)
                processed.add(loc2['user_id'])

        if len(cluster) >= 3:  # Minimum 3 tourists for a hotspot
            # Calculate cluster center
            avg_lat = sum(loc['lat'] for loc in cluster) / len(cluster)
            avg_lng = sum(loc['lng'] for loc in cluster) / len(cluster)

            hotspot = {
                'id': f"hotspot_{len(clusters) + 1}",
                'lat': avg_lat,
                'lng': avg_lng,
                'tourist_count': len(cluster),
                'tourists': [{'name': loc['name'], 'user_id': loc['user_id']} for loc in cluster],
                'created_at': datetime.now().isoformat(),
                'radius': 500  # meters
            }
            clusters.append(hotspot)

    hotspots = clusters
    return hotspots

def update_tourist_location(user_id, lat, lng, name="Anonymous Tourist"):
    """Update a tourist's location for hotspot detection"""
    tourist_locations[user_id] = {
        'lat': lat,
        'lng': lng,
        'timestamp': datetime.now().isoformat(),
        'name': name
    }

    # Detect new hotspots after location update
    detect_hotspots()

@app.route('/api/tourist-attractions')
def get_tourist_attractions():
    """Dedicated endpoint for getting tourist attractions"""
    location = request.args.get('location', '')
    if not location:
        return jsonify({'error': 'Location parameter required'}), 400

    attractions = get_wikipedia_attractions(location)
    if attractions:
        return jsonify({'attractions': attractions})
    else:
        return jsonify({'attractions': [], 'message': 'No tourist attractions found'})

@app.route('/api/ai-assistant', methods=['POST'])
def ai_safety_assistant():
    """AI-powered safety assistant with contextual responses"""
    data = request.get_json()
    user_message = data.get('message', '').lower()
    user_location = data.get('location', {})
    weather_data = data.get('weather', {})

    # AI Response Logic
    response = generate_ai_response(user_message, user_location, weather_data)

    return jsonify({
        'response': response,
        'timestamp': datetime.now().isoformat(),
        'context': {
            'location': user_location,
            'weather': weather_data
        }
    })

def generate_ai_response(message, location, weather):
    """Generate contextual AI responses based on user input and current conditions"""

    # Emergency keywords
    emergency_keywords = ['emergency', 'danger', 'help', 'stuck', 'lost', 'accident', 'medical']
    if any(keyword in message for keyword in emergency_keywords):
        return "🚨 EMERGENCY DETECTED! If you're in immediate danger, call emergency services immediately. Local emergency number: 112 (Europe) / 911 (US) / 100 (India). Stay calm and provide your location details."

    # Location-based safety tips
    if 'safe' in message or 'safety' in message:
        safety_tips = []
        if location:
            safety_tips.append(f"📍 For {location.get('name', 'your location')}:")
            safety_tips.append("• Stay aware of your surroundings")
            safety_tips.append("• Keep valuables secure")
            safety_tips.append("• Use official transportation")

        if weather:
            temp = weather.get('temperature', 20)
            if temp > 35:
                safety_tips.append("🔥 High temperature alert: Stay hydrated and avoid prolonged sun exposure")
            elif temp < 5:
                safety_tips.append("❄️ Cold weather: Dress warmly and be cautious of ice")

        return "\n".join(safety_tips) if safety_tips else "General safety tips: Stay aware, keep emergency contacts handy, and trust your instincts."

    # Weather-related queries
    if 'weather' in message or 'rain' in message or 'hot' in message or 'cold' in message:
        if weather:
            temp = weather.get('temperature', 'N/A')
            desc = weather.get('description', 'Unknown')
            return f"🌤️ Current weather: {temp}°C, {desc}. {'Dress appropriately for the weather!' if temp != 'N/A' else ''}"
        else:
            return "I don't have current weather data. Please check the weather section on the map."

    # Tourist attraction recommendations
    if 'attractions' in message or 'places' in message or 'see' in message:
        if location and location.get('name'):
            return f"🏛️ For tourist attractions in {location['name']}, check the location pins on the map! They show famous places with direct Wikipedia links."
        else:
            return "🏛️ Search for a location on the map to see tourist attractions with images and descriptions!"

    # Transportation queries
    if 'transport' in message or 'taxi' in message or 'uber' in message:
        return "🚗 Transportation tips: Use official taxi services or ride-sharing apps. Verify driver details and share your trip with someone. For public transport, check official schedules."

    # Health and medical queries
    if 'sick' in message or 'medical' in message or 'doctor' in message:
        return "🏥 Medical emergency: Call local emergency services. For non-emergency medical help, look for hospitals or clinics. Keep travel insurance details handy."

    # Lost or directions
    if 'lost' in message or 'direction' in message or 'find' in message:
        return "🗺️ If you're lost: Stay calm, use the map to locate yourself, and ask locals politely. Share your location with trusted contacts."

    # Default responses
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good evening']
    if any(greeting in message for greeting in greetings):
        return "Hello! 👋 I'm your AI Safety Assistant. I can help with safety tips, emergency contacts, weather advice, and travel recommendations. What would you like to know?"

    thanks = ['thank', 'thanks']
    if any(word in message for word in thanks):
        return "You're welcome! 😊 Stay safe and enjoy your travels. Remember, safety first!"

    # Generic helpful response
    return "🤖 I'm here to help with your safety and travel needs! Ask me about:\n• Safety tips for your location\n• Weather conditions\n• Tourist attractions\n• Emergency contacts\n• Travel advice\n\nWhat specific information do you need?"

@app.route('/api/safety-news')
def get_safety_news():
    """Get real-time safety news and alerts for a location"""
    location = request.args.get('location', '')
    if not location:
        return jsonify({'error': 'Location parameter required'}), 400

    try:
        # Use NewsAPI or similar service (mock implementation for demo)
        # In production, you'd use a real news API like NewsAPI.org
        news_alerts = generate_mock_safety_news(location)
        return jsonify({'news': news_alerts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_mock_safety_news(location):
    """Generate mock safety news for demonstration"""
    location_name = location.split(',')[0].lower()

    # Mock safety news based on location
    mock_news = {
        'paris': [
            {
                'title': 'Paris Metro Safety Improvements',
                'description': 'New security measures implemented in major metro stations',
                'severity': 'low',
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': 'Tourist Safety Campaign Launched',
                'description': 'Paris tourism board launches safety awareness campaign for visitors',
                'severity': 'info',
                'timestamp': datetime.now().isoformat()
            }
        ],
        'london': [
            {
                'title': 'London Underground Security Update',
                'description': 'Enhanced security protocols in place following recent incidents',
                'severity': 'medium',
                'timestamp': datetime.now().isoformat()
            }
        ],
        'tokyo': [
            {
                'title': 'Tokyo Earthquake Preparedness',
                'description': 'Emergency drills conducted in tourist areas',
                'severity': 'info',
                'timestamp': datetime.now().isoformat()
            }
        ],
        'new york': [
            {
                'title': 'NYC Tourist Safety Initiatives',
                'description': 'New safety measures for Times Square and Central Park',
                'severity': 'low',
                'timestamp': datetime.now().isoformat()
            }
        ]
    }

    # Default news for unknown locations
    default_news = [
        {
            'title': f'General Safety Advisory for {location_name.title()}',
            'description': 'Stay aware of surroundings and follow local safety guidelines',
            'severity': 'info',
            'timestamp': datetime.now().isoformat()
        }
    ]

    return mock_news.get(location_name, default_news)

@app.route('/api/tourist-community')
def get_tourist_community():
    """Get nearby tourists for community features"""
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)

    if not lat or not lng:
        return jsonify({'error': 'Latitude and longitude required'}), 400

    # Mock nearby tourists (in production, this would come from a database)
    nearby_tourists = [
        {
            'id': 'tourist_001',
            'name': 'Sarah M.',
            'distance': '0.5 km',
            'status': 'Exploring the city',
            'last_seen': datetime.now().isoformat()
        },
        {
            'id': 'tourist_002',
            'name': 'John D.',
            'distance': '1.2 km',
            'status': 'At local restaurant',
            'last_seen': datetime.now().isoformat()
        },
        {
            'id': 'tourist_003',
            'name': 'Maria L.',
            'distance': '2.1 km',
            'status': 'Visiting museum',
            'last_seen': datetime.now().isoformat()
        }
    ]

    return jsonify({'tourists': nearby_tourists})

@app.route('/api/search')
def search_location():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Search query required'}), 400

    try:
        params = {
            'format': 'json',
            'q': query,
            'limit': 1
        }

        response = requests.get(NOMINATIM_API_URL, params=params, headers={
            'User-Agent': 'Tourist-Safety-Portal/1.0'
        })
        data = response.json()

        if data:
            result = data[0]
            location_data = {
                'lat': float(result['lat']),
                'lng': float(result['lon']),
                'display_name': result['display_name']
            }

            # Get Wikipedia page information
            wiki_data = get_wikipedia_info(query)
            if wiki_data:
                location_data['wikipedia'] = wiki_data

            return jsonify(location_data)
        else:
            return jsonify({'error': 'Location not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ratings', methods=['GET', 'POST'])
def handle_ratings():
    if request.method == 'POST':
        data = request.get_json()
        rating = {
            'lat': data['lat'],
            'lng': data['lng'],
            'rating': data['rating'],
            'timestamp': datetime.now().isoformat()
        }
        ratings.append(rating)
        return jsonify({'success': True})

    # Check if location-specific ratings are requested
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', default=5, type=float)  # 5km default

    if lat is not None and lng is not None:
        # Return ratings within radius of specified location
        nearby_ratings = []
        for rating in ratings:
            distance = calculate_distance(lat, lng, rating['lat'], rating['lng'])
            if distance <= radius:
                nearby_ratings.append(rating['rating'])

        if nearby_ratings:
            avg_rating = sum(nearby_ratings) / len(nearby_ratings)
            return jsonify({
                'average_rating': round(avg_rating, 1),
                'total_ratings': len(nearby_ratings),
                'location': {'lat': lat, 'lng': lng},
                'radius_km': radius
            })
        else:
            return jsonify({
                'average_rating': None,
                'total_ratings': 0,
                'location': {'lat': lat, 'lng': lng},
                'radius_km': radius,
                'message': 'No ratings found in this area'
            })

    # Return all ratings for map display (grouped by proximity)
    return jsonify(get_grouped_ratings())

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points in kilometers"""
    from math import radians, sin, cos, sqrt, atan2

    R = 6371  # Earth's radius in kilometers

    lat1_rad = radians(lat1)
    lng1_rad = radians(lng1)
    lat2_rad = radians(lat2)
    lng2_rad = radians(lng2)

    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad

    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c

def get_grouped_ratings():
    """Group ratings by proximity (5km radius) and calculate averages"""
    if not ratings:
        return []

    grouped_ratings = []

    for rating in ratings:
        # Check if this rating is already grouped
        found_group = False
        for group in grouped_ratings:
            distance = calculate_distance(
                rating['lat'], rating['lng'],
                group['lat'], group['lng']
            )
            if distance <= 5:  # 5km radius
                # Add to existing group
                group['ratings'].append(rating['rating'])
                group['count'] = len(group['ratings'])
                group['rating'] = round(sum(group['ratings']) / len(group['ratings']), 1)
                found_group = True
                break

        if not found_group:
            # Create new group
            grouped_ratings.append({
                'lat': rating['lat'],
                'lng': rating['lng'],
                'rating': rating['rating'],
                'count': 1,
                'ratings': [rating['rating']]
            })

    return grouped_ratings


@app.route('/api/alerts')
def get_alerts():
    return jsonify(alerts[-10:])  # Last 10 alerts

@app.route('/api/behavior', methods=['POST'])
def update_behavior():
    data = request.get_json()
    user_id = data.get('user_id', 'anonymous')
    lat = data['lat']
    lng = data['lng']
    name = data.get('name', 'Anonymous Tourist')

    if user_id not in behavior_history:
        behavior_history[user_id] = []

    behavior_history[user_id].append({
        'lat': lat,
        'lng': lng,
        'timestamp': datetime.now().isoformat()
    })

    # Keep only last 50 positions
    if len(behavior_history[user_id]) > 50:
        behavior_history[user_id] = behavior_history[user_id][-50:]

    # Update tourist location for hotspot detection
    update_tourist_location(user_id, lat, lng, name)

    return jsonify({'success': True})

def get_location_language(location_name):
    """Get local language information for a location"""
    location_lower = location_name.lower().strip()

    # Normalize common location names
    location_mappings = {
        'japan': 'tokyo',  # Map country to major city
        'japanese': 'tokyo',
        'india': 'delhi',
        'indian': 'delhi',
        'france': 'paris',
        'french': 'paris',
        'china': 'beijing',
        'chinese': 'beijing',
        'russia': 'moscow',
        'russian': 'moscow',
        'turkey': 'istanbul',
        'turkish': 'istanbul',
        'egypt': 'cairo',
        'egyptian': 'cairo',
        'brazil': 'rio',
        'brazilian': 'rio',
        'uae': 'dubai',
        'united arab emirates': 'dubai',
        'arab': 'dubai',
        'australia': 'sydney',
        'australian': 'sydney',
        'uk': 'london',
        'united kingdom': 'london',
        'british': 'london',
        'usa': 'new york',
        'united states': 'new york',
        'america': 'new york',
        'american': 'new york',
        'italy': 'rome',
        'italian': 'rome',
        'spain': 'barcelona',
        'spanish': 'barcelona',
        'netherlands': 'amsterdam',
        'dutch': 'amsterdam',
        'germany': 'berlin',
        'german': 'berlin',
        'czech republic': 'prague',
        'czech': 'prague',
        'austria': 'vienna',
        'austrian': 'vienna',
        'thailand': 'bangkok',
        'thai': 'bangkok',
        'south korea': 'seoul',
        'korean': 'seoul',
        'hong kong': 'hong kong',
        'china': 'beijing',
        'malaysia': 'kuala lumpur',
        'malay': 'kuala lumpur',
        'mexico': 'mexico city',
        'mexican': 'mexico city',
        'canada': 'toronto',
        'canadian': 'toronto',
        'brazil': 'sao paulo',
        'brazilian': 'sao paulo',
        'argentina': 'buenos aires',
        'argentinian': 'buenos aires',
        'israel': 'jerusalem',
        'hebrew': 'jerusalem',
        'saudi arabia': 'riyadh',
        'saudi': 'riyadh',
        'south africa': 'cape town',
        'african': 'cape town',
        'kenya': 'nairobi',
        'kenyan': 'nairobi',
        'new zealand': 'auckland',
        'zealand': 'auckland'
    }

    # Apply mapping if exists
    if location_lower in location_mappings:
        location_lower = location_mappings[location_lower]

    # Direct match
    if location_lower in LOCAL_LANGUAGES:
        return LOCAL_LANGUAGES[location_lower]

    # Partial match for city names
    for key, data in LOCAL_LANGUAGES.items():
        if key in location_lower or location_lower in key:
            return data

    # Try to match by language keywords
    language_keywords = {
        'hindi': 'delhi',
        'marathi': 'mumbai',
        'bengali': 'kolkata',
        'tamil': 'chennai',
        'telugu': 'hyderabad',
        'kannada': 'bangalore',
        'gujarati': 'ahmedabad',
        'rajasthani': 'jaipur',
        'french': 'paris',
        'english': 'london',
        'japanese': 'tokyo',
        'mandarin': 'beijing',
        'chinese': 'beijing',
        'russian': 'moscow',
        'arabic': 'dubai',
        'turkish': 'istanbul',
        'portuguese': 'rio'
    }

    for keyword, city in language_keywords.items():
        if keyword in location_lower:
            return LOCAL_LANGUAGES[city]

    # Default to English for unknown locations
    return {
        'language': 'English',
        'code': 'en',
        'script': 'Latin',
        'greeting': 'Hello',
        'thank_you': 'Thank you'
    }

def get_tourist_phrases(language_code):
    """Get tourist phrases for a language"""
    # Extract primary language code
    primary_code = language_code.split('/')[0] if '/' in language_code else language_code

    if primary_code in TOURIST_PHRASES:
        return TOURIST_PHRASES[primary_code]

    # Default English phrases
    return {
        'where_is': 'Where is',
        'how_much': 'How much',
        'water': 'Water',
        'food': 'Food',
        'help': 'Help',
        'bathroom': 'Bathroom',
        'taxi': 'Taxi',
        'hotel': 'Hotel'
    }

@app.route('/api/language/<location>')
def get_location_language_info(location):
    """Get language information for a location"""
    language_info = get_location_language(location)
    phrases = get_tourist_phrases(language_info['code'])

    return jsonify({
        'location': location,
        'language': language_info,
        'phrases': phrases
    })

@app.route('/api/language/phrases/<language_code>')
def get_language_phrases(language_code):
    """Get tourist phrases for a specific language"""
    phrases = get_tourist_phrases(language_code)
    return jsonify({'phrases': phrases})

@app.route('/api/dashboard')
def get_dashboard_data():
    active_tourists = len([u for u in users.values() if u.get('verified', False)])
    recent_alerts = alerts[-5:]

    # Calculate safety heatmap data
    if ratings:
        avg_rating = sum(r['rating'] for r in ratings) / len(ratings)
        low_safety = len([r for r in ratings if r['rating'] < 3])
        high_safety = len([r for r in ratings if r['rating'] >= 4])
    else:
        avg_rating = 0
        low_safety = 0
        high_safety = 0

    dashboard_data = {
        'active_tourists': active_tourists,
        'recent_alerts': recent_alerts,
        'safety_heatmap': {
            'average_rating': round(avg_rating, 1),
            'low_safety_zones': low_safety,
            'high_safety_zones': high_safety,
            'total_rated': len(ratings)
        },
        'behavior_analysis': analyze_behavior_patterns()
    }

    return jsonify(dashboard_data)

def analyze_behavior_patterns():
    """Analyze behavior patterns for dashboard"""
    if not behavior_history:
        return {'status': 'No data available'}

    total_movements = sum(len(history) for history in behavior_history.values())
    avg_movements = total_movements / len(behavior_history) if behavior_history else 0

    return {
        'total_users': len(behavior_history),
        'average_movements': round(avg_movements, 1),
        'status': 'Active monitoring'
    }

# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data['email']

    if email in users:
        return jsonify({'error': 'User already exists'}), 400

    user_id = str(len(users) + 1)
    users[email] = {
        'id': user_id,
        'name': data['name'],
        'email': email,
        'password': generate_password_hash(data['password']),
        'verified': False,
        'created_at': datetime.now().isoformat()
    }

    # Generate verification code
    code = str(random.randint(100000, 999999))
    verification_codes[email] = code

    return jsonify({
        'message': f'Verification code sent to {email}: {code}',
        'user_id': user_id
    })

@app.route('/api/auth/verify', methods=['POST'])
def verify_email():
    data = request.get_json()
    email = data['email']
    code = data['code']

    if email in verification_codes and verification_codes[email] == code:
        if email in users:
            users[email]['verified'] = True
            del verification_codes[email]
            return jsonify({'message': 'Email verified successfully'})
        else:
            return jsonify({'error': 'User not found'}), 404
    else:
        return jsonify({'error': 'Invalid verification code'}), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    if email in users and check_password_hash(users[email]['password'], password):
        if users[email]['verified']:
            session['user_id'] = users[email]['id']
            session['user_email'] = email
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': users[email]['id'],
                    'name': users[email]['name'],
                    'email': email
                }
            })
        else:
            return jsonify({'error': 'Please verify your email first'}), 400
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/logout')
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/auth/status')
def auth_status():
    if 'user_id' in session:
        email = session['user_email']
        user = users.get(email)
        if user:
            return jsonify({
                'logged_in': True,
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email']
                }
            })
    return jsonify({'logged_in': False})

# Blockchain simulation
def generate_blockchain_hash(data):
    """Simple hash simulation"""
    data_str = json.dumps(data, sort_keys=True)
    return hashlib.md5(data_str.encode()).hexdigest()

@app.route('/api/blockchain/verify', methods=['POST'])
def verify_blockchain_id():
    data = request.get_json()
    user_email = data.get('email')

    if user_email not in users:
        return jsonify({'error': 'User not found'}), 404

    user = users[user_email]
    user_data = {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'timestamp': user['created_at']
    }

    current_hash = generate_blockchain_hash(user_data)
    stored_hash = blockchain_hashes.get(user['id'])

    if not stored_hash:
        # First verification - store hash
        blockchain_hashes[user['id']] = current_hash
        return jsonify({
            'verified': True,
            'hash': current_hash,
            'message': 'ID verified and stored on blockchain'
        })
    else:
        verified = stored_hash == current_hash
        return jsonify({
            'verified': verified,
            'hash': current_hash,
            'message': 'Blockchain verification successful' if verified else 'Blockchain verification failed - data tampering detected'
        })

@app.route('/api/sos', methods=['POST'])
def sos_alert():
    data = request.get_json()
    alert = {
        'type': 'sos',
        'message': 'SOS Emergency triggered',
        'location': data.get('location', 'Unknown'),
        'timestamp': datetime.now().isoformat()
    }
    alerts.append(alert)
    return jsonify({'success': True, 'message': 'SOS alert sent'})

@app.route('/api/hotspots')
def get_hotspots():
    """Get all active tourist hotspots"""
    return jsonify({'hotspots': hotspots})

@app.route('/api/hotspots/<hotspot_id>')
def get_hotspot_details(hotspot_id):
    """Get details of a specific hotspot"""
    hotspot = next((h for h in hotspots if h['id'] == hotspot_id), None)
    if hotspot:
        return jsonify(hotspot)
    return jsonify({'error': 'Hotspot not found'}), 404

@app.route('/api/hotspots/join/<hotspot_id>', methods=['POST'])
def join_hotspot(hotspot_id):
    """Join a tourist hotspot"""
    data = request.get_json()
    user_id = data.get('user_id', 'anonymous')
    user_name = data.get('name', 'Anonymous Tourist')

    hotspot = next((h for h in hotspots if h['id'] == hotspot_id), None)
    if hotspot:
        # Check if user is already in the hotspot
        if not any(t['user_id'] == user_id for t in hotspot['tourists']):
            hotspot['tourists'].append({'name': user_name, 'user_id': user_id})
            hotspot['tourist_count'] = len(hotspot['tourists'])
            return jsonify({'success': True, 'message': f'Joined hotspot with {hotspot["tourist_count"]} tourists!'})
        else:
            return jsonify({'success': False, 'message': 'Already joined this hotspot'})
    return jsonify({'error': 'Hotspot not found'}), 404

def check_weather_alerts(current_weather):
    alerts = []
    weather_code = current_weather['weather_code']
    wind_speed = current_weather['wind_speed_10m']
    temp = current_weather['temperature_2m']
    precipitation = current_weather['precipitation']

    if weather_code >= 95 and weather_code <= 99:
        alerts.append('⚡ THUNDERSTORM WARNING: Seek shelter immediately!')

    if ((weather_code >= 61 and weather_code <= 67) or
        (weather_code >= 80 and weather_code <= 82)) and wind_speed > 20:
        alerts.append('🌧️ HEAVY RAIN ALERT: Roads may be slippery, drive cautiously!')

    if wind_speed > 30:
        alerts.append('💨 HIGH WIND WARNING: Strong winds detected, secure loose objects!')

    if temp > 40:
        alerts.append('🔥 HEAT WARNING: Extreme heat conditions, stay hydrated!')

    if temp < 0:
        alerts.append('❄️ FREEZE WARNING: Freezing temperatures, dress warmly!')

    if ((weather_code >= 71 and weather_code <= 77) or
        (weather_code >= 85 and weather_code <= 86)):
        alerts.append('❄️ SNOW ALERT: Snow conditions may affect travel!')

    if weather_code in [45, 48]:
        alerts.append('🌫️ FOG ALERT: Reduced visibility, drive carefully!')

    if precipitation > 10:
        alerts.append('🌧️ HEAVY PRECIPITATION: Flooding risk, avoid low-lying areas!')

    return alerts

def log_alert(alert_type, message, data=None):
    alert = {
        'type': alert_type,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    alerts.append(alert)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)