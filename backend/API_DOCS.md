# MG Holidays Hotel Management API Documentation v2.0

## Base URL
```
http://localhost:8000
```

## Installation & Setup

1. **Update Database Schema First:**
```sql
-- Add status 5 as cancelled to books table
ALTER TABLE books DROP CONSTRAINT books_status_check;
ALTER TABLE books ADD CONSTRAINT books_status_check CHECK (status IN (1, 2, 3, 4, 5));
COMMENT ON COLUMN books.status IS 'Booking status: 1=Pending, 2=Confirmed, 3=Checked-in, 4=Completed, 5=Cancelled';
```

2. **Install Dependencies:**
```bash
pip install fastapi uvicorn asyncpg pydantic[email]
```

3. **Run Application:**
```bash
python main.py
```

4. **Access Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Status Reference

### Booking Status:
- `1`: Pending
- `2`: Confirmed  
- `3`: Checked-in
- `4`: Completed/Checked-out
- `5`: Cancelled

### Payment Status:
- `1`: Pending
- `2`: Paid
- `3`: Refunded

### User Types:
- `1`: Customer
- `2`: Admin

## API Endpoints

### 1. Create User
**POST** `/api/createuser`

Creates a new customer account.

**Request Body:**
```json
{
    "username": "john_doe",
    "emailid": "john@example.com",
    "password": "mypassword123"
}
```

**Response:**
```json
{
    "success": true,
    "message": "User created successfully",
    "user_id": 1,
    "username": "john_doe"
}
```

**Testing:**
```bash
curl -X POST "http://localhost:8000/api/createuser" \
-H "Content-Type: application/json" \
-d '{
    "username": "testuser1",
    "emailid": "test1@example.com",
    "password": "password123"
}'
```

---

### 2. User Login
**POST** `/api/login`

Authenticates user with email and password.

**Request Body:**
```json
{
    "emailid": "john@example.com",
    "password": "mypassword123"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Login successful",
    "user_id": 1,
    "username": "john_doe",
    "user_type": 1
}
```

**Testing:**
```bash
curl -X POST "http://localhost:8000/api/login" \
-H "Content-Type: application/json" \
-d '{
    "emailid": "test1@example.com",
    "password": "password123"
}'
```

---

### 3. Get All Rooms
**GET** `/api/getallrooms`

Returns all rooms with their facilities.

**Response:**
```json
[
    {
        "id": 1,
        "type": "Standard",
        "no_of_available_rooms": 10,
        "max_capacity_per_room": 2,
        "room_img_url": "https://example.com/standard.jpg",
        "price_per_night": 99.99,
        "facilities": ["Wi-Fi", "Air Conditioning", "Television"]
    }
]
```

**Testing:**
```bash
curl -X GET "http://localhost:8000/api/getallrooms"
```

---

### 4. Add Feedback
**POST** `/api/addfeedback`

Adds user feedback with optional rating.

**Request Body:**
```json
{
    "userid": 1,
    "feedback": "Great stay! The room was very clean.",
    "rating": 5
}
```

**Response:**
```json
{
    "success": true,
    "message": "Feedback added successfully",
    "feedback_id": 1
}
```

**Testing:**
```bash
curl -X POST "http://localhost:8000/api/addfeedback" \
-H "Content-Type: application/json" \
-d '{
    "userid": 1,
    "feedback": "Excellent service and comfortable rooms!",
    "rating": 5
}'
```

---

### 5. Get All Feedbacks
**GET** `/api/getallfeedbacks`

Returns all user feedbacks with usernames.

**Response:**
```json
[
    {
        "id": 1,
        "feedback": "Great stay! The room was very clean.",
        "username": "john_doe",
        "rating": 5,
        "created_at": "2024-01-15T10:30:00"
    }
]
```

**Testing:**
```bash
curl -X GET "http://localhost:8000/api/getallfeedbacks"
```

---

### 6. Get My Bookings
**GET** `/api/getmybookings/{user_id}`

Returns bookings for a specific user.

