// Smart Tourist Safety Portal JavaScript

// Initialize map
let map;
let userMarker;
let ratingMarkers = [];

// Red marker icon for user location
const redIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// Live tracking variables
let watchId = null;
let isTracking = false;
let lastNotificationTime = 0;
const NOTIFICATION_COOLDOWN = 30000; // 30 seconds

// AI/ML and Advanced Features
let behaviorHistory = [];
let alertHistory = [];
let blockchainHashes = new Map();

// Initialize the map
function initMap() {
    map = L.map('map').setView([20.5937, 78.9629], 5); // Center on India

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Add click event for rating
    map.on('click', onMapClick);
}

// Get user's current location
function getCurrentLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                // Update map view
                map.setView([lat, lng], 15);

                // Add or update user marker
                if (userMarker) {
                    userMarker.setLatLng([lat, lng]);
                } else {
                    userMarker = L.marker([lat, lng], {icon: redIcon}).addTo(map)
                        .bindPopup('Your current location')
                        .openPopup();
                }

                // Update location info
                document.getElementById('current-location').textContent =
                    `Latitude: ${lat.toFixed(6)}, Longitude: ${lng.toFixed(6)}`;

                // Auto-fetch weather for current location
                getWeatherForLocation(lat, lng);
            },
            (error) => {
                alert('Error getting location: ' + error.message);
            }
        );
    } else {
        alert('Geolocation is not supported by this browser.');
    }
}

// Handle map click for rating
async function onMapClick(e) {
    const rating = prompt('Rate the safety of this location (1-5 stars):');
    if (rating && rating >= 1 && rating <= 5) {
        // Reverse geocode to get location name
        const locationName = await getLocationName(e.latlng.lat, e.latlng.lng);

        // Get Wikipedia attractions for this location
        let wikiData = null;
        if (locationName) {
            try {
                const response = await fetch(`/api/search?q=${encodeURIComponent(locationName)}`);
                const data = await response.json();
                if (data.wikipedia) {
                    wikiData = data.wikipedia;
                }
            } catch (error) {
                console.error('Wikipedia fetch error:', error);
            }
        }

        // Create popup content
        let popupContent = `<div style="max-width: 300px;">Safety Rating: ${rating} stars`;
        if (locationName) {
            popupContent += `<br><b>${locationName}</b>`;
        }

        if (wikiData) {
            popupContent += '<br><br><div style="background: rgba(0,123,255,0.1); padding: 12px; border-radius: 6px; margin-top: 8px;">';
            if (wikiData.thumbnail) {
                popupContent += `<img src="${wikiData.thumbnail}" alt="${wikiData.title}" style="width: 80px; height: 60px; object-fit: cover; float: left; margin-right: 10px; border-radius: 4px;">`;
            }
            popupContent += `<strong>📖 Wikipedia:</strong><br>`;
            popupContent += `<a href="${wikiData.url}" target="_blank" style="color: #007bff; text-decoration: none; font-weight: bold; font-size: 14px;">${wikiData.title}</a><br>`;
            if (wikiData.description) {
                popupContent += `<small style="color: #666; font-size: 12px; line-height: 1.3;">${wikiData.description}</small><br>`;
            }
            popupContent += `<small style="color: #888; font-size: 11px;">Click to read more on Wikipedia</small>`;
            popupContent += '</div>';
        }
        popupContent += '</div>';

        const marker = L.marker([e.latlng.lat, e.latlng.lng]).addTo(map)
            .bindPopup(popupContent);

        ratingMarkers.push({
            lat: e.latlng.lat,
            lng: e.latlng.lng,
            rating: parseInt(rating),
            marker: marker
        });

        updateRatingsList();
    }
}

// Update the ratings list in the UI
function updateRatingsList() {
    const ratingsList = document.getElementById('ratings-list');
    ratingsList.innerHTML = '';

    ratingMarkers.forEach((rating, index) => {
        const ratingItem = document.createElement('div');
        ratingItem.className = 'rating-item';

        const locationText = document.createElement('span');
        locationText.textContent = `Location ${index + 1}: (${rating.lat.toFixed(4)}, ${rating.lng.toFixed(4)})`;

        const stars = document.createElement('span');
        stars.className = 'rating-stars';
        stars.textContent = '★'.repeat(rating.rating) + '☆'.repeat(5 - rating.rating);

        ratingItem.appendChild(locationText);
        ratingItem.appendChild(stars);
        ratingsList.appendChild(ratingItem);
    });
}

