from django.contrib import admin
from django import forms
from .models import Stop, Route, Bus, Booking
from django.contrib.auth.models import User

# --- Stop ---
@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ['name']

# --- Bus ---
@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ['bus_name', 'number_plate', 'capacity']

# --- Route Custom Form ---
class RouteAdminForm(forms.ModelForm):
    source_name = forms.CharField(label="Source")
    destination_name = forms.CharField(label="Destination")

    class Meta:
        model = Route
        fields = ['source_name', 'destination_name','departure_time', 'arrival_time']

    def clean(self):
        cleaned_data = super().clean()
        source_obj, _ = Stop.objects.get_or_create(name=cleaned_data['source_name'])
        destination_obj, _ = Stop.objects.get_or_create(name=cleaned_data['destination_name'])
        self.instance.source = source_obj
        self.instance.destination = destination_obj
        return cleaned_data

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    form = RouteAdminForm
    list_display = ['source', 'destination','departure_time', 'arrival_time']



# --- Booking Custom Form ---
class BookingAdminForm(forms.ModelForm):
    username = forms.CharField(label="Username")
    bus_name = forms.CharField(label="Bus Name")
    source_name = forms.CharField(label="Source")
    destination_name = forms.CharField(label="Destination")

    class Meta:
        model = Booking
        fields = ['username', 'bus_name', 'source_name', 'destination_name', 'seat_number', 'journey_date']

    def clean(self):
        cleaned_data = super().clean()
        
        # Get or raise user
        try:
            user = User.objects.get(username=cleaned_data['username'])
        except User.DoesNotExist:
            raise forms.ValidationError("User not found.")

        # Get or raise bus
        try:
            bus = Bus.objects.get(bus_name=cleaned_data['bus_name'])
        except Bus.DoesNotExist:
            raise forms.ValidationError("Bus not found.")

        # Create or get stops
        source, _ = Stop.objects.get_or_create(name=cleaned_data['source_name'])
        destination, _ = Stop.objects.get_or_create(name=cleaned_data['destination_name'])

        self.instance.user = user
        self.instance.bus = bus
        self.instance.source = source
        self.instance.destination = destination

        return cleaned_data

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm
    list_display = ['user', 'bus', 'source', 'destination', 'seat_number', 'journey_date','phone','email']