**Response:**
```json
[
    {
        "id": 1,
        "user_id": 1,
        "username": "john_doe",
        "checkin_date": "2024-01-15",
        "checkout_date": "2024-01-18",
        "room_id": 1,
        "room_type": "Standard",
        "no_of_rooms": 1,
        "no_of_people": 2,
        "checkin_time": "15:00:00",
        "checkout_time": "11:00:00",
        "status": 2,
        "payment_status": 2,
        "total_amount": 299.97,
        "booking_date": "2024-01-10T14:30:00"
    }
]
```

**Testing:**
```bash
curl -X GET "http://localhost:8000/api/getmybookings/1"
```

---

### 7. Get All Bookings
**GET** `/api/getallbookings`

Returns all bookings (admin function).

**Response:** Same structure as "Get My Bookings" but for all users.

**Testing:**
```bash
curl -X GET "http://localhost:8000/api/getallbookings"
```

---

### 8. Get All Room Types
**GET** `/api/getallroomtypes`

Returns basic room type information without facilities.

**Response:**
```json
[
    {
        "id": 1,
        "type": "Standard",
        "no_of_available_rooms": 10,
        "max_capacity_per_room": 2,
        "room_img_url": "https://example.com/standard.jpg",
        "price_per_night": 99.99
    }
]
```

**Testing:**
```bash
curl -X GET "http://localhost:8000/api/getallroomtypes"
```

---

### 9. Create Room Type
**POST** `/api/createroomtype`

Creates a new room type with facilities.

**Request Body:**
```json
{
    "room_type_name": "Luxury Suite",
    "no_of_available_rooms": 5,
    "max_capacity_per_room": 4,
    "price_per_night": 399.99,
    "room_image_url": "https://example.com/luxury-suite.jpg",
    "facilities": [
        "Wi-Fi",
        "Air Conditioning",
        "Television",
        "Mini Bar",
        "Balcony",
        "Living Room",
        "Kitchenette"
    ]
}
```

**Response:**
```json
{
    "success": true,
    "message": "Room type created successfully",
    "room_id": 5,
    "room_type": "Luxury Suite",
    "facilities_count": 7
}
```

**Testing:**
```bash
curl -X POST "http://localhost:8000/api/createroomtype" \
-H "Content-Type: application/json" \
-d '{
    "room_type_name": "Business Suite",
    "no_of_available_rooms": 3,
    "max_capacity_per_room": 2,
    "price_per_night": 249.99,
    "room_image_url": "https://example.com/business-suite.jpg",
    "facilities": ["Wi-Fi", "Air Conditioning", "Television", "Work Desk", "Coffee Machine", "Safe"]
}'
```

---

### 10. Create Booking
**POST** `/api/createbooking`

Creates a new booking.

**Request Body:**
```json
{
    "user_id": 1,
    "checkin_date": "2024-02-15",
    "checkout_date": "2024-02-18",
    "room_id": 1,
    "no_of_rooms": 1,
    "no_of_people": 2,
    "checkin_time": "15:00:00",
    "checkout_time": "11:00:00"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Booking created successfully",
    "booking_id": 1,
    "total_amount": 299.97
}
```

**Testing:**
```bash
curl -X POST "http://localhost:8000/api/createbooking" \
-H "Content-Type: application/json" \
-d '{
    "user_id": 1,
    "checkin_date": "2024-03-01",
    "checkout_date": "2024-03-05",
    "room_id": 1,
    "no_of_rooms": 2,
    "no_of_people": 4,
    "checkin_time": "14:00:00",
    "checkout_time": "12:00:00"
}'
```

---

## NEW ENDPOINTS (v2.0)

### 11. Update Booking
**PUT** `/api/updatebooking/{booking_id}`

Updates booking details by ID. Only provided fields are updated.

**Request Body:** (All fields are optional)
```json
{
    "checkin_date": "2024-02-16",
    "checkout_date": "2024-02-19",
    "room_id": 2,
    "no_of_rooms": 2,
    "no_of_people": 3,
    "checkin_time": "16:00:00",
    "checkout_time": "10:00:00"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Booking updated successfully",
    "booking_id": 1
}
```

