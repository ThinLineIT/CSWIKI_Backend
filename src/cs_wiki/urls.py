from django.urls import path

from cs_wiki.views import (
    HomeView,
    IssueListView,
    NoteListView,
    NoteDetailView,
    TopicView,
    PageView,
    PageDetailView,
)

app_name = "cs_wiki"

urlpatterns = [
    path("home/", HomeView.as_view(), name="home"),
    path("issues/", IssueListView.as_view(), name="issue-list"),
    path("notes/", NoteListView.as_view(), name="note-list"),
    path("notes/<int:note_id>/", NoteDetailView.as_view(), name="note-detail"),
    path("topics/", TopicView.as_view(), name="topic"),
    path("pages/", PageView.as_view(), name="page"),
    path("pages/<int:page_id>/", PageDetailView.as_view(), name="page-detail"),
]
