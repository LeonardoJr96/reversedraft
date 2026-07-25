from django.urls import path
from .views import MyTeamView, MyRosterView, TacticSlotView

urlpatterns = [
    path("me/", MyTeamView.as_view()),
    path("me/roster/", MyRosterView.as_view()),
    path("me/slots/<str:slot_code>/", TacticSlotView.as_view()),
]