// Smart Tourist Safety Portal - Flask Frontend JavaScript

// Initialize map
let map;
let userMarker;
let ratingMarkers = [];
let hotspotMarkers = [];

// Live tracking variables
let watchId = null;
let isTracking = false;
let lastNotificationTime = 0;
const NOTIFICATION_COOLDOWN = 30000; // 30 seconds

// Authentication variables
let currentUser = null;
let verificationCode = null;

// Red marker icon for user location
const redIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

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

                // Get ratings for current location
                fetch(`/api/ratings?lat=${lat}&lng=${lng}&radius=5`)
                    .then(response => response.json())
                    .then(ratingData => {
                        if (ratingData.average_rating !== null) {
                            document.getElementById('current-location').innerHTML =
                                `Current Location: ${lat.toFixed(4)}, ${lng.toFixed(4)}<br>
                                <small>Safety Rating: ${ratingData.average_rating} ⭐ (${ratingData.total_ratings} reviews within 5km)</small>`;
                        } else {
                            document.getElementById('current-location').innerHTML =
                                `Current Location: ${lat.toFixed(4)}, ${lng.toFixed(4)}<br>
                                <small>No safety ratings available for this area</small>`;
                        }
                    })
                    .catch(error => console.error('Error fetching location ratings:', error));

                // Auto-fetch weather for current location
                getWeatherForLocation(lat, lng);

                // Fetch tourist attractions and language info for current location
                fetchLocationInfo(lat, lng);
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
function onMapClick(e) {
    const rating = prompt('Rate the safety of this location (1-5 stars):');
    if (rating && rating >= 1 && rating <= 5) {
        // Send rating to server
        fetch('/api/ratings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                lat: e.latlng.lat,
                lng: e.latlng.lng,
                rating: parseInt(rating)
            })
        }).then(() => {
            // Reload ratings after adding new one
            loadRatings();
        });

        alert(`Thank you! Your ${rating}-star rating has been recorded.`);
    }
}

// Load ratings from server
async function loadRatings() {
    try {
        const response = await fetch('/api/ratings');
        const data = await response.json();

        // Clear existing markers
        ratingMarkers.forEach(rating => {
            map.removeLayer(rating.marker);
        });
        ratingMarkers = [];

        // Add proximity-grouped rating markers
        data.forEach(rating => {
            const marker = L.marker([rating.lat, rating.lng]).addTo(map)
                .bindPopup(`<div style="text-align: center;">
                    <strong>Safety Rating: ${rating.rating} ⭐</strong><br>
                    <small>Based on ${rating.count} reviews within 5km area</small><br>
                    <em>Click map to rate this area</em>
                </div>`);

            ratingMarkers.push({
                lat: rating.lat,
                lng: rating.lng,
                rating: rating.rating,
                count: rating.count,
                marker: marker
            });
        });

        updateRatingsList();
    } catch (error) {
        console.error('Error loading ratings:', error);
    }
}

// Load and display tourist hotspots
async function loadHotspots() {
    try {
        const response = await fetch('/api/hotspots');
        const data = await response.json();

        // Clear existing hotspot markers
        hotspotMarkers.forEach(hotspot => {
            map.removeLayer(hotspot.marker);
        });
        hotspotMarkers = [];

        // Add hotspot markers
        data.hotspots.forEach(hotspot => {
            // Create a custom icon for hotspots
            const hotspotIcon = L.divIcon({
                html: `<div style="background: linear-gradient(135deg, #ff6b6b, #ee5a24); border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px; border: 3px solid white; box-shadow: 0 2px 10px rgba(0,0,0,0.3);">${hotspot.tourist_count}</div>`,
                className: 'hotspot-marker',
                iconSize: [40, 40],
                iconAnchor: [20, 20]
            });

            const marker = L.marker([hotspot.lat, hotspot.lng], {icon: hotspotIcon}).addTo(map)
                .bindPopup(createHotspotPopup(hotspot));

            hotspotMarkers.push({
                id: hotspot.id,
                lat: hotspot.lat,
                lng: hotspot.lng,
                tourist_count: hotspot.tourist_count,
                marker: marker
            });
        });
    } catch (error) {
        console.error('Error loading hotspots:', error);
    }
}

