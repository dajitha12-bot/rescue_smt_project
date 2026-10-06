# RESCUEGRID
### Multi-Region Emergency Response & Relief Platform for India

**RESCUEGRID** is a production-grade, human-designed emergency operations and disaster relief platform engineered specifically for regional and national emergency coordination across India (with dedicated operational support for Tamil Nadu and multi-state disaster coordination).

The platform bridges real-time hazard monitoring from the **Global Disaster Alert and Coordination System (GDACS)**, multi-tier incident intake, algorithmic priority triage, automated fair resource allocation, and multi-facility capacity monitoring.

---

## 🎨 Design Theme & System

- **Primary Brand Color**: `#FE8D01` (Safety Rescue Orange)
- **Secondary Brand Color**: `#FFA53F` (Warm Accent Orange)
- **Neutral Palette**: Clean white (`#FFFFFF`), Soft warm-gray (`#F8F9FA` / `#F3F4F6`), and Dark Charcoal (`#1F2937` / `#111827`)
- **Philosophy**: Designed like a real emergency command center: clean, modern, high-contrast, robust, trustworthy, and devoid of AI clichés, decorative fluff, glassmorphism, or fake data.

---

## 👥 Role Architecture

1. **Operations Administrator (`ADMIN`)**
   - Command & Control operations dashboard
   - GDACS live disaster feed sync & management
   - Multi-layer GIS operations map (India-wide & Tamil Nadu coordinate bounds)
   - Incident triage & responder dispatch
   - Resource depot inventory & restock controls
   - Donations pipeline verification (`Submitted` &rarr; `Verified` &rarr; `Received` &rarr; `Allocated` &rarr; `Delivered`)
   - Hospital & shelter capacity management
   - Real response-time metrics and fair resource allocation simulations
   - Administrative database records inspector

2. **Affected Person / Citizen & Hospital Facility User (`USER`)**
   - **Citizen / Affected Person**:
     - Quick emergency intake with automatic browser GPS pin-drop or manual coordinates
     - Real-time incident tracking with mathematical priority breakdown
     - Directory of nearby hospitals (available beds, ICU, oxygen) and shelters
     - Localized safety map
   - **Hospital User (Subtype)**:
     - Direct facility dashboard overlay
     - Live management of available beds, ICU beds, oxygen supplies (liters), and ambulances

3. **Relief Donor (`DONOR`)**
   - Relief Need Summary (actual unmet demand from active ground requests)
   - Supply pledge & donation form with target region and logistics notes
   - Donation status lifecycle tracking
   - Transparent delivery metrics computed strictly from verified database records

---

## ⚙️ Mathematical Models & Algorithms

### 1. Emergency Priority Score (PS)
Triages incidents using a documented multi-criteria model based purely on actual request parameters:
$$\text{PS} = 0.35S + 0.25P + 0.20W + 0.10R + 0.10D$$
Where:
- $S$ = Severity (1–5 scale, normalized to 10)
- $P$ = Population Affected (count scaled 0–10)
- $W$ = Waiting Time (hours elapsed, normalized)
- $R$ = Resource Shortage (unmet demand ratio)
- $D$ = Distance from Available Help (isolation factor in km)

**Classification**:
- **Critical**: $\text{PS} \ge 7.5$
- **High**: $5.5 \le \text{PS} < 7.5$
- **Medium**: $3.5 \le \text{PS} < 5.5$
- **Low**: $\text{PS} < 3.5$

### 2. Fair Resource Allocation (RA)
Dynamically calculates equitable supply distribution across active unfulfilled incidents:
$$\text{RA}_i = \left[ \frac{N_i \times D_i \times S_i}{\sum (N_i \times D_i \times S_i)} \right] \times R_t$$
Where:
- $N_i$ = Quantity needed by request $i$
- $D_i$ = Distance factor $(1 + \frac{\text{dist}}{50})$
- $S_i$ = Severity factor
- $R_t$ = Total available resource pool in depots

### 3. Incident Response Time
$$\text{Response Time} = \text{Resolved Time} - \text{Reported Time}$$
- Strictly computed from closed incidents. If no incidents have been resolved, the system accurately displays:
  > *"No response-time data available yet"*

---

## 🌐 Official GDACS Live Feed Integration

- Connects to official GDACS XML RSS service: `https://www.gdacs.org/xml/rss.xml`
- Parses real-time global events with exact coordinates, disaster types (FL, TC, EQ, DR, VO, WF), severity, and alert levels (Red, Orange, Green)
- Prevents duplicates using unique `external_event_id`
- **Tamil Nadu Coordinate Filtering**: Strictly applies real geographic boundaries:
  - Latitude: $8.08^\circ\text{ N}$ to $13.55^\circ\text{ N}$
  - Longitude: $76.24^\circ\text{ E}$ to $80.35^\circ\text{ E}$
- **No-Fake-Data Rule**: Never invents disaster events, random coordinates, or mock statistics.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Django 6.0+
- SQLite (included)

### Setup & Run
From the project directory:
```bash
# 1. Apply database migrations
python manage.py migrate

# 2. Seed initial operational accounts, facilities, and sync live GDACS feed
python manage.py seed_data

# 3. Start development server
python manage.py runserver 127.0.0.1:8000
```

Open your browser at: `http://127.0.0.1:8000/`

---

## 🔑 Pre-Configured Demo Accounts

| Role | Username | Password | Purpose |
|---|---|---|---|
| **Operations Admin** | `admin` | `rescue2026` | Full command center, GDACS sync, triage |
| **Affected Person** | `citizen1` | `rescue2026` | Citizen emergency intake & tracking |
| **Hospital Facility** | `hospital_user` | `rescue2026` | Hospital bed & oxygen management |
| **Relief Donor** | `donor1` | `rescue2026` | Supply donations & relief need matching |

*(One-click demo login buttons are also provided directly on the login screen for instant evaluation).*
