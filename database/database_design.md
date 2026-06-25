# Database Design

## 1. Users

Purpose:

Stores authentication details for every user.

| Column | Type | Description |
|---------|------|-------------|
| user_id | SERIAL | Primary Key |
| full_name | VARCHAR(100) | Full name |
| email | VARCHAR(100) | Unique email |
| password_hash | TEXT | Encrypted password |
| role | VARCHAR(20) | Admin / Trainer / Member |
| phone | VARCHAR(20) | Contact number |
| created_at | TIMESTAMP | Account creation date |
| updated_at | TIMESTAMP | Last updated |
| is_active | BOOLEAN | Account status |

---

## 2. Members

Purpose:

Stores member-specific information.

| Column | Type | Description |
|---------|------|-------------|
| member_id | SERIAL | Primary Key |
| user_id | INTEGER | Foreign Key → Users.user_id |
| membership_plan_id | INTEGER | Foreign Key → MembershipPlans.plan_id |
| trainer_id | INTEGER | Foreign Key → Trainers.trainer_id |
| gender | VARCHAR(20) | Gender |
| date_of_birth | DATE | Date of birth |
| height_cm | DECIMAL(5,2) | Height in cm |
| weight_kg | DECIMAL(5,2) | Current weight |
| bmi | DECIMAL(5,2) | Body Mass Index |
| address | TEXT | Residential address |
| emergency_contact | VARCHAR(20) | Emergency phone number |
| joined_date | DATE | Gym joining date |
| status | VARCHAR(20) | Active / Inactive |

---

## 3. Trainers

Purpose:

Stores trainer information.

| Column | Type | Description |
|---------|------|-------------|
| trainer_id | SERIAL | Primary Key |
| user_id | INTEGER | Foreign Key → Users.user_id |
| specialization | VARCHAR(100) | Area of expertise |
| experience_years | INTEGER | Years of experience |
| qualification | VARCHAR(100) | Certifications |
| salary | DECIMAL(10,2) | Monthly salary |
| hire_date | DATE | Joining date |
| status | VARCHAR(20) | Active / Inactive |

---

## 4. MembershipPlans

Purpose:

Stores available membership plans.

| Column | Type | Description |
|---------|------|-------------|
| plan_id | SERIAL | Primary Key |
| plan_name | VARCHAR(100) | Gold / Silver / Platinum |
| duration_months | INTEGER | Membership duration |
| price | DECIMAL(10,2) | Plan cost |
| description | TEXT | Plan benefits |
| is_active | BOOLEAN | Available or not |

---

## 5. Memberships

Purpose:

Stores purchased memberships.

| Column | Type | Description |
|---------|------|-------------|
| membership_id | SERIAL | Primary Key |
| member_id | INTEGER | Foreign Key → Members.member_id |
| plan_id | INTEGER | Foreign Key → MembershipPlans.plan_id |
| start_date | DATE | Membership start |
| end_date | DATE | Membership expiry |
| payment_status | VARCHAR(20) | Paid / Pending |
| status | VARCHAR(20) | Active / Expired |

### Relationships

- One Member can have many Memberships.
- One Membership Plan can be purchased by many Members.
- Each Membership belongs to exactly one Member.
- Each Membership uses exactly one Membership Plan.


---

## 6. WorkoutPlans

Purpose:

Stores workout plans created by trainers.

| Column | Type | Description |
|---------|------|-------------|
| workout_id | SERIAL | Primary Key |
| trainer_id | INTEGER | Foreign Key → Trainers.trainer_id |
| member_id | INTEGER | Foreign Key → Members.member_id |
| title | VARCHAR(100) | Workout plan name |
| goal | VARCHAR(100) | Weight Loss / Muscle Gain / Strength |
| duration_weeks | INTEGER | Plan duration |
| notes | TEXT | Trainer notes |
| created_at | TIMESTAMP | Creation date |

---

## 7. Exercises

Purpose:

Stores exercises belonging to a workout plan.

| Column | Type | Description |
|---------|------|-------------|
| exercise_id | SERIAL | Primary Key |
| workout_id | INTEGER | Foreign Key → WorkoutPlans.workout_id |
| exercise_name | VARCHAR(100) | Exercise name |
| sets | INTEGER | Number of sets |
| reps | INTEGER | Number of repetitions |
| rest_seconds | INTEGER | Rest time |
| instructions | TEXT | Exercise instructions |