// Create popup content for hotspots
function createHotspotPopup(hotspot) {
    const touristNames = hotspot.tourists.map(t => t.name).join(', ');
    return `
        <div style="text-align: center; max-width: 250px;">
            <h4 style="margin: 0 0 10px 0; color: #ff6b6b;">🫂 Tourist Hotspot!</h4>
            <p style="margin: 5px 0;"><strong>${hotspot.tourist_count} tourists</strong> in this area</p>
            <p style="margin: 5px 0; font-size: 12px;">Tourists: ${touristNames}</p>
            <button onclick="joinHotspot('${hotspot.id}')" style="background: #ff6b6b; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; margin-top: 10px;">
                Join Hotspot
            </button>
            <p style="margin: 8px 0; font-size: 11px; color: #666;">Meet fellow travelers and explore together!</p>
        </div>
    `;
}

// Join a tourist hotspot
async function joinHotspot(hotspotId) {
    try {
        const userName = currentUser ? currentUser.name : 'Anonymous Tourist';
        const userId = currentUser ? currentUser.id : 'anonymous_' + Date.now();

        const response = await fetch(`/api/hotspots/join/${hotspotId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                name: userName
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(data.message);
            // Refresh hotspots to show updated count
            loadHotspots();

            // Show notification
            if (Notification.permission === 'granted') {
                new Notification('Tourist Hotspot', {
                    body: 'Welcome to the tourist hotspot! Meet fellow travelers.',
                    icon: '/static/favicon.ico'
                });
            }
        } else {
            alert(data.message || 'Could not join hotspot');
        }
    } catch (error) {
        console.error('Error joining hotspot:', error);
        alert('Error joining hotspot. Please try again.');
    }
}

// Display language information
function displayLanguageInfo(languageData) {
    const languageDiv = document.getElementById('language-info');
    if (!languageDiv) return;

    if (languageData.language && languageData.phrases) {
        const lang = languageData.language;
        const phrases = languageData.phrases;

        languageDiv.innerHTML = `
            <div class="language-header">
                <h3>🌐 Local Language: ${lang.language}</h3>
                <p><strong>Script:</strong> ${lang.script} | <strong>Code:</strong> ${lang.code}</p>
            </div>
            <div class="language-greetings">
                <p><strong>Greeting:</strong> "${lang.greeting}"</p>
                <p><strong>Thank you:</strong> "${lang.thank_you}"</p>
            </div>
            <div class="language-phrases">
                <h4>Useful Tourist Phrases:</h4>
                <div class="phrase-grid">
                    <div class="phrase-item">
                        <span class="phrase-english">"Where is..."</span>
                        <span class="phrase-local">"${phrases.where_is}"</span>
                    </div>
                    <div class="phrase-item">
                        <span class="phrase-english">"How much..."</span>
                        <span class="phrase-local">"${phrases.how_much}"</span>
                    </div>
                    <div class="phrase-item">
                        <span class="phrase-english">"Water"</span>
                        <span class="phrase-local">"${phrases.water}"</span>
                    </div>
                    <div class="phrase-item">
                        <span class="phrase-english">"Food"</span>
                        <span class="phrase-local">"${phrases.food}"</span>
                    </div>
                    <div class="phrase-item">
                        <span class="phrase-english">"Help"</span>
                        <span class="phrase-local">"${phrases.help}"</span>
                    </div>
                    <div class="phrase-item">
                        <span class="phrase-english">"Bathroom"</span>
                        <span class="phrase-local">"${phrases.bathroom}"</span>
                    </div>
                    <div class="phrase-item">
                        <span class="phrase-english">"Taxi"</span>
                        <span class="phrase-local">"${phrases.taxi}"</span>
                    </div>
                    <div class="phrase-item">
                        <span class="phrase-english">"Hotel"</span>
                        <span class="phrase-local">"${phrases.hotel}"</span>
                    </div>
                </div>
            </div>
        `;
    } else {
        languageDiv.innerHTML = '<p>Language information not available for this location.</p>';
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
        stars.textContent = '★'.repeat(Math.round(rating.rating)) + '☆'.repeat(5 - Math.round(rating.rating));

        const countText = document.createElement('span');
        countText.className = 'rating-count';
        countText.textContent = ` (${rating.count} reviews)`;

        ratingItem.appendChild(locationText);
        ratingItem.appendChild(stars);
        ratingItem.appendChild(countText);
        ratingsList.appendChild(ratingItem);
    });
}

// Search location using Flask API
async function searchLocation(query) {
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (response.ok) {
            // Center map on searched location
            map.setView([data.lat, data.lng], 15);

            // Get ratings for this location (within 5km radius)
            const ratingsResponse = await fetch(`/api/ratings?lat=${data.lat}&lng=${data.lng}&radius=5`);
            const ratingsData = await ratingsResponse.json();

            // Get language information for this location
            // Use the original search query for better language detection
            const locationName = query.split(',')[0].trim();
            const languageResponse = await fetch(`/api/language/${encodeURIComponent(locationName)}`);
            const languageData = await languageResponse.json();

            let popupContent = `<b>${data.display_name}</b><br>`;

            // Add language information
            if (languageData.language) {
                popupContent += `<div style="margin-top: 8px; padding: 8px; background: rgba(100,200,255,0.9); border-radius: 4px; color: white;">
                    <strong>🌐 Local Language: ${languageData.language.language}</strong><br>
                    <small>Greeting: "${languageData.language.greeting}" | Thank you: "${languageData.language.thank_you}"</small>
                </div>`;
            }

            if (ratingsData.average_rating !== null) {
                popupContent += `<div style="margin-top: 8px; padding: 8px; background: rgba(255,255,255,0.9); border-radius: 4px;">
                    <strong>Safety Rating: ${ratingsData.average_rating} ⭐</strong><br>
                    <small>Based on ${ratingsData.total_ratings} reviews within 5km</small>
                </div>`;
            } else {
                popupContent += `<div style="margin-top: 8px; padding: 8px; background: rgba(255,255,255,0.9); border-radius: 4px;">
                    <em>No safety ratings available for this area</em>
                </div>`;
            }

            // Add marker for searched location
            L.marker([data.lat, data.lng]).addTo(map)
                .bindPopup(popupContent)
                .openPopup();

            // Update current location display with language info
            document.getElementById('current-location').innerHTML =
                `Searched: ${locationName}<br>
                <small style="color: #4a90e2;">🌐 ${languageData.language ? languageData.language.language : 'English'}</small>`;

            // Display language phrases
            displayLanguageInfo(languageData);

            // Fetch tourist attractions
            fetchAttractions(locationName);

            // Auto-fetch weather for searched location
            getWeatherForLocation(data.lat, data.lng);
        } else {
            alert('Location not found. Please try a different search term.');
        }
    } catch (error) {
        console.error('Search error:', error);
        alert('Error searching for location. Please try again.');
    }
}

// Fetch tourist attractions for a location
async function fetchAttractions(location) {
    try {
        const response = await fetch(`/api/tourist-attractions?location=${encodeURIComponent(location)}`);
        const data = await response.json();

        if (response.ok && data.attractions && data.attractions.length > 0) {
            displayAttractions(data.attractions);
        } else {
            displayAttractions([]);
        }
    } catch (error) {
        console.error('Attractions fetch error:', error);
        displayAttractions([]);
    }
}

// Display tourist attractions
function displayAttractions(attractions) {
    const attractionsDiv = document.getElementById('attractions-list');
    if (!attractionsDiv) return;

    attractionsDiv.innerHTML = '';

    if (attractions.length === 0) {
        attractionsDiv.innerHTML = '<p>No tourist attractions found for this location.</p>';
        return;
    }

    attractions.forEach(attraction => {
        const attractionItem = document.createElement('div');
        attractionItem.className = 'attraction-item';

        const nameLink = document.createElement('a');
        nameLink.href = attraction.url;
        nameLink.target = '_blank';
        nameLink.textContent = attraction.name;
        nameLink.className = 'attraction-link';

        const addBtn = document.createElement('button');
        addBtn.textContent = 'Add to Todo';
        addBtn.className = 'add-todo-btn';
        addBtn.onclick = () => addToTodo(attraction);

        attractionItem.appendChild(nameLink);
        attractionItem.appendChild(addBtn);
        attractionsDiv.appendChild(attractionItem);
    });
}

// Add attraction to todo list
function addToTodo(attraction) {
    let todoList = loadTodoFromStorage();
    if (!todoList.some(item => item.name === attraction.name)) {
        todoList.push(attraction);
        saveTodoToStorage(todoList);
        alert(`${attraction.name} added to your todo list!`);
        showTodoNotification();
    } else {
        alert(`${attraction.name} is already in your todo list.`);
    }
}

// Load todo list from localStorage
function loadTodoFromStorage() {
    const todo = localStorage.getItem('touristTodoList');
    return todo ? JSON.parse(todo) : [];
}

// Save todo list to localStorage
function saveTodoToStorage(todoList) {
    localStorage.setItem('touristTodoList', JSON.stringify(todoList));
}

// Show todo notification
function showTodoNotification() {
    if (Notification.permission === 'granted') {
        new Notification('Tourist Todo List', {
            body: 'New attraction added to your todo list!',
            icon: '/static/favicon.ico' // Assuming there's a favicon
        });
    }
    // Also show the todo popup
    showTodoPopup();
}

// Show todo list popup
function showTodoPopup() {
    const todoList = loadTodoFromStorage();
    const todoContent = document.getElementById('todo-content');
    if (!todoContent) return;

    todoContent.innerHTML = '';

    if (todoList.length === 0) {
        todoContent.innerHTML = '<p>Your todo list is empty.</p>';
    } else {
        todoList.forEach((item, index) => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'todo-item';

            // Handle both Wikipedia attractions and custom tasks
            if (item.url) {
                const nameLink = document.createElement('a');
                nameLink.href = item.url;
                nameLink.target = '_blank';
                nameLink.textContent = item.name;
                itemDiv.appendChild(nameLink);
            } else {
                const nameSpan = document.createElement('span');
                nameSpan.textContent = item.name;
                nameSpan.className = 'custom-task-name';
                itemDiv.appendChild(nameSpan);
            }

            const removeBtn = document.createElement('button');
            removeBtn.textContent = 'Remove';
            removeBtn.className = 'remove-todo-btn';
            removeBtn.onclick = () => removeFromTodo(index);

            itemDiv.appendChild(removeBtn);
            todoContent.appendChild(itemDiv);
        });
    }

    openModal('todo-modal');
}

// Remove from todo list
function removeFromTodo(index) {
    let todoList = loadTodoFromStorage();
    todoList.splice(index, 1);
    saveTodoToStorage(todoList);
    showTodoPopup(); // Refresh the popup
}

// Add custom task to todo list
function addCustomTask(taskName) {
    if (!taskName.trim()) {
        alert('Please enter a task name.');
        return;
    }

    let todoList = loadTodoFromStorage();
    const customTask = {
        name: taskName.trim(),
        type: 'custom',
        added: new Date().toISOString()
    };

    todoList.push(customTask);
    saveTodoToStorage(todoList);
    alert(`"${taskName}" added to your todo list!`);
    showTodoNotification();

    // Clear the input field
    document.getElementById('custom-task-input').value = '';

    // Refresh the popup
    showTodoPopup();
}

// Fetch location information (attractions and language) for coordinates
async function fetchLocationInfo(lat, lng) {
    try {
        // Reverse geocode to get location name
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=10`);
        const data = await response.json();

        if (data && data.display_name) {
            const locationName = data.display_name.split(',')[0];

            // Fetch tourist attractions
            await fetchAttractions(locationName);

            // Fetch language information
            await fetchLanguageInfo(locationName);

            return locationName;
        }
    } catch (error) {
        console.error('Location info fetch error:', error);
    }
    return null;
}