// Reverse geocode coordinates to get location name
async function getLocationName(lat, lng) {
    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=10`);
        const data = await response.json();
        if (data && data.display_name) {
            return data.display_name.split(',')[0]; // Return just the city/place name
        }
    } catch (error) {
        console.error('Reverse geocoding error:', error);
    }
    return null;
}

// Search location using our backend API (includes Wikipedia data)
async function searchLocation(query) {
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        const lat = data.lat;
        const lng = data.lng;

        // Center map on searched location
        map.setView([lat, lng], 15);

        // Create popup content with Wikipedia information
        let popupContent = `<div style="max-width: 300px;"><b>${data.display_name}</b>`;

        if (data.wikipedia) {
            const wiki = data.wikipedia;
            popupContent += '<br><br><div style="background: rgba(0,123,255,0.1); padding: 12px; border-radius: 6px; margin-top: 8px;">';
            if (wiki.thumbnail) {
                popupContent += `<img src="${wiki.thumbnail}" alt="${wiki.title}" style="width: 80px; height: 60px; object-fit: cover; float: left; margin-right: 10px; border-radius: 4px;">`;
            }
            popupContent += `<strong>📖 Wikipedia:</strong><br>`;
            popupContent += `<a href="${wiki.url}" target="_blank" style="color: #007bff; text-decoration: none; font-weight: bold; font-size: 14px;">${wiki.title}</a><br>`;
            if (wiki.description) {
                popupContent += `<small style="color: #666; font-size: 12px; line-height: 1.3;">${wiki.description}</small><br>`;
            }
            popupContent += `<small style="color: #888; font-size: 11px;">Click to read more on Wikipedia</small>`;
            popupContent += '</div>';
        }
        popupContent += '</div>';

        // Add marker for searched location
        L.marker([lat, lng]).addTo(map)
            .bindPopup(popupContent)
            .openPopup();

        // Update current location display
        document.getElementById('current-location').textContent =
            `Searched: ${data.display_name.split(',')[0]}`;

        // Store current location for AI assistant
        currentLocation = {
            lat: lat,
            lng: lng,
            name: data.display_name.split(',')[0]
        };

        // Auto-fetch weather for searched location
        getWeatherForLocation(lat, lng);

        // Load safety news for the location
        loadSafetyNews(data.display_name);
    } catch (error) {
        console.error('Search error:', error);
        alert('Error searching for location. Please try again.');
    }
}

// Check weather for current location or map center
function checkWeather() {
    // Try to get weather for user's current location first
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                getWeatherForLocation(lat, lng);
            },
            (error) => {
                // Fallback to map center if geolocation fails
                console.log('Geolocation failed, using map center:', error);
                const center = map.getCenter();
                getWeatherForLocation(center.lat, center.lng);
            }
        );
    } else {
        // Fallback to map center
        const center = map.getCenter();
        getWeatherForLocation(center.lat, center.lng);
    }
}

// SOS button functionality
function triggerSOS() {
    const confirmed = confirm('Are you sure you want to trigger SOS? This will alert emergency services.');
    if (confirmed) {
        // In a real implementation, this would send alerts to police/emergency contacts
        alert('SOS ALERT TRIGGERED!\n\nEmergency services have been notified.\nYour location has been shared.');

        // Get current location for SOS
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    console.log('SOS Location:', lat, lng);
                    // Here you would send this to emergency services
                }
            );
        }
    }
}

// Live location tracking functions
function startLiveTracking() {
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by this browser.');
        return;
    }

    if (isTracking) {
        stopLiveTracking();
        return;
    }

    isTracking = true;
    updateTrackingUI();

    watchId = navigator.geolocation.watchPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;

            // Update user marker
            if (userMarker) {
                userMarker.setLatLng([lat, lng]);
            } else {
                userMarker = L.marker([lat, lng], {icon: redIcon}).addTo(map)
                    .bindPopup('Your current location')
                    .openPopup();
            }

            // Check for safety zones
            checkSafetyZone(lat, lng);

            // AI behavior analysis
            analyzeBehavior(lat, lng);

            // Update location info
            document.getElementById('current-location').textContent =
                `Latitude: ${lat.toFixed(6)}, Longitude: ${lng.toFixed(6)}`;

            // Store current location for AI assistant
            currentLocation = {
                lat: lat,
                lng: lng,
                name: `Location (${lat.toFixed(4)}, ${lng.toFixed(4)})`
            };

            // Auto-fetch weather for current location
            getWeatherForLocation(lat, lng);

            // Load nearby tourist community
            loadTouristCommunity(lat, lng);
        },
        (error) => {
            console.error('Tracking error:', error);
            alert('Error tracking location: ' + error.message);
            stopLiveTracking();
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 30000
        }
    );
}

function stopLiveTracking() {
    if (watchId) {
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
    }
    isTracking = false;
    updateTrackingUI();
}

function updateTrackingUI() {
    const button = document.getElementById('live-tracking-btn');
    const status = document.getElementById('tracking-status');

    if (isTracking) {
        button.textContent = 'Stop Live Tracking';
        button.classList.add('active');
        status.textContent = 'Tracking: ON';
        status.style.color = '#27ae60';
    } else {
        button.textContent = 'Start Live Tracking';
        button.classList.remove('active');
        status.textContent = 'Tracking: OFF';
        status.style.color = '#2c3e50';
    }
}

function checkSafetyZone(lat, lng) {
    const now = Date.now();
    if (now - lastNotificationTime < NOTIFICATION_COOLDOWN) {
        return; // Too soon for another notification
    }

    // Check proximity to low-safety zones (rating < 2)
    const lowSafetyZones = ratingMarkers.filter(marker => marker.rating < 2);

    for (const zone of lowSafetyZones) {
        const distance = getDistance(lat, lng, zone.lat, zone.lng);

        // If within 500 meters of a low-safety zone
        if (distance < 500) {
            sendSafetyNotification(zone);
            lastNotificationTime = now;
            break; // Only send one notification at a time
        }
    }
}

function getDistance(lat1, lng1, lat2, lng2) {
    const R = 6371e3; // Earth's radius in meters
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lng2 - lng1) * Math.PI / 180;

    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return R * c; // Distance in meters
}

function sendSafetyNotification(zone) {
    const message = `⚠️ SAFETY ALERT ⚠️\n\nYou have entered a low-safety zone!\nRating: ${zone.rating} stars\nLocation: (${zone.lat.toFixed(4)}, ${zone.lng.toFixed(4)})\n\nPlease be cautious and consider changing your route.`;

    // Browser notification
    if (Notification.permission === 'granted') {
        new Notification('Tourist Safety Alert', {
            body: message,
            icon: '⚠️'
        });
    } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                new Notification('Tourist Safety Alert', {
                    body: message,
                    icon: '⚠️'
                });
            }
        });
    }

    // Alert fallback
    alert(message);

    // Log alert for dashboard
    logAlert('safety_zone', message, { lat, lng });
}

// AI/ML Behavior Tracking Simulation
function analyzeBehavior(lat, lng) {
    const now = Date.now();
    const currentPosition = { lat, lng, timestamp: now };

    behaviorHistory.push(currentPosition);

    // Keep only last 50 positions
    if (behaviorHistory.length > 50) {
        behaviorHistory.shift();
    }

    // Analyze patterns
    if (behaviorHistory.length >= 5) {
        const patterns = detectPatterns();
        const predictions = generatePredictions(patterns);

        if (predictions.risk > 0.7) {
            sendPredictiveAlert(predictions);
        }
    }
}

function detectPatterns() {
    if (behaviorHistory.length < 5) return {};

    const recent = behaviorHistory.slice(-10);
    let totalDistance = 0;
    let directionChanges = 0;
    let speedVariations = 0;

    for (let i = 1; i < recent.length; i++) {
        const dist = getDistance(recent[i-1].lat, recent[i-1].lng, recent[i].lat, recent[i].lng);
        totalDistance += dist;

        if (i > 1) {
            // Simple direction change detection
            const prevDist = getDistance(recent[i-2].lat, recent[i-2].lng, recent[i-1].lat, recent[i-1].lng);
            if (Math.abs(dist - prevDist) > 50) { // Significant speed change
                speedVariations++;
            }
        }
    }

    return {
        avgSpeed: totalDistance / (recent.length - 1),
        speedVariations,
        totalDistance,
        erraticMovement: speedVariations > 3
    };
}

function generatePredictions(patterns) {
    let risk = 0;

    if (patterns.erraticMovement) risk += 0.3;
    if (patterns.avgSpeed > 100) risk += 0.2; // Moving too fast
    if (patterns.avgSpeed < 5) risk += 0.1; // Moving too slow (possible distress)

    // Time-based risk
    const hour = new Date().getHours();
    if (hour >= 22 || hour <= 5) risk += 0.2; // Night time risk

    return {
        risk: Math.min(risk, 1),
        patterns,
        recommendation: risk > 0.7 ? 'High risk detected - Consider safety measures' : 'Normal activity'
    };
}

function sendPredictiveAlert(predictions) {
    const message = `🤖 AI ALERT: ${predictions.recommendation}\n\nRisk Level: ${(predictions.risk * 100).toFixed(1)}%\nPatterns: ${predictions.patterns.erraticMovement ? 'Erratic movement' : 'Normal'}`;

    if (Notification.permission === 'granted') {
        new Notification('AI Safety Alert', {
            body: message,
            icon: '🤖'
        });
    }

    alert(message);
    logAlert('ai_prediction', message, predictions);
}

// Weather API Integration using Open-Meteo (free, no API key required)
let currentWeatherData = null;

// Get weather for coordinates using Open-Meteo API
async function getWeatherForLocation(lat, lng) {
    try {
        const response = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&timezone=auto`);
        const data = await response.json();

        if (data.current) {
            currentWeatherData = data;
            displayWeather(data);
            checkWeatherAlerts(data);
            return data;
        } else {
            throw new Error('Weather data not available');
        }
    } catch (error) {
        console.error('Weather API error:', error);
        document.getElementById('weather-display').innerHTML = `<span style="color: #f5576c;">Weather data unavailable: ${error.message}</span>`;
        return null;
    }
}

