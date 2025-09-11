from panel_settings import views
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('patient_rating.urls')),
    path('patients/', include('patient_rating.urls')),
]


urlpatterns += [
    path('api/panel-settings/', views.panel_settings_view, name='panel_settings'),
]