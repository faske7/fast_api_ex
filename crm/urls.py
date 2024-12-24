from django.urls import path
from . import views

app_name = "crm"

urlpatterns = [
    path("", views.request_list, name="request_list"),
    path("<int:request_id>/", views.request_detail, name="request_detail"),
    path("<int:request_id>/close/", views.close_request, name="close_request"),
]