// Display weather information
function displayWeather(data) {
    const temp = Math.round(data.current.temperature_2m);
    const feelsLike = Math.round(data.current.apparent_temperature);
    const humidity = data.current.relative_humidity_2m;
    const windSpeed = data.current.wind_speed_10m;
    const precipitation = data.current.precipitation;
    const weatherCode = data.current.weather_code;

    // Convert Open-Meteo weather code to description and icon
    const weatherInfo = getWeatherDescription(weatherCode);
    const description = weatherInfo.description;
    const iconUrl = weatherInfo.icon;

    const weatherHtml = `
        <div class="weather-content">
            <div class="weather-main">
                <img src="${iconUrl}" alt="${description}" class="weather-icon">
                <div class="weather-temp">
                    <span class="temp">${temp}°C</span>
                    <span class="feels-like">Feels like ${feelsLike}°C</span>
                </div>
            </div>
            <div class="weather-details">
                <p><strong>${description}</strong></p>
                <p>Humidity: ${humidity}%</p>
                <p>Wind: ${windSpeed} km/h</p>
                <p>Precipitation: ${precipitation} mm</p>
                <p>Coordinates: ${data.latitude.toFixed(4)}, ${data.longitude.toFixed(4)}</p>
            </div>
        </div>
    `;

    document.getElementById('weather-display').innerHTML = weatherHtml;

    // Store weather data for AI assistant
    currentWeather = {
        temperature: temp,
        description: description,
        humidity: humidity,
        windSpeed: windSpeed,
        precipitation: precipitation
    };
}

