# 🚀 SkyStream Quick Start Guide

## Setup & Run

### 1. Seed Database (10 Days of Flights)
```bash
cd backend
python seed_comprehensive.py
```

**Output**: 440 flights, 8 aircraft, 22 routes, 10 days coverage

### 2. Start Application
```bash
python app.py
```

**Access**: http://localhost:5000

## 🔐 Login Credentials

| Role     | Username/Email              | Password     |
|----------|----------------------------|--------------|
| Admin    | hussain@skystream.com      | hussain9887  |
| Staff    | STF-1001 to STF-1008       | password123  |
| Customer | sarah.mitchell@example.com | customer123  |

## 🎯 Test Return Trip Booking

### Step-by-Step
1. Go to **Search Flights**
2. Select **"Return"** trip type
3. Set:
   - Departure: **Karachi**
   - Arrival: **Peshawar**
   - Departure Date: **May 25, 2026**
   - Return Date: **May 27, 2026**
4. Click **"Search Flights"**
5. Select an **outbound flight** (Karachi → Peshawar)
6. Select a **return flight** (Peshawar → Karachi)
7. Click **"Choose Premium"** (Rs 30,000)
8. Enter passenger details
9. Proceed to checkout
10. **Total Price**: Rs 60,000 (30k × 2)
11. Select payment method
12. Confirm booking
13. **Result**: 2 tickets issued ✅

## 📋 Key Features to Test

### ✅ Package Selection (Direct Navigation)
- Click "Choose Basic/Economy/Premium"
- Should go **directly** to passenger details
- No "Continue" button needed

### ✅ Return Trips
- Shows **two flight lists**: Outbound + Return
- Creates **two bookings**
- Issues **two tickets**
- Price is **doubled** (e.g., Premium: Rs 60,000)

### ✅ Staff Deletion (Professional Prompt)
1. Login as admin
2. Go to Staff section
3. Click "Delete" on any staff
4. Type **"DELETE"** to confirm
5. Shows professional warning

### ✅ Payment Options
- Credit / Debit Card
- EasyPaisa
- JazzCash
- Bank Transfer

## 🗺️ Available Routes

All cities connect to each other:
- **Karachi** ↔ Lahore, Islamabad, Peshawar, Multan, Quetta
- **Lahore** ↔ Islamabad, Peshawar, Multan
- **Islamabad** ↔ Peshawar, Multan, Quetta

**Total**: 22 bidirectional routes, 440 flights over 10 days

## 💰 Package Pricing

| Package | One-Way  | Return   |
|---------|----------|----------|
| Basic   | Rs 19,000| Rs 38,000|
| Economy | Rs 24,000| Rs 48,000|
| Premium | Rs 30,000| Rs 60,000|

## 🧪 Run Tests

```bash
cd backend
python test_pages.py
```

## 📊 Check Database Status

Visit: http://localhost:5000/db-status

Shows:
- Total flights, planes, bookings
- Staff and customer counts
- Admin users

## 🎨 Admin Dashboard

**URL**: http://localhost:5000/admin/dashboard

**Features**:
- View all flights, staff, customers
- Add flights, staff, admins
- Assign staff to flights
- Delete staff (with confirmation)
- Real-time KPIs

## 🛫 Customer Booking Flow

1. **Search** → Select dates, cities, trip type
2. **Select Flight(s)** → Choose outbound (+ return if applicable)
3. **Choose Package** → Click Basic/Economy/Premium
4. **Passenger Details** → Names, seats, meals
5. **Checkout** → Payment method
6. **Confirmation** → Tickets issued

## 📱 Pages Available

| Page | URL | Access |
|------|-----|--------|
| Home | / | Public |
| Search Flights | /flights/search | Public |
| Login | /login | Public |
| Register | /register | Public |
| My Bookings | /my-bookings | Customer |
| Admin Dashboard | /admin/dashboard | Admin |
| Staff Dashboard | /staff/dashboard | Staff |

## 🔧 Troubleshooting

### Database Issues
```bash
cd backend
python seed_comprehensive.py  # Re-seed database
```

### Port Already in Use
```bash
# Change port in app.py or kill existing process
lsof -ti:5000 | xargs kill -9
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

## ✨ What's New

1. ✅ **10 days of flights** (440 total)
2. ✅ **Direct package selection** (no continue button)
3. ✅ **Return trip support** (2 bookings, 2 tickets)
4. ✅ **Professional staff delete** (type "DELETE" to confirm)
5. ✅ **Multiple payment gateways**
6. ✅ **Comprehensive route network**

## 🎉 Ready to Use!

All features implemented and tested. Start the app and explore!

**Need Help?** Check `IMPLEMENTATION_SUMMARY.md` for detailed documentation.
