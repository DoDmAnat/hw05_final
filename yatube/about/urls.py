from django.urls import path
from . import views

app_name = 'about'

urlpatterns = [
    path('author/', views.AboutAuthorView.as_view(), name="author_page"),
    path('tech/', views.AboutTechView.as_view(), name="tech_page"),
]
