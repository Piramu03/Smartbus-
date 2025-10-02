from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),  
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('book-ticket/<int:route_id>/', views.book_ticket, name='book_ticket'),
    path('get-timing/', views.get_route_timing, name='get_route_timing'),
    path('view-ticket/', views.view_ticket_by_phone, name='view_ticket_by_phone'),

    
    path('feedback/', views.feedback_view, name='feedback'),
    path('contact/', views.contact, name='contact'),
    path('select-seat/<int:bus_id>/', views.select_seat, name='select_seat'),  # ✅ Correct route
    path('success/', views.booking_success, name='booking_success'),

    

]
