from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    TicketViewSet, CategoryViewSet, CompanyViewSet, ProjectViewSet,
    api_status, generate_api_token, toggle_api_access, whatsapp_receive_message,
    landing_page_meeting_click, landing_page_contact_click
)

# Router para los ViewSets
router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='api-tickets')
router.register(r'categories', CategoryViewSet, basename='api-categories')
router.register(r'companies', CompanyViewSet, basename='api-companies')
router.register(r'projects', ProjectViewSet, basename='api-projects')

api_urlpatterns = [
    # URLs del router
    path('', include(router.urls)),
    
    # URLs de utilidad
    path('status/', api_status, name='api-status'),
    path('generate-token/', generate_api_token, name='api-generate-token'),
    path('toggle-access/', toggle_api_access, name='api-toggle-access'),
    
    # URLs de WhatsApp
    path('whatsapp/message/', whatsapp_receive_message, name='api-whatsapp-message'),
    
    # URLs de Landing Pages (para contadores)
    path('landing-pages/<slug:slug>/meeting-click/', landing_page_meeting_click, name='api-landing-meeting-click'),
    path('landing-pages/<slug:slug>/contact-click/', landing_page_contact_click, name='api-landing-contact-click'),
]

# Django espera que la variable se llame urlpatterns
urlpatterns = api_urlpatterns