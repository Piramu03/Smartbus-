from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from .models import Stop,Route, Bus, Booking,Feedback
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, JsonResponse, FileResponse
from datetime import datetime
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.colors import HexColor,black,white
from django.conf import settings
from twilio.rest import Client


import io
from io import BytesIO


def home(request):
    return redirect('login')



# 🔐 User Login
def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')  # redirect to dashboard after login
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'login.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'booking/login.html', {'form': form})


# 📝 User Signup
def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        else:
            User.objects.create_user(username=username, password=password)
            messages.success(request, "Account created successfully. Please login.")
            return redirect('login')
    return render(request, 'booking/signup.html')


# 🧭 Dashboard - Search Routes
@login_required
def dashboard(request):
    if request.method == 'POST':
        source = request.POST.get('source')
        destination = request.POST.get('destination')
        routes = Route.objects.filter(
            source__name__icontains=source,
            destination__name__icontains=destination
        )
        return render(request, 'dashboard.html', {'routes': routes})
    return render(request, 'booking/dashboard.html')


@login_required
def book_ticket(request, route_id):
    from_stops = Stop.objects.all()
    to_stops = Stop.objects.all()
    buses = Bus.objects.all()

    if request.method == 'POST':
        
        passenger_name = request.POST.get('passenger_name') 
        bus_id = request.POST.get('bus')
        from_stop_id = request.POST.get('from_stop')
        to_stop_id = request.POST.get('to_stop')
        journey_date = request.POST.get('journey_date')
        phone = request.POST.get('phone')
        email = request.POST.get('email')

        # Validate required fields
        if not all([passenger_name, bus_id, from_stop_id, to_stop_id, journey_date, phone, email]):
            messages.error(request, "All fields are required.")
            return redirect('book_ticket', route_id=route_id)

        try:
            bus_id = int(bus_id)
            from_stop_obj = Stop.objects.get(id=int(from_stop_id))
            to_stop_obj = Stop.objects.get(id=int(to_stop_id))
        except (ValueError, Stop.DoesNotExist):
            messages.error(request, "Invalid stop or bus selection.")
            return redirect('book_ticket', route_id=route_id)

        # Check if the selected bus exists
        if not Bus.objects.filter(id=bus_id).exists():
            messages.error(request, "Invalid bus selection.")
            return redirect('book_ticket', route_id=bus_id)
        # Store human-readable stop names in session for select_seat
        request.session['passenger_name'] = passenger_name
        request.session['bus_id'] = bus_id
      
        request.session['from_stop'] = from_stop_obj.name
        request.session['to_stop'] = to_stop_obj.name
        request.session['journey_date'] = journey_date
        request.session['phone'] = phone
        request.session['email'] = email

        return redirect('select_seat', bus_id=bus_id)

    return render(request, 'booking/book_ticket.html', {
        'from_stops': from_stops,
        'to_stops': to_stops,
        'buses': buses,
    })

def get_route_timing(request):
    source_id = request.GET.get('source_id')
    destination_id = request.GET.get('destination_id')

    try:
        route = Route.objects.get(source_id=source_id, destination_id=destination_id)
        return JsonResponse({
            'departure_time': route.departure_time.strftime('%H:%M'),
            'arrival_time': route.arrival_time.strftime('%H:%M')
        })
    except Route.DoesNotExist:
        return JsonResponse({'error': 'No route found'}, status=404)
    
    
