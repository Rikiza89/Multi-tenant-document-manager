"""
URL patterns for documents app.
"""
from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.folder_list, name='list'),
    path('folder/<int:folder_id>/', views.folder_list, name='folder_list'),
    path('folder/create/', views.folder_create, name='folder_create'),
    path('folder/<int:parent_id>/create/', views.folder_create, name='folder_create_sub'),
    path('folder/<int:folder_id>/delete/', views.folder_delete, name='folder_delete'),
    path('upload/', views.document_upload, name='upload'),
    path('folder/<int:folder_id>/upload/', views.document_upload, name='upload_to_folder'),
    path('document/<int:document_id>/', views.document_detail, name='detail'),
    path('document/<int:document_id>/download/', views.document_download, name='download'),
    path('document/<int:document_id>/delete/', views.document_delete, name='delete'),
    
    path('document/<int:document_id>/preview/', views.document_preview, name='preview'),
    path('document/<int:document_id>/preview/content/', views.document_preview_content, name='preview_content'),
]