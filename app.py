from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import sqlite3, math, os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "resqgrid.db")

app = Flask(__name__)
app.secret_key = os.environ.get("RESQGRID_SECRET", "dev-only-change-this-secret")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS hospitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        emergency_available INTEGER DEFAULT 1,
        icu_beds INTEGER DEFAULT 0,
        emergency_beds INTEGER DEFAULT 0,
        trauma INTEGER DEFAULT 0,
        specialist TEXT DEFAULT '',
        phone TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS ambulances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        type TEXT DEFAULT 'Basic',
        status TEXT DEFAULT 'Available',
        hospital_id INTEGER,
        FOREIGN KEY(hospital_id) REFERENCES hospitals(id)
    );

    CREATE TABLE IF NOT EXISTS blood_banks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        phone TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS blood_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        blood_bank_id INTEGER NOT NULL,
        blood_group TEXT NOT NULL,
        units INTEGER DEFAULT 0,
        UNIQUE(blood_bank_id, blood_group),
        FOREIGN KEY(blood_bank_id) REFERENCES blood_banks(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS pharmacies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        phone TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pharmacy_id INTEGER NOT NULL,
        medicine TEXT NOT NULL,
        units INTEGER DEFAULT 0,
        UNIQUE(pharmacy_id, medicine),
        FOREIGN KEY(pharmacy_id) REFERENCES pharmacies(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS emergencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT NOT NULL,
        emergency_type TEXT NOT NULL,
        priority TEXT DEFAULT 'High',
        blood_group TEXT DEFAULT '',
        specialist TEXT DEFAULT '',
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        notes TEXT DEFAULT '',
        status TEXT DEFAULT 'Searching',
        hospital_id INTEGER,
        ambulance_id INTEGER,
        created_at TEXT NOT NULL,
        FOREIGN KEY(hospital_id) REFERENCES hospitals(id),
        FOREIGN KEY(ambulance_id) REFERENCES ambulances(id)
    );
    """)

    # Seed only when the main table is empty.
    if conn.execute("SELECT COUNT(*) FROM hospitals").fetchone()[0] == 0:
        hospitals = [
            ("City Trauma & Emergency Hospital", 28.9845, 77.7064, 1, 6, 14, 1, "Trauma,Cardiology,Orthopedics", "0121-4001001"),
            ("Metro Multispeciality Hospital", 28.9620, 77.7000, 1, 3, 9, 1, "Cardiology,Neurology,General", "0121-4001002"),
            ("Shakti Medical Centre", 28.9950, 77.7250, 1, 1, 5, 0, "General,Pediatrics", "0121-4001003"),
            ("Green Valley Hospital", 28.9700, 77.7350, 0, 0, 2, 0, "General", "0121-4001004"),
        ]
        conn.executemany("""INSERT INTO hospitals
            (name,lat,lng,emergency_available,icu_beds,emergency_beds,trauma,specialist,phone)
            VALUES (?,?,?,?,?,?,?,?,?)""", hospitals)

        ambulances = [
            ("RG-A101", 28.9780, 77.7100, "Advanced Life Support", "Available", 1),
            ("RG-A102", 28.9880, 77.6950, "Basic Life Support", "Available", 2),
            ("RG-A103", 29.0000, 77.7150, "Advanced Life Support", "Busy", 1),
            ("RG-A104", 28.9500, 77.7200, "Basic Life Support", "Available", 3),
        ]
        conn.executemany("""INSERT INTO ambulances
            (code,lat,lng,type,status,hospital_id) VALUES (?,?,?,?,?,?)""", ambulances)

        blood_banks = [
            ("Meerut Central Blood Bank", 28.9785, 77.7060, "0121-4102001"),
            ("LifeSave Blood Centre", 28.9520, 77.7150, "0121-4102002"),
            ("RedDrop Community Blood Bank", 28.9980, 77.7300, "0121-4102003"),
        ]
        conn.executemany("INSERT INTO blood_banks (name,lat,lng,phone) VALUES (?,?,?,?)", blood_banks)

        for bank_id, inventory in [
            (1, [("A+",12),("A-",3),("B+",9),("B-",2),("O+",15),("O-",2),("AB+",4),("AB-",1)]),
            (2, [("A+",6),("A-",1),("B+",7),("B-",1),("O+",10),("O-",1),("AB+",2),("AB-",0)]),
            (3, [("A+",5),("A-",2),("B+",4),("B-",1),("O+",8),("O-",0),("AB+",3),("AB-",1)]),
        ]:
            conn.executemany("INSERT INTO blood_inventory (blood_bank_id,blood_group,units) VALUES (?,?,?)",
                             [(bank_id,g,u) for g,u in inventory])

        pharmacies = [
            ("MedPoint Pharmacy", 28.9850, 77.7180, "0121-4203001"),
            ("24x7 Care Pharmacy", 28.9680, 77.6900, "0121-4203002"),
            ("HealthHub Pharmacy", 28.9990, 77.7200, "0121-4203003"),
        ]
        conn.executemany("INSERT INTO pharmacies (name,lat,lng,phone) VALUES (?,?,?,?)", pharmacies)

        meds = [
            (1,"Adrenaline",20),(1,"Saline",50),(1,"Paracetamol",100),
            (2,"Adrenaline",10),(2,"Saline",40),(2,"Paracetamol",80),
            (3,"Adrenaline",0),(3,"Saline",20),(3,"Paracetamol",60)
        ]
        conn.executemany("INSERT INTO medicines (pharmacy_id,medicine,units) VALUES (?,?,?)", meds)

    conn.commit()
    conn.close()

def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2-lat1)
    dl = math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def priority_score(priority):
    return {"Critical": 100, "High": 80, "Medium": 60, "Low": 40}.get(priority, 60)

def hospital_recommendations(emergency):
    conn = db()
    hospitals = conn.execute("SELECT * FROM hospitals").fetchall()
    results = []
    requested = (emergency["specialist"] or "").strip().lower()

    for h in hospitals:
        distance = haversine_km(emergency["lat"], emergency["lng"], h["lat"], h["lng"])
        specialist_match = 1 if requested and any(requested in x.strip().lower() for x in h["specialist"].split(",")) else 0
        trauma_match = 1 if emergency["emergency_type"].lower() in ["accident", "severe bleeding", "trauma"] and h["trauma"] else 0

        score = 0
        score += max(0, 30 - min(distance * 5, 30))
        score += 25 if h["emergency_available"] else 0
        score += min(h["emergency_beds"] * 2, 15)
        score += min(h["icu_beds"] * 2, 10) if emergency["priority"] == "Critical" else min(h["icu_beds"], 5)
        score += 12 if specialist_match else 0
        score += 8 if trauma_match else 0
        score = round(min(score, 100), 1)

        results.append({
            "id": h["id"], "name": h["name"], "phone": h["phone"],
            "lat": h["lat"], "lng": h["lng"], "distance_km": round(distance, 2),
            "eta_min": max(2, round(distance / 0.45)), "score": score,
            "emergency_available": bool(h["emergency_available"]),
            "icu_beds": h["icu_beds"], "emergency_beds": h["emergency_beds"],
            "trauma": bool(h["trauma"]), "specialist": h["specialist"],
            "specialist_match": bool(specialist_match), "trauma_match": bool(trauma_match)
        })
    conn.close()
    return sorted(results, key=lambda x: (-x["score"], x["eta_min"]))

def nearest_ambulances(emergency):
    conn = db()
    rows = conn.execute("SELECT * FROM ambulances WHERE status='Available'").fetchall()
    data = []
    for a in rows:
        d = haversine_km(emergency["lat"], emergency["lng"], a["lat"], a["lng"])
        data.append({**dict(a), "distance_km": round(d,2), "eta_min": max(2, round(d/0.45))})
    conn.close()
    return sorted(data, key=lambda x: x["distance_km"])

@app.route("/")
def index():
    conn = db()
    stats = {
        "hospitals": conn.execute("SELECT COUNT(*) FROM hospitals").fetchone()[0],
        "ambulances": conn.execute("SELECT COUNT(*) FROM ambulances WHERE status='Available'").fetchone()[0],
        "blood_banks": conn.execute("SELECT COUNT(*) FROM blood_banks").fetchone()[0],
        "active": conn.execute("SELECT COUNT(*) FROM emergencies WHERE status NOT IN ('Completed','Cancelled')").fetchone()[0]
    }
    conn.close()
    return render_template("index.html", stats=stats)

@app.route("/emergency/new", methods=["GET","POST"])
def new_emergency():
    if request.method == "POST":
        f = request.form
        try:
            lat = float(f["lat"]); lng = float(f["lng"])
        except (ValueError, KeyError):
            flash("Please provide a valid location.", "danger")
            return redirect(url_for("new_emergency"))

        conn = db()
        cur = conn.execute("""INSERT INTO emergencies
            (patient_name,emergency_type,priority,blood_group,specialist,lat,lng,notes,status,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (f.get("patient_name","Anonymous"), f.get("emergency_type","Other"),
             f.get("priority","High"), f.get("blood_group",""), f.get("specialist",""),
             lat,lng,f.get("notes",""),"Searching",datetime.now().isoformat(timespec="seconds")))
        emergency_id = cur.lastrowid
        conn.commit()
        conn.close()
        return redirect(url_for("emergency_detail", emergency_id=emergency_id))
    return render_template("emergency_new.html")

@app.route("/emergency/<int:emergency_id>")
def emergency_detail(emergency_id):
    conn = db()
    e = conn.execute("SELECT * FROM emergencies WHERE id=?", (emergency_id,)).fetchone()
    conn.close()
    if not e:
        return "Emergency not found", 404
    return render_template("emergency_detail.html", emergency=e,
                           recommendations=hospital_recommendations(e),
                           ambulances=nearest_ambulances(e))

@app.post("/emergency/<int:emergency_id>/assign")
def assign_emergency(emergency_id):
    ambulance_id = request.form.get("ambulance_id", type=int)
    hospital_id = request.form.get("hospital_id", type=int)
    conn = db()
    if ambulance_id:
        conn.execute("UPDATE ambulances SET status='Assigned' WHERE id=? AND status='Available'", (ambulance_id,))
    if hospital_id:
        conn.execute("UPDATE emergencies SET hospital_id=?, status='Coordinating' WHERE id=?", (hospital_id, emergency_id))
    if ambulance_id:
        conn.execute("UPDATE emergencies SET ambulance_id=?, status='Ambulance Assigned' WHERE id=?", (ambulance_id, emergency_id))
    conn.commit()
    conn.close()
    flash("Emergency coordination updated.", "success")
    return redirect(url_for("emergency_detail", emergency_id=emergency_id))

@app.post("/emergency/<int:emergency_id>/complete")
def complete_emergency(emergency_id):
    conn = db()
    e = conn.execute("SELECT ambulance_id FROM emergencies WHERE id=?", (emergency_id,)).fetchone()
    if e and e["ambulance_id"]:
        conn.execute("UPDATE ambulances SET status='Available' WHERE id=?", (e["ambulance_id"],))
    conn.execute("UPDATE emergencies SET status='Completed' WHERE id=?", (emergency_id,))
    conn.commit(); conn.close()
    return redirect(url_for("emergency_detail", emergency_id=emergency_id))

@app.route("/dashboard")
def dashboard():
    conn = db()
    emergencies = conn.execute("""SELECT e.*, h.name hospital_name, a.code ambulance_code
        FROM emergencies e
        LEFT JOIN hospitals h ON h.id=e.hospital_id
        LEFT JOIN ambulances a ON a.id=e.ambulance_id
        ORDER BY e.id DESC LIMIT 20""").fetchall()
    hospitals = conn.execute("SELECT * FROM hospitals").fetchall()
    ambulances = conn.execute("SELECT * FROM ambulances").fetchall()
    blood = conn.execute("""SELECT b.name, bi.blood_group, bi.units
        FROM blood_banks b JOIN blood_inventory bi ON bi.blood_bank_id=b.id
        ORDER BY b.name, bi.blood_group""").fetchall()
    conn.close()
    return render_template("dashboard.html", emergencies=emergencies, hospitals=hospitals,
                           ambulances=ambulances, blood=blood)

@app.get("/api/recommendations/<int:emergency_id>")
def api_recommendations(emergency_id):
    conn = db()
    e = conn.execute("SELECT * FROM emergencies WHERE id=?", (emergency_id,)).fetchone()
    conn.close()
    if not e: return jsonify({"error":"Emergency not found"}), 404
    return jsonify({"hospitals": hospital_recommendations(e), "ambulances": nearest_ambulances(e)})

@app.get("/api/resources")
def api_resources():
    conn = db()
    hospitals = [dict(x) for x in conn.execute("SELECT * FROM hospitals").fetchall()]
    ambulances = [dict(x) for x in conn.execute("SELECT * FROM ambulances").fetchall()]
    banks = [dict(x) for x in conn.execute("SELECT * FROM blood_banks").fetchall()]
    pharmacies = [dict(x) for x in conn.execute("SELECT * FROM pharmacies").fetchall()]
    conn.close()
    return jsonify({"hospitals":hospitals,"ambulances":ambulances,"blood_banks":banks,"pharmacies":pharmacies})

@app.post("/hospital/<int:hospital_id>/update")
def update_hospital(hospital_id):
    f = request.form
    conn = db()
    conn.execute("""UPDATE hospitals SET emergency_available=?, icu_beds=?, emergency_beds=?
                    WHERE id=?""",
                 (1 if f.get("emergency_available") else 0,
                  max(0, int(f.get("icu_beds",0))), max(0,int(f.get("emergency_beds",0))), hospital_id))
    conn.commit(); conn.close()
    flash("Hospital resource status updated.", "success")
    return redirect(url_for("dashboard"))

@app.post("/ambulance/<int:ambulance_id>/status")
def update_ambulance(ambulance_id):
    status = request.form.get("status","Available")
    if status not in ["Available","Busy","Assigned"]:
        status = "Available"
    conn = db()
    conn.execute("UPDATE ambulances SET status=? WHERE id=?", (status, ambulance_id))
    conn.commit(); conn.close()
    return redirect(url_for("dashboard"))

@app.get("/api/blood/<blood_group>")
def api_blood(blood_group):
    conn = db()
    rows = conn.execute("""SELECT b.*, bi.blood_group, bi.units
        FROM blood_banks b JOIN blood_inventory bi ON bi.blood_bank_id=b.id
        WHERE UPPER(bi.blood_group)=UPPER(?) AND bi.units>0""", (blood_group,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.context_processor
def inject_globals():
    return {"app_name":"ResQGrid"}

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