@login_required 
def select_seat(request, bus_id):
    passenger_name = request.session.get('passenger_name')
    from_stop = request.session.get('from_stop')
    to_stop = request.session.get('to_stop')
    journey_date = request.session.get('journey_date')
    phone = request.session.get('phone')
    email = request.session.get('email')



    if not all([passenger_name, bus_id, from_stop, to_stop, journey_date,phone,email]):
        messages.error(request, "Session expired or incomplete data.")
        return redirect('book_ticket')

    seat_labels = [
        '1W', '1B', '', '1C', '1D',
        '2A', '2B', '', '2C', '2D',
        '3A', '3B', '', '3C', '3D',
        '4A', '4B', '', '4C', '4D',
        '5A', '5B', '', '5C', '5D',
        '6A', '6B', '', '6C', '6D',
      
        'steering'
    ]

    # Hardcoded route order for now
    ROUTE_STOPS = ["Erode", "Karur", "Dindigul", "Madurai", "Nagercoil"]
    start_index = ROUTE_STOPS.index(from_stop)
    end_index = ROUTE_STOPS.index(to_stop)


    # Function to check if two seat bookings overlap in the route
    def is_overlap(existing_start, existing_end, new_start, new_end):
        return not (existing_end <= new_start or new_end <= existing_start)


    # Get all bookings for the same date
    all_bookings = Booking.objects.filter(
        bus_id=bus_id,
        journey_date=journey_date
    )

    # Determine which seats are actually occupied for this segment
    occupied_seats = []
    new_start = ROUTE_STOPS.index(from_stop)
    new_end = ROUTE_STOPS.index(to_stop)
    for booking in all_bookings:
        if booking.start_index is not None and booking.end_index is not None:
            if is_overlap(booking.start_index, booking.end_index, new_start, new_end):
                occupied_seats.append(str(booking.seat_number))

    if request.method == 'POST':
        selected = request.POST.get('selected_seats')
        selected_seats = selected.split(',') if selected else []

        # Check only for seats that overlap with this segment
        conflict = set(selected_seats).intersection(set(occupied_seats))
        if conflict:
            messages.error(request, f"Seats {', '.join(conflict)} already booked for this segment.")
            return redirect('select_seat', bus_id=bus_id)

        # Create bookings for selected seats
        for seat_number in selected_seats:

            Booking.objects.create(
                user=request.user,                         # or get user instance however you have it
                bus_id=bus_id,
                source=Stop.objects.get(name=from_stop),  # get Stop instance by name
                destination=Stop.objects.get(name=to_stop), # get Stop instance by name
                seat_number=seat_number,
                journey_date=journey_date,
                start_index=start_index,
                end_index=end_index,
                phone=request.session.get('phone'),
                email=request.session.get('email'),
                passenger_name=passenger_name,

            )


        # Clear session data
        for key in ['passenger_name', 'from_stop', 'to_stop', 'journey_date']:
            request.session.pop(key, None)

        return redirect('booking_success')

    return render(request, 'booking/select_seat.html', {
        'seats': seat_labels,
        'occupied_seats': occupied_seats,
        'bus_id': bus_id, 
    })

def format_phone_number(phone):
    """Ensure phone is in E.164 format for Twilio"""
    phone = phone.strip().replace(" ", "")
    if not phone.startswith("+"):
        # Assume India (+91) if country code is missing
        phone = "+91" + phone
    return phone