// Fetch language information for a location
async function fetchLanguageInfo(location) {
    try {
        const response = await fetch(`/api/language/${encodeURIComponent(location)}`);
        const data = await response.json();

        if (response.ok && data.language) {
            displayLanguageInfo(data);
        }
    } catch (error) {
        console.error('Language info fetch error:', error);
    }
}

// Display language information
function displayLanguageInfo(data) {
    const languageDiv = document.getElementById('language-info');
    if (!languageDiv) return;

    const language = data.language;
    const phrases = data.phrases;

    languageDiv.innerHTML = `
        <h3>🌐 Local Language: ${language.language}</h3>
        <div class="language-details">
            <p><strong>Language:</strong> ${language.language}</p>
            <p><strong>Code:</strong> ${language.code}</p>
            <p><strong>Script:</strong> ${language.script}</p>
            <p><strong>Greeting:</strong> "${language.greeting}"</p>
            <p><strong>Thank you:</strong> "${language.thank_you}"</p>
        </div>
        <div class="useful-phrases">
            <h4>📝 Useful Phrases:</h4>
            <ul>
                <li><strong>Where is:</strong> "${phrases.where_is}"</li>
                <li><strong>How much:</strong> "${phrases.how_much}"</li>
                <li><strong>Water:</strong> "${phrases.water}"</li>
                <li><strong>Food:</strong> "${phrases.food}"</li>
                <li><strong>Help:</strong> "${phrases.help}"</li>
                <li><strong>Bathroom:</strong> "${phrases.bathroom}"</li>
                <li><strong>Taxi:</strong> "${phrases.taxi}"</li>
                <li><strong>Hotel:</strong> "${phrases.hotel}"</li>
            </ul>
        </div>
    `;
}

