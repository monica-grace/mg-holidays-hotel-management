from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import asyncpg
import hashlib
import asyncio
from datetime import datetime, date, time
import os
from contextlib import asynccontextmanager

# Load variables from a local .env file if present (no-op if python-dotenv isn't installed)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Database connection string — read from environment (see .env.example)
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Copy .env.example to .env and set your PostgreSQL connection string."
    )

# Global connection pool
pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
    print("Database connection pool created")
    yield
    # Shutdown
    await pool.close()
    print("Database connection pool closed")

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="MG Holidays Hotel Management API",
    description="Hotel Management System API for MG Holidays",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    emailid: EmailStr
    password: str

class UserLogin(BaseModel):
    emailid: EmailStr
    password: str

class FeedbackCreate(BaseModel):
    userid: int
    feedback: str
    rating: Optional[int] = None

class RoomTypeCreate(BaseModel):
    room_type_name: str
    no_of_available_rooms: int
    max_capacity_per_room: int
    price_per_night: float
    room_image_url: Optional[str] = None
    facilities: List[str]

class RoomTypeUpdate(BaseModel):
    room_type_name: Optional[str] = None
    no_of_available_rooms: Optional[int] = None
    max_capacity_per_room: Optional[int] = None
    price_per_night: Optional[float] = None
    room_image_url: Optional[str] = None
    facilities: Optional[List[str]] = None

class BookingCreate(BaseModel):
    user_id: int
    checkin_date: date
    checkout_date: date
    room_id: int
    no_of_rooms: int
    no_of_people: int
    checkin_time: Optional[time] = None
    checkout_time: Optional[time] = None

class BookingUpdate(BaseModel):
    checkin_date: Optional[date] = None
    checkout_date: Optional[date] = None
    room_id: Optional[int] = None
    no_of_rooms: Optional[int] = None
    no_of_people: Optional[int] = None
    checkin_time: Optional[time] = None
    checkout_time: Optional[time] = None

class BookingStatusUpdate(BaseModel):
    status: int  # 1=Pending, 2=Confirmed, 3=Checked-in, 4=Completed, 5=Cancelled

# Response Models
class UserResponse(BaseModel):
    id: int
    username: str
    emailid: str
    type: int
    created_at: datetime

class RoomResponse(BaseModel):
    id: int
    type: str
    no_of_available_rooms: int
    max_capacity_per_room: int
    room_img_url: Optional[str]
    price_per_night: float
    facilities: List[str]

class FeedbackResponse(BaseModel):
    id: int
    feedback: str
    username: str
    rating: Optional[int]
    created_at: datetime

class BookingResponse(BaseModel):
    id: int
    user_id: int
    username: str
    checkin_date: date
    checkout_date: date
    room_id: int
    room_type: str
    no_of_rooms: int
    no_of_people: int
    checkin_time: Optional[time]
    checkout_time: Optional[time]
    status: int
    payment_status: int
    total_amount: Optional[float]
    booking_date: datetime

# Helper functions
def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

async def get_db():
    """Get database connection from pool"""
    async with pool.acquire() as connection:
        yield connection

def get_status_name(status: int) -> str:
    """Get status name from status code"""
    status_map = {
        1: "Pending",
        2: "Confirmed", 
        3: "Checked-in",
        4: "Completed",
        5: "Cancelled"
    }
    return status_map.get(status, "Unknown")

def get_payment_status_name(payment_status: int) -> str:
    """Get payment status name from status code"""
    payment_map = {
        1: "Pending",
        2: "Paid",
        3: "Refunded"
    }
    return payment_map.get(payment_status, "Unknown")

# API Endpoints

@app.get("/")
async def root():
    return {
        "message": "MG Holidays Hotel Management API", 
        "version": "2.0.0",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health"
        }
    }

