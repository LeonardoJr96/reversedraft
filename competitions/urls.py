from django.urls import path

from . import views

urlpatterns = [
    path('competitions/', views.CompetitionListView.as_view(), name='competition-list'),
    path('competitions/matches/', views.MatchListView.as_view(), name='match-list'),
    path('competitions/matches/<int:pk>/simulate/', views.SimulateMatchView.as_view(), name='match-simulate'),
    path('competitions/<int:pk>/finish/', views.FinishCompetitionView.as_view(), name='competition-finish'),
    path('competitions/<int:pk>/generate-bracket/', views.GenerateBracketView.as_view(), name='competition-generate-bracket'),
    path('competitions/<int:pk>/bracket/', views.BracketView.as_view(), name='competition-bracket'),
]
