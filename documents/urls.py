from django.urls import path
from . import views

urlpatterns = [
    path('', views.liste_documents, name='liste_documents'),
    path('nouveau/', views.creer_document, name='creer_document'),
    path('<int:document_id>/pdf/', views.apercu_pdf, name='apercu_pdf'),
]