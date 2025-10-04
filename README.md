## Smart Bus Reservation System

The Smart Bus Reservation System is a web platform designed to make intercity travel smarter and more efficient. It supports dynamic seat allocation, real-time booking updates, e-ticket delivery via email, and SMS notifications to enhance passenger experience.

## Key Features

## Smart Booking & Reservation
Book seats from source to destination or intermediate stops

Dynamic seat allocation ensures seats vacated mid-journey become available for new passengers

View available seats in real time with color-coded seat status

## Ticket Management

View Ticket by Phone Number: Passengers can retrieve booked tickets easily using their registered phone number

Email e-Ticket: Automatically sends digital ticket with route details, bus info, and seat number to the passenger’s email

## Notifications & Alerts

SMS & Email Confirmation after successful booking

2-Hour Reminder Notification before journey start

15-Minute Arrival Alert with sound notification if the passenger is sleeping

Notifications managed via Celery background tasks for automation

## Customer Feedback Form

After completing the journey, passengers can submit feedback about their travel experience

Feedback stored in the database and viewable by the admin for service improvement

## Admin / Operator Panel

Add, edit, or remove buses, routes, and schedules

Monitor seat usage and journey statistics

View passenger feedback reports and system logs

## Tech Stack
-- **Frontend** - HTML/CSS/Javascript
-- **Backend** - Django(Python)
-- **Database** - SQLite
-- **Task** - Celery
-- **Notifications** - Twilio(SMS),SMTP(Email)

## Installation Guide
1.Clone the Repository
       
    git clone https://github.com/Piramu03/Smartbus-.git
    cd Smartbus/backend
2.Create Virtual Environment

    python -m venv venv
    venv\Scripts\activate  # On Windows

3.Install Dependencies

    pip install -r requirements.txt
4.Configure Environment Variables

Configure Environment Variables:
      
      EMAIL_HOST_USER=your_email@example.com
      EMAIL_HOST_PASSWORD=your_app_password
      TWILIO_ACCOUNT_SID=your_twilio_sid
      TWILIO_AUTH_TOKEN=your_twilio_token
      TWILIO_PHONE_NUMBER=+1234567890
5.Apply Migrations

     python manage.py makemigrations
     python manage.py migrate
6.Start the Server

    python manage.py runserver

## Developed By

-- **Piramu M**
-- **Final Year – B.Tech Artificial Intelligence and Data Science**