// Convert Open-Meteo weather code to description and icon
function getWeatherDescription(code) {
    const weatherCodes = {
        0: { description: "Clear sky", icon: "☀️" },
        1: { description: "Mainly clear", icon: "🌤️" },
        2: { description: "Partly cloudy", icon: "⛅" },
        3: { description: "Overcast", icon: "☁️" },
        45: { description: "Fog", icon: "🌫️" },
        48: { description: "Depositing rime fog", icon: "🌫️" },
        51: { description: "Light drizzle", icon: "🌦️" },
        53: { description: "Moderate drizzle", icon: "🌦️" },
        55: { description: "Dense drizzle", icon: "🌦️" },
        56: { description: "Light freezing drizzle", icon: "🌨️" },
        57: { description: "Dense freezing drizzle", icon: "🌨️" },
        61: { description: "Slight rain", icon: "🌧️" },
        63: { description: "Moderate rain", icon: "🌧️" },
        65: { description: "Heavy rain", icon: "🌧️" },
        66: { description: "Light freezing rain", icon: "🌨️" },
        67: { description: "Heavy freezing rain", icon: "🌨️" },
        71: { description: "Slight snow fall", icon: "❄️" },
        73: { description: "Moderate snow fall", icon: "❄️" },
        75: { description: "Heavy snow fall", icon: "❄️" },
        77: { description: "Snow grains", icon: "❄️" },
        80: { description: "Slight rain showers", icon: "🌦️" },
        81: { description: "Moderate rain showers", icon: "🌦️" },
        82: { description: "Violent rain showers", icon: "🌧️" },
        85: { description: "Slight snow showers", icon: "❄️" },
        86: { description: "Heavy snow showers", icon: "❄️" },
        95: { description: "Thunderstorm", icon: "⛈️" },
        96: { description: "Thunderstorm with slight hail", icon: "⛈️" },
        99: { description: "Thunderstorm with heavy hail", icon: "⛈️" }
    };

    return weatherCodes[code] || { description: "Unknown weather", icon: "❓" };
}