# ✅ Booking Success
@login_required
def booking_success(request):
    latest_booking = Booking.objects.filter(user=request.user).order_by('-id').first()

    if not latest_booking:
        return render(request, 'booking/success.html', {
            'error': "No booking found!"
        })

    # Prepare booking details
    passenger_name = latest_booking.passenger_name
    if passenger_name:
        passenger_name = passenger_name
    else:
        passenger_name = "UNKNOWN"
    bus = latest_booking.bus
    route = f"{latest_booking.source} → {latest_booking.destination}"
    seats = [latest_booking.seat_number] 
    journey_date = latest_booking.journey_date

    user_number = format_phone_number(latest_booking.phone)  # direct from Booking model
    sms_message = (
        f"Dear {passenger_name}, your bus booking is confirmed "
        f"for {latest_booking.source} → {latest_booking.destination} "
        f"on {journey_date}. "
        f"Seats: {', '.join(map(str, seats))}. "
        "Thank you for choosing Smart Bus System."
    )

    send_sms(user_number, sms_message)




    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- COLOR SCHEME ---
    primary_purple = HexColor('#6366f1')    # Purple (matching dashboard)
    dark_background = HexColor('#1e1b2e')   # Dark background
    secondary_purple = HexColor('#8b5cf6')  # Light purple
    accent_blue = HexColor('#06b6d4')       # Cyan blue accent
    card_background = HexColor('#2d2438')   # Dark card background
    text_light = HexColor('#e2e8f0')        # Light text

    # --- HEADER SECTION ---
    p.setFillColor(dark_background)
    p.rect(0, 0, width, height, fill=1, stroke=0)

    # Gradient header
    for i in range(120):
        alpha = i / 120.0
        r = 0.39 + (0.22 * alpha)
        g = 0.40 + (0.22 * alpha)
        b = 0.96
        p.setFillColorRGB(r, g, b)
        p.rect(0, height - 120 + i, width, 1, fill=1, stroke=0)

    # Logo
    p.setFillColor(text_light)
    p.circle(80, height - 60, 30, fill=0, stroke=1)
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(80, height - 65, "SPM")

    # Title
    p.setFont("Helvetica-Bold", 26)
    p.drawCentredString(300, height - 45, "Smart Bus Booking System")

    # Subtitle
    p.setFont("Helvetica", 14)
    p.drawString(130, height - 70, "Digital Bus Reservation Ticket")

    # Ticket badge
    p.setFillColor(accent_blue)
    p.rect(130, height - 95, 100, 20, fill=1, stroke=0)
    p.setFillColor(white)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(145, height - 88, "E-TICKET")

    # --- BODY BACKGROUND ---
    p.setFillColor(card_background)
    p.rect(30, height - 550, width - 60, 400, fill=1, stroke=0)
    p.setStrokeColor(primary_purple)
    p.setLineWidth(2)
    p.rect(30, height - 550, width - 60, 400, fill=0, stroke=1)

    # --- BUS INFORMATION ---
    y_pos = height - 160
    p.setFillColor(secondary_purple)
    p.rect(50, y_pos - 5, width - 100, 30, fill=1, stroke=0)
    p.setFillColor(text_light)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(60, y_pos + 8, "🚌 BUS INFORMATION")

    y_pos -= 40
    p.setFont("Helvetica-Bold", 12)
    bus_name = getattr(bus, 'bus_name', 'SPM Travels Express')
    bus_number = getattr(bus, 'bus_number', 'TNAB123')

    p.drawString(60, y_pos, f"Bus Operator: {bus_name}")
    p.drawString(60, y_pos - 20, f"Bus Number: {bus_number}")
    p.drawString(60, y_pos - 40, f"Bus Type: AC Sleeper")

    # --- PASSENGER DETAILS ---
    y_pos -= 80
    p.setFillColor(secondary_purple)
    p.rect(50, y_pos - 5, width - 100, 30, fill=1, stroke=0)
    p.setFillColor(text_light)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(60, y_pos + 8, "👤 PASSENGER DETAILS")

    y_pos -= 40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, y_pos, f"Passenger Name: {passenger_name.upper()}")
    p.drawString(60, y_pos - 20, f"Seat Numbers: {', '.join(map(str, seats))}")
    p.drawString(60, y_pos - 40, f"Total Passengers: {len(seats)}")

    # --- JOURNEY DETAILS ---
    y_pos -= 80
    p.setFillColor(secondary_purple)
    p.rect(50, y_pos - 5, width - 100, 30, fill=1, stroke=0)
    p.setFillColor(text_light)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(60, y_pos + 8, "🗺️ JOURNEY DETAILS")

    y_pos -= 40
    p.setFont("Helvetica-Bold", 12)

    route_parts = route.split(' to ') if ' to ' in route else route.split('-')
    if len(route_parts) >= 2:
        from_city = route_parts[0].strip()
        to_city = route_parts[1].strip()
    else:
        from_city = route
        to_city = "Destination"

    p.drawString(60, y_pos, f"From: {from_city.upper()}")
    p.drawString(60, y_pos - 20, f"To: {to_city.upper()}")
    p.drawString(60, y_pos - 40, f"Journey Date: {journey_date}")
    p.drawString(60, y_pos - 60, "Departure Time: 06:30 AM")
    p.drawString(60, y_pos - 80, "Arrival Time: 02:30 PM")

    # --- BOOKING INFO BOX ---
    booking_box_y = y_pos - 120
    p.setFillColor(primary_purple)
    p.rect(350, booking_box_y - 20, 200, 120, fill=1, stroke=0)

    for i in range(20):
        alpha = i / 20.0
        r = 0.39 + (0.15 * alpha)
        g = 0.40 + (0.15 * alpha)
        b = 0.95
        p.setFillColorRGB(r, g, b)
        p.rect(350, booking_box_y - 20 + i * 6, 200, 6, fill=1, stroke=0)

    p.setFillColor(text_light)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(370, booking_box_y + 70, "BOOKING INFO")

    p.setFont("Helvetica-Bold", 12)
    p.drawString(370, booking_box_y + 40, "Booking ID:")
    p.setFont("Helvetica", 12)
    p.drawString(370, booking_box_y + 25, f"#{latest_booking.id}")

    p.setFont("Helvetica-Bold", 12)
    p.drawString(370, booking_box_y + 5, "Booking Date:")
    p.setFont("Helvetica", 12)
    p.drawString(370, booking_box_y - 10, datetime.now().strftime("%d/%m/%Y"))

    # Status badge
    p.setFillColor(accent_blue)
    p.rect(370, booking_box_y - 35, 80, 20, fill=1, stroke=0)
    p.setFillColor(white)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(385, booking_box_y - 28, "CONFIRMED")

    # --- TERMS ---
    terms_y = 180
    p.setFillColor(text_light)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, terms_y, "IMPORTANT TERMS & CONDITIONS:")

    p.setFont("Helvetica", 9)
    p.setFillColor(HexColor('#94a3b8'))
    terms = [
        "• Please arrive at the boarding point 15 minutes before departure",
        "• Valid ID proof is mandatory during travel",
        "• Smoking and alcohol consumption are strictly prohibited",
        "• Management is not responsible for loss of belongings",
        "• Ticket is non-transferable and non-refundable"
    ]
    for i, term in enumerate(terms):
        p.drawString(50, terms_y - 25 - (i * 15), term)

    # --- FOOTER ---
    for i in range(60):
        alpha = i / 60.0
        r = 0.12 + (0.27 * alpha)
        g = 0.11 + (0.29 * alpha)
        b = 0.18 + (0.77 * alpha)
        p.setFillColorRGB(r, g, b)
        p.rect(0, i, width, 1, fill=1, stroke=0)

    p.setFillColor(text_light)
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width/2, 35, "Smart Bus Booking System")
    p.setFont("Helvetica", 11)
    p.drawCentredString(width/2, 18, "Thank you for choosing our service • Have a safe journey!")

    # --- BORDER ---
    p.setStrokeColor(primary_purple)
    p.setDash(4, 4)
    p.setLineWidth(1)
    p.rect(20, 70, width - 40, height - 190, fill=0, stroke=1)

    # Save
    p.showPage()
    p.save()

    pdf_data = buffer.getvalue()
    buffer.close()



    to_email = latest_booking.email

    # Email the ticket
    email = EmailMessage(
        subject="Your Bus Ticket - Smart Bus Reservation",
        body=f"Dear {passenger_name},\n\nPlease find attached your ticket.\n\nSafe Journey!",
        from_email="yourbusapp@example.com",
        to=[to_email],  # Make sure the user has an email in profile
    )
    email.attach("ticket.pdf", pdf_data, "application/pdf")
    email.send()

    # Also allow direct download from success page
    response = FileResponse(io.BytesIO(pdf_data), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ticket.pdf"'

    # Pass context for success.html
    context = {
        'passenger_name': passenger_name,
        'bus': bus,
        'route': route,
        'seats': seats,
        'journey_date': journey_date,
    }

    return render(request, 'booking/success.html', context)

def send_sms(to_number, message):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    try:
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_number
        )
        return True
    except Exception as e:
        print("SMS Error:", e)
        return False
