-- ==========================================================
-- FitSphere
-- Database Schema
-- Database: PostgreSQL
-- Author: Sangeerth Murali
-- ==========================================================


CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE MembershipPlans (
    plan_id SERIAL PRIMARY KEY,
    plan_name VARCHAR(50) NOT NULL,
    duration_months INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE Trainers (
    trainer_id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES Users(user_id),
    specialization VARCHAR(100),
    experience_years INTEGER,
    qualification VARCHAR(100),
    salary DECIMAL(10,2),
    hire_date DATE,
    status VARCHAR(20)
);

CREATE TABLE Members (
    member_id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES Users(user_id),
    plan_id INTEGER REFERENCES MembershipPlans(plan_id),
    trainer_id INTEGER REFERENCES Trainers(trainer_id),
    gender VARCHAR(20),
    date_of_birth DATE,
    height_cm DECIMAL(5,2),
    weight_kg DECIMAL(5,2),
    bmi DECIMAL(5,2),
    address TEXT,
    emergency_contact VARCHAR(20),
    joined_date DATE,
    status VARCHAR(20)
);

CREATE TABLE Memberships (
    membership_id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES Members(member_id),
    plan_id INTEGER REFERENCES MembershipPlans(plan_id),
    start_date DATE,
    end_date DATE,
    payment_status VARCHAR(20),
    status VARCHAR(20)
);

CREATE TABLE WorkoutPlans (
    workout_id SERIAL PRIMARY KEY,
    trainer_id INTEGER REFERENCES Trainers(trainer_id),
    member_id INTEGER REFERENCES Members(member_id),
    title VARCHAR(100),
    goal VARCHAR(100),
    duration_weeks INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE DietPlans (
    diet_id SERIAL PRIMARY KEY,
    trainer_id INTEGER REFERENCES Trainers(trainer_id),
    member_id INTEGER REFERENCES Members(member_id),
    title VARCHAR(100),
    goal VARCHAR(100),
    calories_per_day INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Attendance (
    attendance_id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES Members(member_id),
    check_in_time TIMESTAMP,
    check_out_time TIMESTAMP,
    attendance_date DATE,
    method VARCHAR(20),
    status VARCHAR(20)
);

CREATE TABLE ProgressRecords (
    progress_id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES Members(member_id),
    weight_kg DECIMAL(5,2),
    body_fat_percentage DECIMAL(5,2),
    chest_cm DECIMAL(5,2),
    waist_cm DECIMAL(5,2),
    biceps_cm DECIMAL(5,2),
    thighs_cm DECIMAL(5,2),
    bmi DECIMAL(5,2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Payments (
    payment_id SERIAL PRIMARY KEY,
    membership_id INTEGER REFERENCES Memberships(membership_id),
    amount DECIMAL(10,2),
    payment_method VARCHAR(30),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    transaction_id VARCHAR(100),
    status VARCHAR(20)
);

CREATE TABLE Bookings (
    booking_id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES Members(member_id),
    trainer_id INTEGER REFERENCES Trainers(trainer_id),
    booking_date DATE,
    booking_time TIME,
    purpose VARCHAR(100),
    status VARCHAR(20)
);

CREATE TABLE Notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES Users(user_id),
    title VARCHAR(100),
    message TEXT,
    notification_type VARCHAR(30),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);