// Check for dangerous weather conditions and issue alerts
function checkWeatherAlerts(data) {
    const alerts = [];
    const weatherCode = data.current.weather_code;
    const windSpeed = data.current.wind_speed_10m;
    const temp = data.current.temperature_2m;
    const precipitation = data.current.precipitation;

    // Check for severe weather conditions based on Open-Meteo weather codes
    if (weatherCode >= 95 && weatherCode <= 99) {
        alerts.push('⚡ THUNDERSTORM WARNING: Seek shelter immediately!');
    }

    if ((weatherCode >= 61 && weatherCode <= 67) && windSpeed > 20) {
        alerts.push('🌧️ HEAVY RAIN ALERT: Roads may be slippery, drive cautiously!');
    }

    if (windSpeed > 30) {
        alerts.push('💨 HIGH WIND WARNING: Strong winds detected, secure loose objects!');
    }

    if (temp > 40) {
        alerts.push('🔥 HEAT WARNING: Extreme heat conditions, stay hydrated!');
    }

    if (temp < 0) {
        alerts.push('❄️ FREEZE WARNING: Freezing temperatures, dress warmly!');
    }

    if ((weatherCode >= 71 && weatherCode <= 77) || (weatherCode >= 85 && weatherCode <= 86)) {
        alerts.push('❄️ SNOW ALERT: Snow conditions may affect travel!');
    }

    if (weatherCode === 45 || weatherCode === 48) {
        alerts.push('🌫️ FOG ALERT: Reduced visibility, drive carefully!');
    }

    if (precipitation > 10) {
        alerts.push('🌧️ HEAVY PRECIPITATION: Flooding risk, avoid low-lying areas!');
    }

    // Issue alerts if any dangerous conditions detected
    if (alerts.length > 0) {
        const weatherInfo = getWeatherDescription(weatherCode);
        const alertMessage = '🚨 WEATHER ALERT 🚨\n\n' + alerts.join('\n\n') +
                           '\n\nLocation: ' + data.latitude.toFixed(4) + ', ' + data.longitude.toFixed(4) +
                           '\nTemperature: ' + Math.round(temp) + '°C' +
                           '\nConditions: ' + weatherInfo.description +
                           '\nWind: ' + windSpeed + ' km/h' +
                           '\nPrecipitation: ' + precipitation + ' mm';

        // Browser notification
        if (Notification.permission === 'granted') {
            new Notification('Weather Safety Alert', {
                body: alertMessage,
                icon: '⚠️'
            });
        }

        // Alert dialog
        alert(alertMessage);

        // Log weather alert
        logAlert('weather_alert', alertMessage, {
            location: `${data.latitude.toFixed(4)}, ${data.longitude.toFixed(4)}`,
            alerts: alerts,
            weather: data
        });
    }
}

// Mock Blockchain ID Verification
function generateBlockchainHash(data) {
    // Simple hash simulation (not cryptographically secure)
    let hash = 0;
    const str = JSON.stringify(data);
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(16);
}

function verifyBlockchainID(user) {
    const userData = {
        id: user.id,
        name: user.name,
        email: user.email,
        timestamp: user.id // Using ID as timestamp for demo
    };

    const hash = generateBlockchainHash(userData);
    const storedHash = blockchainHashes.get(user.id);

    if (!storedHash) {
        // First verification - store hash
        blockchainHashes.set(user.id, hash);
        return { verified: true, hash, message: 'ID verified and stored on blockchain' };
    }

    const isValid = storedHash === hash;
    return {
        verified: isValid,
        hash,
        message: isValid ? 'Blockchain verification successful' : 'Blockchain verification failed - data tampering detected'
    };
}

