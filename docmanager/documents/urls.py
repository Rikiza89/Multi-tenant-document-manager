"""
URL patterns for documents app.
"""
from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.document_list, name='list'),
    path('upload/', views.document_upload, name='upload'),
    path('document/<int:document_id>/', views.document_detail, name='detail'),
    path('document/<int:document_id>/download/', views.document_download, name='download'),
    path('document/<int:document_id>/delete/', views.document_delete, name='delete'),
]
