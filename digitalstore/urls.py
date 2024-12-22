from django.contrib import admin
from django.urls import path, include
from digikeyoutlet import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('', include('digikeyoutlet.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # Include auth URLs
]