**Testing:**
```bash
curl -X PUT "http://localhost:8000/api/updatebooking/1" \
-H "Content-Type: application/json" \
-d '{
    "checkin_date": "2024-04-01",
    "checkout_date": "2024-04-05",
    "no_of_people": 3
}'
```

**Notes:**
- Cannot update cancelled bookings (status 5)
- Total amount is automatically recalculated if dates, room, or number of rooms change
- Validates that new room exists if room_id is provided

---

### 12. Cancel Booking
**DELETE** `/api/cancelbooking/{booking_id}`

Cancels a booking by setting status to 5 (Cancelled).

**Response:**
```json
{
    "success": true,
    "message": "Booking cancelled successfully",
    "booking_id": 1,
    "refund_status": "Refunded"
}
```

**Testing:**
```bash
curl -X DELETE "http://localhost:8000/api/cancelbooking/1"
```

**Notes:**
- Cannot cancel already cancelled bookings
- Cannot cancel completed bookings (status 4)
- Automatically sets payment status to "Refunded" (3) if payment was already made
- Refund status in response indicates if a refund was processed

---

### 13. Update Booking Status
**PUT** `/api/updatebookingstatus/{booking_id}`

Updates only the booking status.

**Request Body:**
```json
{
    "status": 2
}
```

**Response:**
```json
{
    "success": true,
    "message": "Booking status updated to Confirmed",
    "booking_id": 1,
    "old_status": "Pending",
    "new_status": "Confirmed"
}
```

**Testing:**
```bash
curl -X PUT "http://localhost:8000/api/updatebookingstatus/1" \
-H "Content-Type: application/json" \
-d '{"status": 3}'
```

**Status Transition Rules:**
- Cannot change status of cancelled bookings (status 5)
- Cannot change status of completed bookings (status 4)
- Valid status values: 1-5

---

### 14. Update Room Type
**PUT** `/api/updateroomtype/{room_id}`

Updates room type details and facilities. Only provided fields are updated.

**Request Body:** (All fields are optional)
```json
{
    "room_type_name": "Premium Suite",
    "no_of_available_rooms": 8,
    "max_capacity_per_room": 3,
    "price_per_night": 199.99,
    "room_image_url": "https://example.com/premium-suite.jpg",
    "facilities": [
        "Wi-Fi",
        "Air Conditioning",
        "Television",
        "Mini Bar",
        "Room Service"
    ]
}
```

**Response:**
```json
{
    "success": true,
    "message": "Room type updated successfully",
    "room_id": 1,
    "updated_fields": 3,
    "facilities_updated": true
}
```

**Testing:**
```bash
curl -X PUT "http://localhost:8000/api/updateroomtype/1" \
-H "Content-Type: application/json" \
-d '{
    "price_per_night": 120.00,
    "no_of_available_rooms": 15,
    "facilities": ["Wi-Fi", "AC", "TV", "Mini Fridge"]
}'
```

**Notes:**
- If facilities are provided, all existing facilities are replaced
- Room type name, availability, capacity, price, and image URL can be updated independently
- Response indicates how many fields were updated and if facilities were modified

---

### 15. Status Reference
**GET** `/api/status-reference`

Returns reference for all status codes used in the system.

**Response:**
```json
{
    "booking_status": {
        "1": "Pending",
        "2": "Confirmed", 
        "3": "Checked-in",
        "4": "Completed",
        "5": "Cancelled"
    },
    "payment_status": {
        "1": "Pending",
        "2": "Paid",
        "3": "Refunded"
    },
    "user_types": {
        "1": "Customer",
        "2": "Admin"
    }
}
```

**Testing:**
```bash
curl -X GET "http://localhost:8000/api/status-reference"
```

---

## Complete Testing Sequence (v2.0)

Run these commands in sequence to test the complete system:

```bash
# 1. Create a test user
curl -X POST "http://localhost:8000/api/createuser" \
-H "Content-Type: application/json" \
-d '{"username": "testuser2", "emailid": "test2@example.com", "password": "password123"}'

# 2. Login with the user
curl -X POST "http://localhost:8000/api/login" \
-H "Content-Type: application/json" \
-d '{"emailid": "test2@example.com", "password": "password123"}'

# 3. Create a room type
curl -X POST "http://localhost:8000/api/createroomtype" \
-H "Content-Type: application/json" \
-d '{
    "room_type_name": "Test Suite",
    "no_of_available_rooms": 5,
    "max_capacity_per_room": 3,
    "price_per_night": 180.00,
    "room_image_url": "https://example.com/test-suite.jpg",
    "facilities": ["Wi-Fi", "AC", "TV", "Mini Bar"]
}'

# 4. Get all rooms
curl -X GET "http://localhost:8000/api/getallrooms"

# 5. Create a booking (use actual user_id and room_id from previous responses)
curl -X POST "http://localhost:8000/api/createbooking" \
-H "Content-Type: application/json" \
-d '{
    "user_id": 1,
    "checkin_date": "2024-12-15",
    "checkout_date": "2024-12-18",
    "room_id": 1,
    "no_of_rooms": 1,
    "no_of_people": 2
}'

# 6. Update the booking
curl -X PUT "http://localhost:8000/api/updatebooking/1" \
-H "Content-Type: application/json" \
-d '{
    "no_of_people": 3,
    "checkout_date": "2024-12-20"
}'

# 7. Update booking status to confirmed
curl -X PUT "http://localhost:8000/api/updatebookingstatus/1" \
-H "Content-Type: application/json" \
-d '{"status": 2}'

# 8. Add feedback
curl -X POST "http://localhost:8000/api/addfeedback" \
-H "Content-Type: application/json" \
-d '{"userid": 1, "feedback": "Great experience with the updated booking system!", "rating": 5}'

# 9. Get user bookings
curl -X GET "http://localhost:8000/api/getmybookings/1"

# 10. Update room type
curl -X PUT "http://localhost:8000/api/updateroomtype/1" \
-H "Content-Type: application/json" \
-d '{
    "price_per_night": 200.00,
    "facilities": ["Wi-Fi", "AC", "TV", "Mini Bar", "Balcony", "Room Service"]
}'

# 11. Cancel booking (optional - test cancellation)
curl -X DELETE "http://localhost:8000/api/cancelbooking/1"

# 12. Get status reference
curl -X GET "http://localhost:8000/api/status-reference"

# 13. Get all bookings (admin view)
curl -X GET "http://localhost:8000/api/getallbookings"

# 14. Get all feedbacks
curl -X GET "http://localhost:8000/api/getallfeedbacks"

# 15. Health check
curl -X GET "http://localhost:8000/health"
```

---

## Error Handling

All endpoints return error responses in this format:

```json
{
    "detail": "Error message description"
}
```

**Common HTTP Status Codes:**
- `400`: Bad Request (validation errors, business logic violations)
- `404`: Not Found (user, room, booking not found)
- `500`: Internal Server Error (database issues)

**Business Logic Errors:**
- Cannot update cancelled bookings
- Cannot cancel completed bookings
- Cannot change status of cancelled/completed bookings
- Room availability validation
- Date validation (checkout must be after checkin)

---

## Database Schema Requirements

Before running the API, ensure your database has the updated schema:

```sql
-- Update books table constraint for status 5
ALTER TABLE books DROP CONSTRAINT books_status_check;
ALTER TABLE books ADD CONSTRAINT books_status_check CHECK (status IN (1, 2, 3, 4, 5));
COMMENT ON COLUMN books.status IS 'Booking status: 1=Pending, 2=Confirmed, 3=Checked-in, 4=Completed, 5=Cancelled';
```

This API provides comprehensive hotel management functionality with proper validation, error handling, and business logic implementation.