// Dashboard Functions
function updateDashboard() {
    updateActiveTourists();
    updateRecentAlerts();
    updateSafetyHeatmap();
    updateBehaviorAnalysis();
}

function updateActiveTourists() {
    const tourists = JSON.parse(localStorage.getItem('users') || '[]');
    const activeCount = tourists.filter(u => u.verified).length;

    document.getElementById('active-tourists').innerHTML = `
        <p><strong>${activeCount}</strong> verified tourists</p>
        <p>Tracking: ${isTracking ? 'Active' : 'Inactive'}</p>
        <p>Last update: ${new Date().toLocaleTimeString()}</p>
    `;
}

function updateRecentAlerts() {
    const alerts = alertHistory.slice(-5); // Last 5 alerts
    const alertsDiv = document.getElementById('recent-alerts');

    if (alerts.length === 0) {
        alertsDiv.innerHTML = '<p>No recent alerts</p>';
        return;
    }

    alertsDiv.innerHTML = alerts.map(alert => `
        <div class="alert-item ${alert.type === 'safety_zone' ? 'danger' : ''}">
            <strong>${alert.type.toUpperCase()}</strong><br>
            ${alert.message.substring(0, 100)}...<br>
            <small>${new Date(alert.timestamp).toLocaleString()}</small>
        </div>
    `).join('');
}

function updateSafetyHeatmap() {
    const heatmap = document.getElementById('safety-heatmap');
    const ratings = ratingMarkers;

    if (ratings.length === 0) {
        heatmap.innerHTML = '<p>No safety data available</p>';
        return;
    }

    const avgRating = ratings.reduce((sum, r) => sum + r.rating, 0) / ratings.length;
    const lowSafety = ratings.filter(r => r.rating < 3).length;
    const highSafety = ratings.filter(r => r.rating >= 4).length;

    heatmap.innerHTML = `
        <p>Average Safety: ${avgRating.toFixed(1)}/5 ⭐</p>
        <p>Low Safety Zones: ${lowSafety}</p>
        <p>High Safety Zones: ${highSafety}</p>
        <p>Total Rated Locations: ${ratings.length}</p>
    `;
}

function updateBehaviorAnalysis() {
    const analysis = document.getElementById('behavior-analysis');

    if (behaviorHistory.length < 5) {
        analysis.innerHTML = '<p>Insufficient data for analysis</p>';
        return;
    }

    const patterns = detectPatterns();
    const predictions = generatePredictions(patterns);

    analysis.innerHTML = `
        <div class="behavior-pattern">
            <strong>Current Pattern:</strong><br>
            Average Speed: ${patterns.avgSpeed.toFixed(1)} m<br>
            Movement: ${patterns.erraticMovement ? 'Erratic' : 'Normal'}<br>
            Risk Level: ${(predictions.risk * 100).toFixed(1)}%<br>
            Status: ${predictions.recommendation}
        </div>
    `;
}

function logAlert(type, message, data = {}) {
    alertHistory.push({
        type,
        message,
        data,
        timestamp: Date.now()
    });

    // Keep only last 50 alerts
    if (alertHistory.length > 50) {
        alertHistory.shift();
    }
}

// AI Safety Assistant variables
let currentLocation = null;
let currentWeather = null;

// AI Assistant Functions
function toggleAssistant() {
    const chat = document.getElementById('assistant-chat');
    chat.classList.toggle('hidden');
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    // Add user message
    addMessage(message, 'user');
    input.value = '';

    // Show typing indicator
    showTypingIndicator();

    try {
        const response = await fetch('/api/ai-assistant', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                location: currentLocation,
                weather: currentWeather
            })
        });

        const data = await response.json();
        hideTypingIndicator();
        addMessage(data.response, 'bot');

    } catch (error) {
        hideTypingIndicator();
        addMessage('Sorry, I\'m having trouble connecting. Please try again.', 'bot');
        console.error('AI Assistant error:', error);
    }
}

function addMessage(text, type) {
    const messages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    if (type === 'user') {
        messageDiv.innerHTML = `<strong>You:</strong> ${text}`;
    } else {
        messageDiv.innerHTML = `<strong>AI Assistant:</strong> ${text}`;
    }

    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
}

