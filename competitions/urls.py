from django.urls import path

from . import views

urlpatterns = [
    path('competitions/', views.CompetitionListView.as_view(), name='competition-list'),
    path('competitions/matches/', views.MatchListView.as_view(), name='match-list'),
    path('competitions/matches/<int:pk>/simulate/', views.SimulateMatchView.as_view(), name='match-simulate'),
]
