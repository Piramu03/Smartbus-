from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Booking

# 🔐 User Signup Form
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


# 🎫 Booking Form
class BookingForm(forms.ModelForm):
    journey_date = forms.DateField(widget=forms.SelectDateWidget)

    class Meta:
        model = Booking
        fields = [
            'bus',
            'source',
            'destination',
            'seat_number',
            'journey_date'
        ]
