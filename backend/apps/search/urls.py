from django.urls import path
from apps.search.views import SearchView, SearchHistoryView

urlpatterns = [
    path("search/", SearchView.as_view(), name="search"),
    path("search/history/", SearchHistoryView.as_view(), name="search-history"),
]
