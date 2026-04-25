# Admin Dashboard - Flight Index-Based Numbering

## ✅ Changes Made

### 1. Flights Table
- **Before**: Showed `SS-{database_id}` (e.g., SS-1, SS-15, SS-23)
- **After**: Shows `FL-{index}` (e.g., FL-1, FL-2, FL-3...)

### 2. Delete Confirmation Modal
- **Before**: "Flight #15 (Karachi → Lahore)"
- **After**: "Flight FL-2 (Karachi → Lahore)"

### 3. Assign Staff Dropdown
- **Before**: "#15 — Karachi → Lahore"
- **After**: "FL-2 — Karachi → Lahore"

## 📝 Implementation Details

### Flight Table Display
```jinja
{% for fl in flights %}
  <span class="font-mono">FL-{{ loop.index }}</span>
  <!-- loop.index gives 1, 2, 3... instead of database ID -->
{% endfor %}
```

### JavaScript Function Updated
```javascript
function confirmDeleteFlight(flightId, flightIndex, label) {
  // flightId: database ID (for deletion)
  // flightIndex: display index (for user-friendly label)
  document.getElementById('delete-flight-label').textContent = `Flight FL-${flightIndex} (${label})`;
  document.getElementById('delete-flight-form').action = `/admin/flights/${flightId}/delete`;
}
```

## 🎯 Benefits

1. **User-Friendly**: Sequential numbering (1, 2, 3...) is easier to reference
2. **Consistent**: All flights numbered in order of appearance
3. **Professional**: Standard airline flight numbering convention
4. **Maintains Functionality**: Database IDs still used for backend operations

## 📊 Display Examples

| Section | Before | After |
|---------|--------|-------|
| Flight Table | SS-1, SS-15, SS-23 | FL-1, FL-2, FL-3 |
| Delete Modal | Flight #15 | Flight FL-2 |
| Staff Assignment | #15 — Route | FL-2 — Route |

## ⚠️ Note

Fleet cards still show database IDs (FL-{id}) for recent flights since they reference historical data across different planes. This is intentional to maintain data integrity.

---

**Status**: ✅ COMPLETE - Flights now display with index-based numbering (FL-1, FL-2, FL-3...)
