from django.urls import path

from . import views

urlpatterns = [
    path(
        "",
        views.HelloView.as_view(),
        name="home",
    ),
]