def send_voice_call(to_number, message):
    try:
        call = Client.calls.create(
            twiml=f'<Response><Say>{message}</Say></Response>',
            to=to_number,
            from_=settings.TWILIO_PHONE_NUMBER
        )
        return True
    except Exception as e:
        print("Voice Call Error:", e)
        return False



def view_ticket_by_phone(request):
    tickets = None
    message = None

    if request.method == 'POST':
        phone = request.POST.get('phone')
        journey_date = request.POST.get('journey_date')  # match form field name

        if phone and journey_date:
            try:
                journey_date_obj = datetime.strptime(journey_date, "%Y-%m-%d").date()
            except ValueError:
                message = 'Invalid date format. Use YYYY-MM-DD.'
            else:
                tickets = Booking.objects.filter(phone=phone, journey_date=journey_date_obj)
                if not tickets.exists():
                    message = 'No tickets found for the given details.'

    return render(request, 'booking/view_ticket_by_phone.html', {
        'tickets': tickets,
        'message': message
    })

def feedback_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        if name and email and message:
            feedback = Feedback.objects.create(
                name=name,
                email=email,
                message=message
            )
            feedback.save()
            messages.success(request, "Thank you for your feedback! 🚍")
            return redirect("feedback")  # reload the page after submission
        else:
            messages.error(request, "All fields are required!")

    return render(request, "booking/feedback.html")


def contact(request):
    return render(request, 'booking/contact.html')
