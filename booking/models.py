from django.db import models
from django.contrib.auth.models import User

class Stop(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)  
    def __str__(self):
        return self.name


class Route(models.Model):
    source = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='route_sources')
    destination = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='route_destinations')
    departure_time = models.TimeField(null=True, blank=True)
    arrival_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.source.name} → {self.destination.name}"


class Bus(models.Model):
    bus_name = models.CharField(max_length=100)
    number_plate = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField()
    route = models.ForeignKey(Route, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.bus_name} ({self.number_plate})"


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, null=True, blank=True)
    source = models.ForeignKey(Stop, related_name='booking_source', on_delete=models.CASCADE, null=True, blank=True)
    destination = models.ForeignKey(Stop, related_name='booking_destination', on_delete=models.CASCADE, null=True, blank=True)
    seat_number = models.CharField(max_length=5)  # e.g. '2A', '5W'
    journey_date = models.DateField()
    passenger_name = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    timestamp = models.DateTimeField(auto_now_add=True)
    confirmation_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    destination_alert_sent = models.BooleanField(default=False)

    # ✅ New fields for seat segment logic
    start_index = models.PositiveIntegerField(null=True, blank=True, help_text="Stop order of source")
    end_index = models.PositiveIntegerField(null=True, blank=True, help_text="Stop order of destination")

    def __str__(self):
        return f"{self.user.username} - {self.bus.bus_name} ({self.source} → {self.destination})"
class Feedback(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.submitted_at.strftime('%Y-%m-%d')}"
class ContactInfo(models.Model):
    admin_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()

    def __str__(self):
        return self.admin_name
