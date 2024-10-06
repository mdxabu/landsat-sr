from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("map", views.map_view, name="map"),
    path('landsat_pass/', views.check_landsat_pass, name='landsat_pass'),
]