@app.post("/api/createuser", response_model=Dict[str, Any])
async def create_user(user: UserCreate, db: asyncpg.Connection = Depends(get_db)):
    """
    Create a new user
    - Validates if username already exists
    - Creates user with hashed password
    - Returns success message with user details
    """
    try:
        # Check if username already exists
        existing_user = await db.fetchrow(
            "SELECT id FROM users WHERE username = $1 OR emailid = $2",
            user.username, user.emailid
        )
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Hash password
        hashed_password = user.password
        
        # Insert new user (default type = 1 for customer)
        user_id = await db.fetchval(
            """INSERT INTO users (username, emailid, password, type) 
               VALUES ($1, $2, $3, 1) 
               RETURNING id""",
            user.username, user.emailid, hashed_password
        )
        
        return {
            "success": True,
            "message": "User created successfully",
            "user_id": user_id,
            "username": user.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/login", response_model=Dict[str, Any])
async def login(credentials: UserLogin, db: asyncpg.Connection = Depends(get_db)):
    """
    User login
    - Validates email and password
    - Returns success status with user details
    """
    try:
        hashed_password = credentials.password
        
        user = await db.fetchrow(
            "SELECT id, username, type FROM users WHERE emailid = $1 AND password = $2",
            credentials.emailid, hashed_password
        )
        
        if not user:
            return {"success": False, "message": "Invalid email or password"}
        
        return {
            "success": True,
            "message": "Login successful",
            "user_id": user['id'],
            "username": user['username'],
            "user_type": user['type']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/getallrooms", response_model=List[RoomResponse])
async def get_all_rooms(db: asyncpg.Connection = Depends(get_db)):
    """
    Get all rooms with their facilities
    - Returns list of rooms with facilities as list of strings
    """
    try:
        rooms = await db.fetch("""
            SELECT r.id, r.type, r.no_of_available_rooms, r.max_capacity_per_room, 
                   r.room_img_url, r.price_per_night
            FROM rooms r
            ORDER BY r.id
        """)
        
        result = []
        for room in rooms:
            # Get facilities for this room
            facilities = await db.fetch(
                "SELECT facility_name FROM facility_of_room WHERE room_id = $1",
                room['id']
            )
            
            result.append({
                "id": room['id'],
                "type": room['type'],
                "no_of_available_rooms": room['no_of_available_rooms'],
                "max_capacity_per_room": room['max_capacity_per_room'],
                "room_img_url": room['room_img_url'],
                "price_per_night": float(room['price_per_night']),
                "facilities": [f['facility_name'] for f in facilities]
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/addfeedback", response_model=Dict[str, Any])
async def add_feedback(feedback_data: FeedbackCreate, db: asyncpg.Connection = Depends(get_db)):
    """
    Add user feedback
    - Validates if user exists
    - Adds feedback to database
    """
    try:
        # Check if user exists
        user_exists = await db.fetchval(
            "SELECT id FROM users WHERE id = $1",
            feedback_data.userid
        )
        
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Insert feedback
        feedback_id = await db.fetchval(
            """INSERT INTO feedback (feedback, user_id) 
               VALUES ($1, $2) 
               RETURNING id""",
            feedback_data.feedback, feedback_data.userid,
        )
        
        return {
            "success": True,
            "message": "Feedback added successfully",
            "feedback_id": feedback_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/getallfeedbacks", response_model=List[FeedbackResponse])
async def get_all_feedbacks(db: asyncpg.Connection = Depends(get_db)):
    """
    Get all feedbacks with username
    - Returns list of feedbacks with user details
    """
    try:
        feedbacks = await db.fetch("""
            SELECT f.id, f.feedback, f.rating, f.created_at, u.username
            FROM feedback f
            JOIN users u ON f.user_id = u.id
            ORDER BY f.created_at DESC
        """)
        
        return [
            {
                "id": f['id'],
                "feedback": f['feedback'],
                "username": f['username'],
                "rating": f['rating'],
                "created_at": f['created_at']
            }
            for f in feedbacks
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/getmybookings/{user_id}", response_model=List[BookingResponse])
async def get_my_bookings(user_id: int, db: asyncpg.Connection = Depends(get_db)):
    """
    Get bookings for a specific user
    - Returns user's booking history with room details
    """
    try:
        bookings = await db.fetch("""
            SELECT b.*, u.username, r.type as room_type
            FROM books b
            JOIN users u ON b.user_id = u.id
            JOIN rooms r ON b.room_id = r.id
            WHERE b.user_id = $1
            ORDER BY b.booking_date DESC
        """, user_id)
        
        return [
            {
                "id": b['id'],
                "user_id": b['user_id'],
                "username": b['username'],
                "checkin_date": b['checkin_date'],
                "checkout_date": b['checkout_date'],
                "room_id": b['room_id'],
                "room_type": b['room_type'],
                "no_of_rooms": b['no_of_rooms'],
                "no_of_people": b['no_of_people'],
                "checkin_time": b['checkin_time'],
                "checkout_time": b['checkout_time'],
                "status": b['status'],
                "payment_status": b['payment_status'],
                "total_amount": float(b['total_amount']) if b['total_amount'] else None,
                "booking_date": b['booking_date']
            }
            for b in bookings
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/getallbookings", response_model=List[BookingResponse])
async def get_all_bookings(db: asyncpg.Connection = Depends(get_db)):
    """
    Get all bookings (admin function)
    - Returns all bookings with user and room details
    """
    try:
        bookings = await db.fetch("""
            SELECT b.*, u.username, r.type as room_type
            FROM books b
            JOIN users u ON b.user_id = u.id
            JOIN rooms r ON b.room_id = r.id
            ORDER BY b.booking_date DESC
        """)
        
        return [
            {
                "id": b['id'],
                "user_id": b['user_id'],
                "username": b['username'],
                "checkin_date": b['checkin_date'],
                "checkout_date": b['checkout_date'],
                "room_id": b['room_id'],
                "room_type": b['room_type'],
                "no_of_rooms": b['no_of_rooms'],
                "no_of_people": b['no_of_people'],
                "checkin_time": b['checkin_time'],
                "checkout_time": b['checkout_time'],
                "status": b['status'],
                "payment_status": b['payment_status'],
                "total_amount": float(b['total_amount']) if b['total_amount'] else None,
                "booking_date": b['booking_date']
            }
            for b in bookings
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/getallroomtypes", response_model=List[Dict[str, Any]])
async def get_all_room_types(db: asyncpg.Connection = Depends(get_db)):
    """
    Get all room types (simple list)
    - Returns basic room type information
    """
    try:
        rooms = await db.fetch("""
            SELECT id, type, no_of_available_rooms, max_capacity_per_room, 
                   room_img_url, price_per_night
            FROM rooms
            ORDER BY price_per_night ASC
        """)
        
        return [
            {
                "id": r['id'],
                "type": r['type'],
                "no_of_available_rooms": r['no_of_available_rooms'],
                "max_capacity_per_room": r['max_capacity_per_room'],
                "room_img_url": r['room_img_url'],
                "price_per_night": float(r['price_per_night'])
            }
            for r in rooms
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/createroomtype", response_model=Dict[str, Any])
async def create_room_type(room_data: RoomTypeCreate, db: asyncpg.Connection = Depends(get_db)):
    """
    Create a new room type with facilities
    - Creates room type and associated facilities
    - Returns success message with room ID
    """
    try:
        async with db.transaction():
            # Insert room
            room_id = await db.fetchval("""
                INSERT INTO rooms (type, no_of_available_rooms, max_capacity_per_room, 
                                 room_img_url, price_per_night)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, 
            room_data.room_type_name,
            room_data.no_of_available_rooms,
            room_data.max_capacity_per_room,
            room_data.room_image_url,
            room_data.price_per_night
            )
            
            # Insert facilities
            for facility in room_data.facilities:
                await db.execute("""
                    INSERT INTO facility_of_room (room_id, facility_name)
                    VALUES ($1, $2)
                """, room_id, facility)
            
        return {
            "success": True,
            "message": "Room type created successfully",
            "room_id": room_id,
            "room_type": room_data.room_type_name,
            "facilities_count": len(room_data.facilities)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/createbooking", response_model=Dict[str, Any])
async def create_booking(booking_data: BookingCreate, db: asyncpg.Connection = Depends(get_db)):
    """
    Create a new booking
    - Validates room availability
    - Creates booking record
    """
    try:
        # Check if room exists and has availability
        room = await db.fetchrow(
            "SELECT * FROM rooms WHERE id = $1",
            booking_data.room_id
        )
        
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        if room['no_of_available_rooms'] < booking_data.no_of_rooms:
            raise HTTPException(status_code=400, detail="Not enough rooms available")
        
        # Calculate total amount
        days = (booking_data.checkout_date - booking_data.checkin_date).days
        total_amount = float(room['price_per_night']) * booking_data.no_of_rooms * days
        
        # Create booking
        booking_id = await db.fetchval("""
            INSERT INTO books (user_id, checkin_date, checkout_date, room_id, 
                             no_of_rooms, no_of_people, checkin_time, checkout_time, 
                             status, payment_status, total_amount)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 2, 1, $9)
            RETURNING id
        """, 
        booking_data.user_id,
        booking_data.checkin_date,
        booking_data.checkout_date,
        booking_data.room_id,
        booking_data.no_of_rooms,
        booking_data.no_of_people,
        booking_data.checkin_time,
        booking_data.checkout_time,
        total_amount
        )
        
        return {
            "success": True,
            "message": "Booking created successfully",
            "booking_id": booking_id,
            "total_amount": total_amount
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# NEW ENDPOINTS

@app.put("/api/updatebooking/{booking_id}", response_model=Dict[str, Any])
async def update_booking(booking_id: int, booking_data: BookingUpdate, db: asyncpg.Connection = Depends(get_db)):
    """
    Update booking details by ID
    - Updates only provided fields
    - Recalculates total amount if dates or room changes
    """
    try:
        # Check if booking exists
        existing_booking = await db.fetchrow(
            "SELECT * FROM books WHERE id = $1",
            booking_id
        )
        
        if not existing_booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Check if booking is cancelled
        if existing_booking['status'] == 5:
            raise HTTPException(status_code=400, detail="Cannot update cancelled booking")
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        param_count = 1
        
        if booking_data.checkin_date is not None:
            update_fields.append(f"checkin_date = ${param_count}")
            update_values.append(booking_data.checkin_date)
            param_count += 1
            
        if booking_data.checkout_date is not None:
            update_fields.append(f"checkout_date = ${param_count}")
            update_values.append(booking_data.checkout_date)
            param_count += 1
            
        if booking_data.room_id is not None:
            # Check if new room exists
            room_exists = await db.fetchval("SELECT id FROM rooms WHERE id = $1", booking_data.room_id)
            if not room_exists:
                raise HTTPException(status_code=404, detail="Room not found")
            update_fields.append(f"room_id = ${param_count}")
            update_values.append(booking_data.room_id)
            param_count += 1
            
        if booking_data.no_of_rooms is not None:
            update_fields.append(f"no_of_rooms = ${param_count}")
            update_values.append(booking_data.no_of_rooms)
            param_count += 1
            
        if booking_data.no_of_people is not None:
            update_fields.append(f"no_of_people = ${param_count}")
            update_values.append(booking_data.no_of_people)
            param_count += 1
            
        if booking_data.checkin_time is not None:
            update_fields.append(f"checkin_time = ${param_count}")
            update_values.append(booking_data.checkin_time)
            param_count += 1
            
        if booking_data.checkout_time is not None:
            update_fields.append(f"checkout_time = ${param_count}")
            update_values.append(booking_data.checkout_time)
            param_count += 1
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Add updated_at field
        update_fields.append(f"updated_at = ${param_count}")
        update_values.append(datetime.now())
        param_count += 1
        
        # Add booking_id for WHERE clause
        update_values.append(booking_id)
        
        # Execute update
        query = f"""
            UPDATE books 
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING *
        """
        
        updated_booking = await db.fetchrow(query, *update_values)
        
        # Recalculate total amount if dates or room changed
        if booking_data.checkin_date or booking_data.checkout_date or booking_data.room_id or booking_data.no_of_rooms:
            room_price = await db.fetchval(
                "SELECT price_per_night FROM rooms WHERE id = $1",
                updated_booking['room_id']
            )
            days = (updated_booking['checkout_date'] - updated_booking['checkin_date']).days
            new_total = float(room_price) * updated_booking['no_of_rooms'] * days
            
            await db.execute(
                "UPDATE books SET total_amount = $1 WHERE id = $2",
                new_total, booking_id
            )
        
        return {
            "success": True,
            "message": "Booking updated successfully",
            "booking_id": booking_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/api/cancelbooking/{booking_id}", response_model=Dict[str, Any])
async def cancel_booking(booking_id: int, db: asyncpg.Connection = Depends(get_db)):
    """
    Cancel booking by ID
    - Sets status to 5 (Cancelled)
    - Updates payment status to 3 (Refunded) if already paid
    """
    try:
        # Check if booking exists
        print(booking_id)
        booking = await db.fetchrow(
            "SELECT * FROM books WHERE id = $1",
            booking_id
        )
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        if booking['status'] == 5:
            raise HTTPException(status_code=400, detail="Booking is already cancelled")
        
        if booking['status'] == 4:
            raise HTTPException(status_code=400, detail="Cannot cancel completed booking")
        
        # Update booking status to cancelled (5)
        # If payment was made (status 2), set to refunded (3)
        new_payment_status = 3 if booking['payment_status'] == 2 else booking['payment_status']
        
        await db.execute("""
            UPDATE books 
            SET status = 5, payment_status = $1, updated_at = $2
            WHERE id = $3
        """, new_payment_status, datetime.now(), booking_id)
        
        return {
            "success": True,
            "message": "Booking cancelled successfully",
            "booking_id": booking_id,
            "refund_status": "Refunded" if new_payment_status == 3 else "No payment to refund"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/api/updatebookingstatus/{booking_id}", response_model=Dict[str, Any])
async def update_booking_status(booking_id: int, status_data: BookingStatusUpdate, db: asyncpg.Connection = Depends(get_db)):
    """
    Update booking status by ID
    - Updates booking status (1-5)
    - Validates status transitions
    """
    try:
        # Validate status
        if status_data.status not in [1, 2, 3, 4, 5]:
            raise HTTPException(status_code=400, detail="Invalid status. Must be 1-5")
        
        # Check if booking exists
        booking = await db.fetchrow(
            "SELECT * FROM books WHERE id = $1",
            booking_id
        )
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        current_status = booking['status']
        new_status = status_data.status
        
        # Validate status transitions
        if current_status == 5:  # Cancelled
            raise HTTPException(status_code=400, detail="Cannot change status of cancelled booking")
        
        if current_status == 4 and new_status != 4:  # Completed
            raise HTTPException(status_code=400, detail="Cannot change status of completed booking")
        
        # Update status
        await db.execute("""
            UPDATE books 
            SET status = $1, updated_at = $2
            WHERE id = $3
        """, new_status, datetime.now(), booking_id)
        
        return {
            "success": True,
            "message": f"Booking status updated to {get_status_name(new_status)}",
            "booking_id": booking_id,
            "old_status": get_status_name(current_status),
            "new_status": get_status_name(new_status)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/api/updateroomtype/{room_id}", response_model=Dict[str, Any])
async def update_room_type(room_id: int, room_data: RoomTypeUpdate, db: asyncpg.Connection = Depends(get_db)):
    """
    Update room type by ID
    - Updates room details and facilities
    - Only updates provided fields
    """
    try:
        # Check if room exists
        existing_room = await db.fetchrow(
            "SELECT * FROM rooms WHERE id = $1",
            room_id
        )
        
        if not existing_room:
            raise HTTPException(status_code=404, detail="Room type not found")
        
        async with db.transaction():
            # Build update query for rooms table
            update_fields = []
            update_values = []
            param_count = 1
            
            if room_data.room_type_name is not None:
                update_fields.append(f"type = ${param_count}")
                update_values.append(room_data.room_type_name)
                param_count += 1
                
            if room_data.no_of_available_rooms is not None:
                update_fields.append(f"no_of_available_rooms = ${param_count}")
                update_values.append(room_data.no_of_available_rooms)
                param_count += 1
                
            if room_data.max_capacity_per_room is not None:
                update_fields.append(f"max_capacity_per_room = ${param_count}")
                update_values.append(room_data.max_capacity_per_room)
                param_count += 1
                
            if room_data.price_per_night is not None:
                update_fields.append(f"price_per_night = ${param_count}")
                update_values.append(room_data.price_per_night)
                param_count += 1
                
            if room_data.room_image_url is not None:
                update_fields.append(f"room_img_url = ${param_count}")
                update_values.append(room_data.room_image_url)
                param_count += 1
            
            # Update room details if any fields provided
            if update_fields:
                update_fields.append(f"updated_at = ${param_count}")
                update_values.append(datetime.now())
                param_count += 1
                update_values.append(room_id)
                
                query = f"""
                    UPDATE rooms 
                    SET {', '.join(update_fields)}
                    WHERE id = ${param_count}
                """
                await db.execute(query, *update_values)
            
            # Update facilities if provided
            if room_data.facilities is not None:
                # Delete existing facilities
                await db.execute(
                    "DELETE FROM facility_of_room WHERE room_id = $1",
                    room_id
                )
                
                # Insert new facilities
                for facility in room_data.facilities:
                    await db.execute("""
                        INSERT INTO facility_of_room (room_id, facility_name)
                        VALUES ($1, $2)
                    """, room_id, facility)
        
        return {
            "success": True,
            "message": "Room type updated successfully",
            "room_id": room_id,
            "updated_fields": len(update_fields) if update_fields else 0,
            "facilities_updated": room_data.facilities is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Health check
@app.get("/health")
async def health_check():
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": f"error: {str(e)}"}

# Status reference endpoints
@app.get("/api/status-reference")
async def get_status_reference():
    """Get reference for all status codes used in the system"""
    return {
        "booking_status": {
            1: "Pending",
            2: "Confirmed", 
            3: "Checked-in",
            4: "Completed",
            5: "Cancelled"
        },
        "payment_status": {
            1: "Pending",
            2: "Paid",
            3: "Refunded"
        },
        "user_types": {
            1: "Customer",
            2: "Admin"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)