---

## 8. DietPlans

Purpose:

Stores personalized diet plans created by trainers.

| Column | Type | Description |
|---------|------|-------------|
| diet_id | SERIAL | Primary Key |
| trainer_id | INTEGER | Foreign Key → Trainers.trainer_id |
| member_id | INTEGER | Foreign Key → Members.member_id |
| title | VARCHAR(100) | Diet plan name |
| goal | VARCHAR(100) | Weight Loss / Muscle Gain / Maintenance |
| calories_per_day | INTEGER | Daily calorie target |
| notes | TEXT | Additional instructions |
| created_at | TIMESTAMP | Creation date |

---

## 9. Attendance

Purpose:

Stores gym check-in and attendance records.

| Column | Type | Description |
|---------|------|-------------|
| attendance_id | SERIAL | Primary Key |
| member_id | INTEGER | Foreign Key → Members.member_id |
| check_in_time | TIMESTAMP | Check-in time |
| check_out_time | TIMESTAMP | Check-out time |
| attendance_date | DATE | Attendance date |
| method | VARCHAR(20) | QR / Manual |
| status | VARCHAR(20) | Present / Absent |

---

## 10. ProgressRecords

Purpose:

Stores member fitness progress over time.

| Column | Type | Description |
|---------|------|-------------|
| progress_id | SERIAL | Primary Key |
| member_id | INTEGER | Foreign Key → Members.member_id |
| weight_kg | DECIMAL(5,2) | Current weight |
| body_fat_percentage | DECIMAL(5,2) | Body fat % |
| chest_cm | DECIMAL(5,2) | Chest measurement |
| waist_cm | DECIMAL(5,2) | Waist measurement |
| biceps_cm | DECIMAL(5,2) | Biceps measurement |
| thighs_cm | DECIMAL(5,2) | Thigh measurement |
| bmi | DECIMAL(5,2) | Body Mass Index |
| recorded_at | TIMESTAMP | Record date |

---

---

## 11. Payments

Purpose:

Stores all membership payment transactions made by members.

| Column | Type | Description |
|---------|------|-------------|
| payment_id | SERIAL | Primary Key |
| member_id | INTEGER | Foreign Key → Members.member_id |
| membership_id | INTEGER | Foreign Key → Memberships.membership_id |
| amount | DECIMAL(10,2) | Payment amount |
| payment_method | VARCHAR(30) | Cash / UPI / Card / Net Banking |
| payment_status | VARCHAR(20) | Paid / Pending / Failed / Refunded |
| transaction_id | VARCHAR(100) | Payment reference number |
| payment_date | TIMESTAMP | Date and time of payment |

### Relationships

- One Member can make many Payments.
- Each Payment belongs to one Membership.

---

## 12. Bookings

Purpose:

Stores personal training session and fitness class bookings made by members.

| Column | Type | Description |
|---------|------|-------------|
| booking_id | SERIAL | Primary Key |
| member_id | INTEGER | Foreign Key → Members.member_id |
| trainer_id | INTEGER | Foreign Key → Trainers.trainer_id |
| booking_date | DATE | Booking date |
| booking_time | TIME | Booking time |
| session_type | VARCHAR(50) | Personal Training / Yoga / HIIT / Zumba |
| booking_status | VARCHAR(20) | Booked / Completed / Cancelled |

### Relationships

- One Member can have many Bookings.
- One Trainer can receive many Bookings.

---

## 13. Notifications

Purpose:

Stores notifications sent to members and trainers.

| Column | Type | Description |
|---------|------|-------------|
| notification_id | SERIAL | Primary Key |
| user_id | INTEGER | Foreign Key → Users.user_id |
| title | VARCHAR(100) | Notification title |
| message | TEXT | Notification content |
| notification_type | VARCHAR(30) | Reminder / Announcement / Payment / Workout |
| is_read | BOOLEAN | Read status |
| created_at | TIMESTAMP | Date and time sent |

### Relationships

- One User can receive many Notifications.