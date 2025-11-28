from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    TicketViewSet, CategoryViewSet, CompanyViewSet, ProjectViewSet,
    api_status, generate_api_token, toggle_api_access, whatsapp_receive_message,
    landing_page_meeting_click, landing_page_contact_click,
    active_users_count, active_users_list, open_tickets_count, direct_ai_chat,
    system_info_api, short_url_stats_api, upcoming_events_list, web_counter_track,
    web_counter_stats, quick_create_task, pending_tasks_count, get_all_users_for_tasks,
    dynamic_table_api_list, dynamic_table_api_detail, my_pending_work_orders
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
    
    # URLs de usuarios activos
    path('active-users/count/', active_users_count, name='api-active-users-count'),
    path('active-users/', active_users_list, name='api-active-users-list'),
    
    # URLs de eventos
    path('upcoming-events/', upcoming_events_list, name='api-upcoming-events-list'),
    
    # URLs de órdenes de trabajo
    path('my-pending-work-orders/', my_pending_work_orders, name='api-my-pending-work-orders'),
    
    # URLs de tickets
    path('open-tickets/count/', open_tickets_count, name='api-open-tickets-count'),
    
    # URLs de chat directo con IA
    path('ai-chat/direct/', direct_ai_chat, name='api-direct-ai-chat'),
    
    # URL para información del sistema
    path('system-info/', system_info_api, name='api-system-info'),
    
    # URL para estadísticas de URLs cortas
    path('short-urls/stats/', short_url_stats_api, name='api-short-url-stats'),
    
    # URL para tracking de contadores web (sin autenticación)
    path('web-counter/track/', web_counter_track, name='api-web-counter-track'),
    path('web-counter/stats/<str:token>/', web_counter_stats, name='api-web-counter-stats'),
    
    # URLs para tareas rápidas
    path('tasks/quick-create/', quick_create_task, name='api-quick-create-task'),
    path('tasks/pending-count/', pending_tasks_count, name='api-pending-tasks-count'),
    path('tasks/users/', get_all_users_for_tasks, name='api-get-all-users-for-tasks'),
    
    # URLs para Tablas Dinámicas API (sin autenticación - usa token de tabla)
    path('dynamic-tables/<str:table_name>/', dynamic_table_api_list, name='api-dynamic-table-list'),
    path('dynamic-tables/<str:table_name>/<int:record_id>/', dynamic_table_api_detail, name='api-dynamic-table-detail'),
]

# Django espera que la variable se llame urlpatterns
urlpatterns = api_urlpatterns