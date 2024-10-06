from django.http import JsonResponse
from skyfield.api import Topos, load
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import User

def index(request):
    
    return render(request, "landsatapp/index.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, username=email, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("map"))
        else:
            return render(request, "landsatapp/login.html", {
                "message": "Invalid email and/or password."
            })
    else:
        return render(request, "landsatapp/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "landsatapp/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(email, email, password)
            user.save()
        except IntegrityError as e:
            print(e)
            return render(request, "landsatapp/register.html", {
                "message": "Email address already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "landsatapp/register.html")

@login_required
def map_view(request):
    return render(request,"landsatapp/map.html")

def check_landsat_pass(request):
    # Get latitude and longitude from the GET parameters
    latitude = float(request.GET.get('latitude'))
    longitude = float(request.GET.get('longitude'))

    # Load the TLE data for Landsat 8 and Landsat 9
    stations_url = 'https://celestrak.com/NORAD/elements/resource.txt'
    satellites = load.tle_file(stations_url)
    by_name = {sat.name: sat for sat in satellites}

    landsat_8 = by_name['LANDSAT 8']
    landsat_9 = by_name['LANDSAT 9']

    # Define the user’s location
    user_location = Topos(latitude_degrees=latitude, longitude_degrees=longitude)

    # Load the timescale and get the current time
    ts = load.timescale()

    # Define the time window for the next day
    t0 = ts.now()  # current time
    t1 = ts.utc(t0.utc_datetime() + timedelta(days=1))  # 1 day ahead

    notifications = []

    # Check for Landsat 8 passes
    t_8, events_8 = landsat_8.find_events(user_location, t0, t1, altitude_degrees=30.0)
    for ti, event in zip(t_8, events_8):
        event_name = ('rise above 30°', 'culminate', 'set below 30°')[event]
        notifications.append(f'Landsat 8 will {event_name} at {ti.utc_iso()} over your location.')

    # Check for Landsat 9 passes
    t_9, events_9 = landsat_9.find_events(user_location, t0, t1, altitude_degrees=30.0)
    for ti, event in zip(t_9, events_9):
        event_name = ('rise above 30°', 'culminate', 'set below 30°')[event]
        notifications.append(f'Landsat 9 will {event_name} at {ti.utc_iso()} over your location.')

    # Return notifications as JSON response
    return JsonResponse({'notifications': notifications})
