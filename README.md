# ✈️ SkyStream - Flight Booking System

A comprehensive flight booking system with support for one-way and return trips, multiple packages, and seat selection.

---

## 🚀 Quick Start

### Setup & Run
```bash
# Navigate to backend
cd backend

# Seed database (440 flights, 10 days)
python3 seed_comprehensive.py

# Start application
python3 app.py
```

**Access**: http://localhost:5000

---

## 🔐 Login Credentials

| Role     | Username/Email              | Password     |
|----------|----------------------------|--------------|
| Admin    | hussain@skystream.com      | hussain9887  |
| Staff    | STF-1001 to STF-1008       | password123  |
| Customer | sarah.mitchell@example.com | customer123  |

---

## ✨ Key Features

### 1. **Flight Search**
- **One-Way Trips**: Search and book single direction flights
- **Return Trips**: Search and book round-trip flights with different dates
- 440 flights across 10 days
- 22 routes covering all major Pakistan cities

### 2. **Package Selection**
Three package tiers available:

| Package  | Price      | Features                          |
|----------|-----------|-----------------------------------|
| Basic    | Rs 19,000 | Auto-assigned seats               |
| Economy  | Rs 24,000 | Seat selection, meal preference   |
| Premium  | Rs 30,000 | Business class, seat selection    |

**Return Trip Pricing**: 2× package price (e.g., Premium = Rs 60,000)

### 3. **Seat Selection**

#### One-Way Trips
- Shows **1 seat map** (full width)
- Select seats for single flight
- Creates 1 booking, issues 1 ticket

#### Return Trips
- Shows **2 seat maps** (side-by-side)
- Outbound seat map (blue theme)
- Return seat map (amber theme)
- Select different seats for each flight
- Creates 2 bookings, issues 2 tickets

### 4. **Booking Management**
- View all bookings in "My Bookings"
- Download tickets as PDF
- Track booking status
- View passenger details

---

## 📊 Database

### Current Data
- **Flights**: 440 (10 days coverage)
- **Routes**: 22 bidirectional routes
- **Aircraft**: 8 planes with realistic capacities
- **Cities**: Karachi, Lahore, Islamabad, Peshawar, Multan, Quetta

### Sample Routes
- Karachi ↔ Lahore, Islamabad, Peshawar, Multan, Quetta
- Lahore ↔ Islamabad, Peshawar, Multan
- Islamabad ↔ Peshawar, Multan, Quetta
- And all reverse routes

---

## 🎯 How to Test

### Test One-Way Trip
1. Login as customer
2. Go to `/flights/search`
3. Select "One Way"
4. Search: Karachi → Lahore
5. Select flight → Choose package
6. **Verify**: Only 1 seat map shown (full width)
7. Select seat → Enter details → Complete booking

### Test Return Trip
1. Login as customer
2. Go to `/flights/search`
3. Select "Return"
4. Enter departure date (e.g., May 25)
5. Enter return date (e.g., May 27)
6. Search: Karachi → Peshawar
7. Select outbound flight
8. Select return flight
9. Choose package
10. **Verify**: 2 seat maps shown (side-by-side)
11. Select seats for both flights
12. Enter details → Complete booking
13. **Verify**: 2 tickets issued

---

## 📁 Project Structure

```
SkyStream/
├── backend/
│   ├── app.py                      # Flask application
│   ├── routes.py                   # Route handlers
│   ├── models.py                   # Database models
│   ├── forms.py                    # WTForms
│   ├── seed_comprehensive.py       # Database seeding
│   └── instance/
│       └── skystream.db            # SQLite database
├── templates/
│   ├── search.html                 # Flight search page
│   ├── packages.html               # Package selection
│   ├── passengers.html             # Seat selection
│   ├── checkout.html               # Payment & confirmation
│   └── my_bookings.html            # Booking history
└── static/
    ├── css/                        # Stylesheets
    └── js/                         # JavaScript files
```

---

## 🔧 Technical Details

### Frontend
- **Templates**: Jinja2 with Tailwind CSS
- **JavaScript**: Vanilla JS for seat selection
- **Responsive**: Mobile-first design

### Backend
- **Framework**: Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login with bcrypt
- **Forms**: WTForms with CSRF protection

### Key Routes
- `/flights/search` - Search flights
- `/flights/<id>/package` - Select package
- `/flights/<id>/passengers` - Seat selection
- `/flights/<id>/checkout` - Payment & booking
- `/my-bookings` - View bookings
- `/ticket/<id>` - View ticket

---

## ✅ Verification Status

**Last Verified**: April 24, 2026  
**Status**: ✅ All features working correctly

- ✅ One-way trips show 1 seat map
- ✅ Return trips show 2 seat maps
- ✅ All packages work correctly
- ✅ Database properly seeded
- ✅ Booking flow complete

See `FINAL_VERIFICATION_REPORT.md` for detailed test results.

---

## 🐛 Known Limitations

1. **No seat hold mechanism** - Seats not reserved during booking
2. **No partial booking** - Both flights must be available for return trips
3. **No seat map preview** - Full seat map only on passenger details page

---

## 📝 License

This project is for educational purposes.

---

## 🤝 Support

For issues or questions, refer to the documentation files:
- `FINAL_VERIFICATION_REPORT.md` - Detailed verification report
- `QUICK_START.md` - Quick reference guide