// Get weather for coordinates using Flask API
async function getWeatherForLocation(lat, lng) {
    try {
        const response = await fetch(`/api/weather?lat=${lat}&lng=${lng}`);
        const data = await response.json();

        if (response.ok) {
            displayWeather(data);

            // Check for weather alerts
            if (data.alerts && data.alerts.length > 0) {
                const alertMessage = '🚨 WEATHER ALERT 🚨\n\n' + data.alerts.join('\n\n') +
                                   `\n\nLocation: ${data.coordinates}`;
                alert(alertMessage);
            }
        } else {
            document.getElementById('weather-display').innerHTML =
                `<span style="color: #f5576c;">Weather data unavailable: ${data.error}</span>`;
        }
    } catch (error) {
        console.error('Weather API error:', error);
        document.getElementById('weather-display').innerHTML =
            `<span style="color: #f5576c;">Weather data unavailable: ${error.message}</span>`;
    }
}

// Display weather information
function displayWeather(data) {
    const weatherHtml = `
        <div class="weather-content">
            <div class="weather-main">
                <span class="weather-icon">${data.icon}</span>
                <div class="weather-temp">
                    <span class="temp">${data.temperature}°C</span>
                    <span class="feels-like">Feels like ${data.feels_like}°C</span>
                </div>
            </div>
            <div class="weather-details">
                <p><strong>${data.description}</strong></p>
                <p>Humidity: ${data.humidity}%</p>
                <p>Wind: ${data.wind_speed} km/h</p>
                <p>Precipitation: ${data.precipitation} mm</p>
                <p>Coordinates: ${data.coordinates}</p>
            </div>
        </div>
    `;

    document.getElementById('weather-display').innerHTML = weatherHtml;
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
        // Get current location for SOS
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;

                    // Send SOS to server
                    fetch('/api/sos', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            location: `${lat.toFixed(6)}, ${lng.toFixed(6)}`
                        })
                    }).then(response => response.json())
                      .then(data => {
                          alert(data.message || 'SOS ALERT TRIGGERED!\n\nEmergency services have been notified.');
                      })
                      .catch(error => {
                          console.error('SOS error:', error);
                          alert('SOS ALERT TRIGGERED!\n\nEmergency services have been notified.');
                      });
                }
            );
        } else {
            alert('SOS ALERT TRIGGERED!\n\nEmergency services have been notified.');
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

            // Update location info with ratings
            fetch(`/api/ratings?lat=${lat}&lng=${lng}&radius=5`)
                .then(response => response.json())
                .then(ratingData => {
                    if (ratingData.average_rating !== null) {
                        document.getElementById('current-location').innerHTML =
                            `Tracking: ${lat.toFixed(4)}, ${lng.toFixed(4)}<br>
                            <small>Safety Rating: ${ratingData.average_rating} ⭐ (${ratingData.total_ratings} reviews within 5km)</small>`;
                    } else {
                        document.getElementById('current-location').innerHTML =
                            `Tracking: ${lat.toFixed(4)}, ${lng.toFixed(4)}<br>
                            <small>No safety ratings available for this area</small>`;
                    }
                })
                .catch(error => {
                    document.getElementById('current-location').textContent =
                        `Tracking: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
                    console.error('Error fetching tracking ratings:', error);
                });

            // Send behavior data to server
            if (currentUser) {
                fetch('/api/behavior', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: currentUser.id,
                        lat: lat,
                        lng: lng,
                        name: currentUser.name
                    })
                }).catch(error => console.error('Behavior update error:', error));
            } else {
                // Send anonymous location data for hotspot detection
                fetch('/api/behavior', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: 'anonymous_' + Date.now(),
                        lat: lat,
                        lng: lng,
                        name: 'Anonymous Tourist'
                    })
                }).catch(error => console.error('Anonymous behavior update error:', error));
            }

            // Fetch location info for live tracking (only once when tracking starts)
            if (!window.locationInfoFetched) {
                fetchLocationInfo(lat, lng);
                window.locationInfoFetched = true;
            }

            // Refresh hotspots after location update
            setTimeout(() => loadHotspots(), 1000);
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

// Event listeners
document.addEventListener('DOMContentLoaded', async () => {
    initMap();

    // Check authentication status
    await checkAuthStatus();

    // Side panel controls
    document.getElementById('sidebar-toggle').addEventListener('click', toggleSidebar);
    document.getElementById('sidebar-close').addEventListener('click', closeSidebar);

    // Main functionality buttons
    document.getElementById('location-btn').addEventListener('click', getCurrentLocation);
    document.getElementById('sos-btn').addEventListener('click', triggerSOS);
    document.getElementById('live-tracking-btn').addEventListener('click', startLiveTracking);
    document.getElementById('weather-btn').addEventListener('click', checkWeather);
    document.getElementById('todo-btn').addEventListener('click', showTodoPopup);

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

    // Load ratings
    await loadRatings();

    // Load hotspots
    await loadHotspots();

    // Refresh hotspots every 30 seconds
    setInterval(loadHotspots, 30000);
});

// Authentication Functions
async function registerUser(name, email, password) {
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });
        const data = await response.json();

        if (response.ok) {
            alert(data.message);
            return data;
        } else {
            alert(data.error);
            return null;
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('Registration failed');
        return null;
    }
}

async function verifyEmail(email, code) {
    try {
        const response = await fetch('/api/auth/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, code })
        });
        const data = await response.json();

        if (response.ok) {
            alert(data.message);
            return true;
        } else {
            alert(data.error);
            return false;
        }
    } catch (error) {
        console.error('Verification error:', error);
        alert('Verification failed');
        return false;
    }
}

async function loginUser(email, password) {
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await response.json();

        if (response.ok) {
            currentUser = data.user;
            updateAuthUI();
            alert(data.message);
            return true;
        } else {
            alert(data.error);
            return false;
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed');
        return false;
    }
}

async function logoutUser() {
    try {
        await fetch('/api/auth/logout');
        currentUser = null;
        updateAuthUI();
        alert('Logged out successfully');
    } catch (error) {
        console.error('Logout error:', error);
    }
}

async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();

        if (data.logged_in) {
            currentUser = data.user;
            updateAuthUI();
        }
    } catch (error) {
        console.error('Auth status check error:', error);
    }
}

function updateAuthUI() {
    const userInfo = document.getElementById('user-info');
    const loginBtn = document.getElementById('login-btn');
    const signupBtn = document.getElementById('signup-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const dashboardBtn = document.getElementById('dashboard-btn');

    if (currentUser) {
        userInfo.textContent = `Welcome, ${currentUser.name}`;
        loginBtn.style.display = 'none';
        signupBtn.style.display = 'none';
        logoutBtn.style.display = 'inline-block';
        dashboardBtn.style.display = 'inline-block';
    } else {
        userInfo.textContent = 'Not logged in';
        loginBtn.style.display = 'inline-block';
        signupBtn.style.display = 'inline-block';
        logoutBtn.style.display = 'none';
        dashboardBtn.style.display = 'none';
    }
}

// Dashboard Functions
async function loadDashboard() {
    try {
        const response = await fetch('/api/dashboard');
        const data = await response.json();

        updateDashboardUI(data);
    } catch (error) {
        console.error('Dashboard load error:', error);
    }
}

function updateDashboardUI(data) {
    document.getElementById('active-tourists').innerHTML = `
        <p><strong>${data.active_tourists}</strong> verified tourists</p>
        <p>Tracking: Active</p>
        <p>Last update: ${new Date().toLocaleTimeString()}</p>
    `;

    const alertsDiv = document.getElementById('recent-alerts');
    if (data.recent_alerts.length === 0) {
        alertsDiv.innerHTML = '<p>No recent alerts</p>';
    } else {
        alertsDiv.innerHTML = data.recent_alerts.map(alert => `
            <div class="alert-item ${alert.type === 'sos' ? 'danger' : ''}">
                <strong>${alert.type.toUpperCase()}</strong><br>
                ${alert.message.substring(0, 100)}...<br>
                <small>${new Date(alert.timestamp).toLocaleString()}</small>
            </div>
        `).join('');
    }

    const heatmap = document.getElementById('safety-heatmap');
    heatmap.innerHTML = `
        <p>Average Safety: ${data.safety_heatmap.average_rating}/5 ⭐</p>
        <p>Low Safety Zones: ${data.safety_heatmap.low_safety_zones}</p>
        <p>High Safety Zones: ${data.safety_heatmap.high_safety_zones}</p>
        <p>Total Rated Locations: ${data.safety_heatmap.total_rated}</p>
    `;

    const analysis = document.getElementById('behavior-analysis');
    analysis.innerHTML = `
        <div class="behavior-pattern">
            <strong>AI Analysis Status:</strong><br>
            Total Users: ${data.behavior_analysis.total_users}<br>
            Average Movements: ${data.behavior_analysis.average_movements}<br>
            Status: ${data.behavior_analysis.status}
        </div>
    `;
}

// Modal management
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Event listeners for modals
document.addEventListener('DOMContentLoaded', () => {
    // Modal close buttons
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

    // Authentication buttons
    document.getElementById('login-btn').addEventListener('click', () => openModal('login-modal'));
    document.getElementById('signup-btn').addEventListener('click', () => openModal('signup-modal'));
    document.getElementById('logout-btn').addEventListener('click', logoutUser);
    document.getElementById('dashboard-btn').addEventListener('click', () => {
        openModal('dashboard-modal');
        loadDashboard();
    });

    // Form submissions
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('signup-form').addEventListener('submit', handleSignup);
    document.getElementById('verify-btn').addEventListener('click', handleVerification);
    document.getElementById('resend-code-btn').addEventListener('click', handleResendCode);

    // Custom task addition
    document.getElementById('add-custom-task-btn').addEventListener('click', () => {
        const taskInput = document.getElementById('custom-task-input');
        const taskName = taskInput.value.trim();
        addCustomTask(taskName);
    });

    // Allow Enter key to add custom task
    document.getElementById('custom-task-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const taskName = e.target.value.trim();
            addCustomTask(taskName);
        }
    });
});

// Form handlers
async function handleSignup(e) {
    e.preventDefault();
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const confirmPassword = document.getElementById('signup-confirm-password').value;

    if (password !== confirmPassword) {
        alert('Passwords do not match');
        return;
    }

    const result = await registerUser(name, email, password);
    if (result) {
        closeModal('signup-modal');
        openModal('verification-modal');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    const success = await loginUser(email, password);
    if (success) {
        closeModal('login-modal');
    }
}

async function handleVerification() {
    const email = document.getElementById('signup-email').value;
    const code = document.getElementById('verification-code').value;

    const success = await verifyEmail(email, code);
    if (success) {
        closeModal('verification-modal');
    }
}

async function handleResendCode() {
    const email = document.getElementById('signup-email').value;
    alert(`New verification code sent to ${email}`);
}

// Side Panel Functionality
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.remove('open');
}

// Close sidebar when clicking outside
document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');

    if (!sidebar.contains(e.target) && e.target !== toggleBtn && !toggleBtn.contains(e.target)) {
        closeSidebar();
    }
});

// Request notification permission
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}