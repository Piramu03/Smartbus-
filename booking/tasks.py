from datetime import datetime,timedelta

from django.utils.timezone import now
from django.core.mail import send_mail
from twilio.rest import Client  # type: ignore
from django.conf import settings
from celery import shared_task
from .models import Booking

def send_sms(to_number, message):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_number
        )
        print(f"SMS sent to {to_number}: SID={msg.sid}")
    except Exception as e:
        print(f"Failed to send SMS to {to_number}: {e}")
        
def send_voice_call(to_number, message):
    try:
        call = client.calls.create(
            twiml=f'<Response><Say>{message}</Say></Response>',
            to=to_number,
            from_=settings.TWILIO_PHONE_NUMBER
        )
        return True
    except Exception as e:
        print("Voice Call Error:", e)
        return False


@shared_task
def send_due_notifications():
    bookings = Booking.objects.all()
    current_time = now()

    for booking in bookings:
        source_name = str(booking.source) if booking.source else "Unknown"
        destination_name = str(booking.destination) if booking.destination else "Unknown"

        # 1️⃣ Immediate confirmation
        if not booking.confirmation_sent:
            message = f"Booking Confirmed: Seat {booking.seat_number}, {source_name} → {destination_name}"
            send_sms(booking.phone, message)
            try:
                send_mail(
                    "Booking Confirmed",
                    message,
                    settings.EMAIL_HOST_USER,
                    [booking.email],
                    fail_silently=False,
                )
                print(f"Email sent to {booking.email}")
            except Exception as e:
                print(f"Failed to send email to {booking.email}: {e}")

            booking.confirmation_sent = True
            booking.save()

        # 2️⃣ Reminder 2 hours before journey
        journey_datetime = datetime.combine(booking.journey_date, datetime.min.time())
        time_to_journey = journey_datetime - current_time
        if not booking.reminder_sent and timedelta(0) < time_to_journey <= timedelta(hours=2):
            message = f"Reminder: Your journey starts in 2 hours. Seat {booking.seat_number} from {source_name} → {destination_name}"
            send_sms(booking.phone, message)
            try:
                send_mail(
                    "Journey Reminder",
                    message,
                    settings.EMAIL_HOST_USER,
                    [booking.email],
                    fail_silently=False,
                )
                print(f"Reminder email sent to {booking.email}")
            except Exception as e:
                print(f"Failed to send reminder email to {booking.email}: {e}")

            booking.reminder_sent = True
            booking.save()

        # 3️⃣ Destination alert 15 mins before arrival
        estimated_arrival = journey_datetime + timedelta(hours=booking.bus.estimated_duration_hours)
        time_to_arrival = estimated_arrival - current_time
        if not booking.destination_alert_sent and timedelta(0) < time_to_arrival <= timedelta(minutes=15):
            message = f"Alert: You will reach {destination_name} in 15 minutes. Prepare to get off."
            send_sms(booking.phone, message)
            try:
                send_mail(
                    "Destination Alert",
                    message,
                    settings.EMAIL_HOST_USER,
                    [booking.email],
                    fail_silently=False,
                )
                print(f"Destination alert email sent to {booking.email}")
            except Exception as e:
                print(f"Failed to send destination alert email to {booking.email}: {e}")

            booking.destination_alert_sent = True
            booking.save()