function showTypingIndicator() {
    const messages = document.getElementById('chat-messages');
    const indicator = document.createElement('div');
    indicator.className = 'message bot-message';
    indicator.id = 'typing-indicator';
    indicator.innerHTML = '<strong>AI Assistant:</strong> <div class="typing-indicator"></div> Thinking...';
    messages.appendChild(indicator);
    messages.scrollTop = messages.scrollHeight;
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Safety News Functions
function toggleNews() {
    const news = document.getElementById('news-content');
    news.classList.toggle('hidden');
}

async function loadSafetyNews(location) {
    try {
        const response = await fetch(`/api/safety-news?location=${encodeURIComponent(location)}`);
        const data = await response.json();

        if (data.news) {
            displaySafetyNews(data.news);
        }
    } catch (error) {
        console.error('Safety news error:', error);
    }
}

function displaySafetyNews(news) {
    const newsList = document.getElementById('news-list');
    newsList.innerHTML = '';

    if (news.length === 0) {
        newsList.innerHTML = '<div class="news-item info">No safety news available for this location.</div>';
        return;
    }

    news.forEach(item => {
        const newsItem = document.createElement('div');
        newsItem.className = `news-item ${item.severity || 'info'}`;
        newsItem.innerHTML = `
            <strong>${item.title}</strong><br>
            ${item.description}<br>
            <small>${new Date(item.timestamp).toLocaleDateString()}</small>
        `;
        newsList.appendChild(newsItem);
    });
}

// Tourist Community Functions
function toggleCommunity() {
    const community = document.getElementById('community-content');
    community.classList.toggle('hidden');
}

async function loadTouristCommunity(lat, lng) {
    try {
        const response = await fetch(`/api/tourist-community?lat=${lat}&lng=${lng}`);
        const data = await response.json();

        if (data.tourists) {
            displayTouristCommunity(data.tourists);
        }
    } catch (error) {
        console.error('Community error:', error);
    }
}

function displayTouristCommunity(tourists) {
    const communityList = document.getElementById('community-list');
    communityList.innerHTML = '';

    if (tourists.length === 0) {
        communityList.innerHTML = '<div class="community-item">No tourists found nearby.</div>';
        return;
    }

    tourists.forEach(tourist => {
        const communityItem = document.createElement('div');
        communityItem.className = 'community-item';
        communityItem.innerHTML = `
            <strong>${tourist.name}</strong><br>
            <span class="distance">📍 ${tourist.distance} away</span><br>
            <span class="status">${tourist.status}</span><br>
            <small>Last seen: ${new Date(tourist.last_seen).toLocaleTimeString()}</small>
        `;
        communityList.appendChild(communityItem);
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    initMap();

    document.getElementById('location-btn').addEventListener('click', getCurrentLocation);
    document.getElementById('sos-btn').addEventListener('click', triggerSOS);
    document.getElementById('live-tracking-btn').addEventListener('click', startLiveTracking);

    // AI Assistant event listeners
    document.getElementById('assistant-toggle').addEventListener('click', toggleAssistant);
    document.getElementById('send-message').addEventListener('click', sendMessage);
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Safety News event listeners
    document.getElementById('news-toggle').addEventListener('click', toggleNews);

    // Tourist Community event listeners
    document.getElementById('community-toggle').addEventListener('click', toggleCommunity);

    // Search functionality
    document.getElementById('search-btn').addEventListener('click', () => {
        const query = document.getElementById('search-input').value.trim();
        if (query) {
            searchLocation(query);
        } else {
            alert('Please enter a location to search.');
        }
    });

    // Allow Enter key to trigger search
    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = e.target.value.trim();
            if (query) {
                searchLocation(query);
            } else {
                alert('Please enter a location to search.');
            }
        }
    });
});

// Auto-get location on load (optional)
window.addEventListener('load', () => {
    // Uncomment the line below to auto-get location on page load
    // getCurrentLocation();
    checkLoginStatus();

    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});

// User Authentication System
let currentUser = null;
let verificationCode = null;

// Check if user is logged in
function checkLoginStatus() {
    const userData = localStorage.getItem('currentUser');
    if (userData) {
        currentUser = JSON.parse(userData);
        updateUIForLoggedInUser();
    }
}

