# ResQGrid 🚑

**Real-Time Emergency Resource Coordination Network**

ResQGrid is a college-level working prototype that connects an emergency request with nearby ambulances, hospitals, blood banks and pharmacies. It demonstrates resource matching, distance/ETA estimation, hospital ranking and operational dashboards.

> **Important:** This is an educational prototype. It is not a medical device or a real emergency-dispatch service. For a real emergency in India, contact your local emergency services (112) and qualified medical professionals.

## Features

- Emergency request creation
- Patient location capture using browser geolocation
- Hospital recommendation engine
- Smart hospital scoring using:
  - distance / estimated travel time
  - emergency department availability
  - emergency beds
  - ICU beds
  - specialist match
  - trauma capability
- Nearby available ambulance matching
- Ambulance assignment workflow
- Blood-bank inventory lookup
- Hospital resource status updates
- Ambulance status updates
- Emergency Command Center dashboard
- JSON API endpoints for future React/mobile clients
- SQLite database with demo data
- Responsive UI
- Leaflet/OpenStreetMap map integration

## Project structure

```text
ResQGrid/
├── app.py
├── requirements.txt
├── README.md
├── run.bat
├── run.sh
├── .gitignore
├── resqgrid.db              # created automatically on first run
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── emergency_new.html
│   ├── emergency_detail.html
│   └── dashboard.html
└── static/
    ├── css/style.css
    └── js/app.js
```

## Run on Windows

1. Install Python 3.10+.
2. Open this project folder in VS Code.
3. Open Terminal.
4. Run:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

5. Open:

```text
http://127.0.0.1:5000
```

You can also double-click `run.bat` after Python is installed.

## Run on Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Demo workflow

1. Open **Raise Emergency**.
2. Allow location access or enter the default Meerut demo coordinates.
3. Select emergency type, priority, blood group and specialist.
4. Submit.
5. The system ranks hospitals and available ambulances.
6. Assign a hospital and ambulance.
7. Open **Command Center** to see the network status.
8. Update hospital beds or ambulance status from the dashboard.
9. Complete the emergency to release the assigned ambulance.

## API examples

### All resources

```text
GET /api/resources
```

### Emergency recommendations

```text
GET /api/recommendations/1
```

### Blood availability

```text
GET /api/blood/O-
```

These endpoints can later power a React app, Android app or IoT/real-time layer.

## Important next upgrades

For a hackathon/advanced version:

- WebSocket-based live location
- Real map routing instead of straight-line distance
- Real authenticated hospital/ambulance accounts
- SMS/push notifications
- Hospital admission confirmation
- Blood reservation workflow
- Medicine inventory requests
- Audit logs
- PostgreSQL
- Redis / background jobs
- Role-based access control
- AI-assisted emergency text classification (coordination only, not diagnosis)
- Analytics and resource-demand prediction

## Demo data

The first launch automatically creates sample resources around Meerut. Delete `resqgrid.db` if you want to reset the demo database and seed it again.

## Disclaimer

Do not connect this prototype to real patient data, real hospital systems, real blood inventory or real emergency dispatch without appropriate security, privacy, regulatory, operational and medical review.