// Update UI for logged in user
function updateUIForLoggedInUser() {
    document.getElementById('user-info').textContent = `Welcome, ${currentUser.name}`;
    document.getElementById('login-btn').style.display = 'none';
    document.getElementById('signup-btn').style.display = 'none';
    document.getElementById('logout-btn').style.display = 'inline-block';
    document.getElementById('dashboard-btn').style.display = 'inline-block';

    // Blockchain verification
    const blockchainResult = verifyBlockchainID(currentUser);
    console.log('Blockchain verification:', blockchainResult);
}

// Update UI for logged out user
function updateUIForLoggedOutUser() {
    document.getElementById('user-info').textContent = 'Not logged in';
    document.getElementById('login-btn').style.display = 'inline-block';
    document.getElementById('signup-btn').style.display = 'inline-block';
    document.getElementById('logout-btn').style.display = 'none';
    document.getElementById('dashboard-btn').style.display = 'none';
}

// Modal management
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Generate verification code
function generateVerificationCode() {
    return Math.floor(100000 + Math.random() * 900000).toString();
}

// Login form handler
document.getElementById('login-form').addEventListener('submit', (e) => {
    e.preventDefault();

    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    // Get stored users
    const users = JSON.parse(localStorage.getItem('users') || '[]');
    const user = users.find(u => u.email === email && u.password === password);

    if (user) {
        if (user.verified) {
            currentUser = user;
            localStorage.setItem('currentUser', JSON.stringify(user));
            updateUIForLoggedInUser();
            closeModal('login-modal');
            alert('Login successful!');
        } else {
            alert('Please verify your email first.');
            openModal('verification-modal');
        }
    } else {
        alert('Invalid email or password.');
    }
});

// Signup form handler
document.getElementById('signup-form').addEventListener('submit', (e) => {
    e.preventDefault();

    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const confirmPassword = document.getElementById('signup-confirm-password').value;

    // Validation
    if (password !== confirmPassword) {
        alert('Passwords do not match.');
        return;
    }

    if (password.length < 6) {
        alert('Password must be at least 6 characters long.');
        return;
    }

    // Check if user already exists
    const users = JSON.parse(localStorage.getItem('users') || '[]');
    if (users.find(u => u.email === email)) {
        alert('User with this email already exists.');
        return;
    }

    // Create new user
    const newUser = {
        id: Date.now(),
        name,
        email,
        password,
        verified: false
    };

    users.push(newUser);
    localStorage.setItem('users', JSON.stringify(users));

    // Generate and store verification code
    verificationCode = generateVerificationCode();
    alert(`Verification code sent to ${email}: ${verificationCode}`);

    closeModal('signup-modal');
    openModal('verification-modal');
});

// Email verification handler
document.getElementById('verify-btn').addEventListener('click', () => {
    const code = document.getElementById('verification-code').value;

    if (code === verificationCode) {
        // Find and update user
        const users = JSON.parse(localStorage.getItem('users') || '[]');
        const userIndex = users.findIndex(u => u.email === document.getElementById('signup-email').value);

        if (userIndex !== -1) {
            users[userIndex].verified = true;
            localStorage.setItem('users', JSON.stringify(users));

            currentUser = users[userIndex];
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            updateUIForLoggedInUser();

            closeModal('verification-modal');
            alert('Email verified successfully! Welcome to the portal.');
        }
    } else {
        alert('Invalid verification code.');
    }
});

// Resend verification code
document.getElementById('resend-code-btn').addEventListener('click', () => {
    verificationCode = generateVerificationCode();
    alert(`New verification code sent: ${verificationCode}`);
});

// Logout handler
document.getElementById('logout-btn').addEventListener('click', () => {
    currentUser = null;
    localStorage.removeItem('currentUser');
    updateUIForLoggedOutUser();
    alert('Logged out successfully.');
});

// Modal event listeners
document.getElementById('login-btn').addEventListener('click', () => openModal('login-modal'));
document.getElementById('signup-btn').addEventListener('click', () => openModal('signup-modal'));
document.getElementById('dashboard-btn').addEventListener('click', () => {
    openModal('dashboard-modal');
    updateDashboard();
});

// Close modal when clicking on close button
document.querySelectorAll('.close').forEach(closeBtn => {
    closeBtn.addEventListener('click', (e) => {
        const modal = e.target.closest('.modal');
        closeModal(modal.id);
    });
});

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        closeModal(e.target.id);
    }
});