from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # URLs de tickets
    path('tickets/', views.ticket_list_view, name='ticket_list'),
    path('tickets/create/', views.ticket_create_view, name='ticket_create'),
    path('tickets/<int:pk>/', views.ticket_detail_view, name='ticket_detail'),
    path('tickets/<int:pk>/edit/', views.ticket_edit_view, name='ticket_edit'),
    path('tickets/<int:pk>/delete/', views.ticket_delete_view, name='ticket_delete'),
    path('tickets/<int:pk>/unassign/', views.unassign_ticket_view, name='unassign_ticket'),
    
    # URL para vista pública de tickets (sin autenticación requerida)
    path('public/<uuid:token>/', views.public_ticket_view, name='public_ticket'),
    
    # URLs de categorías (solo para agentes)
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/create/', views.category_create_view, name='category_create'),
    path('categories/<int:pk>/', views.category_detail_view, name='category_detail'),
    path('categories/<int:pk>/edit/', views.category_edit_view, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete_view, name='category_delete'),
    
    # URLs de proyectos (solo para agentes)
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:project_id>/delete/', views.project_delete, name='project_delete'),
    path('projects/<int:project_id>/generate-public-token/', views.project_generate_public_token, name='project_generate_public_token'),
    
    # URLs de adjuntos
    path('attachments/<int:attachment_id>/download/', views.download_attachment_view, name='download_attachment'),
    path('attachments/<int:attachment_id>/delete/', views.delete_attachment_view, name='delete_attachment'),
    
    # URLs de autenticación
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # URL para perfil de usuario
    path('profile/', views.user_profile_view, name='user_profile'),
    
    # URLs de notas internas (solo para agentes)
    path('notes/', views.notes_list_view, name='notes_list'),
    path('notes/create/', views.note_create_view, name='note_create'),
    path('notes/<int:note_id>/', views.note_detail_view, name='note_detail'),
    path('notes/<int:note_id>/edit/', views.note_edit_view, name='note_edit'),
    path('notes/<int:note_id>/delete/', views.note_delete_view, name='note_delete'),
    
    # URL para ver notas de un usuario específico
    path('users/<int:user_id>/notes/', views.user_notes_view, name='user_notes'),
    path('my-notes/', views.user_notes_view, name='my_notes'),
    
    # URLs de gestión de usuarios (solo para agentes)
    path('users/', views.user_management_view, name='user_management'),
    path('users/create/', views.user_create_view, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit_view, name='user_edit'),
    path('users/<int:user_id>/toggle-status/', views.user_toggle_status_view, name='user_toggle_status'),
    
    # API para obtener tickets de usuario (AJAX)
    path('api/user-tickets/<int:user_id>/', views.api_user_tickets, name='api_user_tickets'),
    
    # URLs para Control de Horario (solo para agentes)
    path('time-clock/', views.time_clock_view, name='time_clock'),
    path('time-clock/start/', views.time_start_work, name='time_start_work'),
    path('time-clock/end/', views.time_end_work, name='time_end_work'),
    path('time-entries/', views.time_entries_list, name='time_entries_list'),
    path('time-entries/<int:entry_id>/', views.time_entry_detail, name='time_entry_detail'),
    path('time-entries/<int:entry_id>/edit/', views.time_entry_edit, name='time_entry_edit'),
    
    # Control de asistencia general (para agentes)
    path('attendance/', views.attendance_overview, name='attendance_overview'),
    
    # API AJAX para estado de tiempo actual
    path('api/time-status/', views.ajax_current_time_status, name='ajax_time_status'),
    
    # URLs de gestión de empresas (solo para agentes)
    path('companies/', views.company_list_view, name='company_list'),
    path('companies/create/', views.company_create_view, name='company_create'),
    path('companies/<int:company_id>/', views.company_detail_view, name='company_detail'),
    path('companies/<int:company_id>/edit/', views.company_edit_view, name='company_edit'),
    path('companies/<int:company_id>/delete/', views.company_delete_view, name='company_delete'),
    
    # URL de configuración del sistema (solo para agentes)
    path('system/configuration/', views.system_configuration_view, name='system_configuration'),
    
    # URLs de gestión de documentos (solo para agentes)
    path('documents/', views.document_list_view, name='document_list'),
    path('documents/create/', views.document_create_view, name='document_create'),
    path('documents/<int:document_id>/', views.document_detail_view, name='document_detail'),
    path('documents/<int:document_id>/edit/', views.document_edit_view, name='document_edit'),
    path('documents/<int:document_id>/delete/', views.document_delete_view, name='document_delete'),
    path('documents/<int:document_id>/download/', views.document_download_private_view, name='document_download_private'),
    
    # URLs públicas para compartir documentos (sin autenticación)
    path('document/public/<uuid:token>/', views.document_public_view, name='document_public'),
    path('document/download/<uuid:token>/', views.document_download_view, name='document_download'),
    
    # URLs de gestión de URLs con credenciales (solo para agentes)
    path('urls/', views.url_manager_list_view, name='url_manager_list'),
    path('urls/create/', views.url_manager_create_view, name='url_manager_create'),
    path('urls/<int:url_id>/', views.url_manager_detail_view, name='url_manager_detail'),
    path('urls/<int:url_id>/edit/', views.url_manager_edit_view, name='url_manager_edit'),
    path('urls/<int:url_id>/delete/', views.url_manager_delete_view, name='url_manager_delete'),
    path('urls/<int:url_id>/password/', views.url_manager_password_view, name='url_manager_password'),
    
    # URLs de gestión de órdenes de trabajo (solo para agentes)
    path('work-orders/', views.work_order_list_view, name='work_order_list'),
    path('work-orders/create/', views.work_order_create_view, name='work_order_create'),
    path('work-orders/<int:pk>/', views.work_order_detail_view, name='work_order_detail'),
    path('work-orders/<int:pk>/edit/', views.work_order_edit_view, name='work_order_edit'),
    path('work-orders/<int:pk>/delete/', views.work_order_delete_view, name='work_order_delete'),
    path('work-orders/<int:pk>/change-status/', views.work_order_change_status_view, name='work_order_change_status'),
    
    # URL pública para órdenes de trabajo compartidas (sin autenticación)
    path('work-order/public/<uuid:token>/', views.work_order_public_view, name='public_work_order'),
    
    # URLs de reportes (solo para agentes)
    path('reports/daily/', views.daily_report_view, name='daily_report'),
    path('reports/daily/pdf/', views.daily_report_pdf, name='daily_report_pdf'),
    
    # URLs de gestión de tareas
    path('tasks/', views.task_list_view, name='task_list'),
    path('tasks/create/', views.task_create_view, name='task_create'),
    path('tasks/<int:pk>/', views.task_detail_view, name='task_detail'),
    path('tasks/<int:pk>/edit/', views.task_edit_view, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task_delete_view, name='task_delete'),
    path('tasks/<int:pk>/toggle-status/', views.task_toggle_status_view, name='task_toggle_status'),
    
    # URLs de control diario de tareas
    path('task-control/', views.task_control_dashboard, name='task_control_dashboard'),
    path('task-control/<int:pk>/complete/', views.task_control_complete, name='task_control_complete'),
    path('task-control/<int:pk>/start/', views.task_control_start, name='task_control_start'),
    path('task-control/<int:pk>/pause/', views.task_control_pause, name='task_control_pause'),
    
    # URLs de gestión diaria de tareas
    path('daily-tasks/', views.daily_task_management, name='daily_task_management'),
    path('daily-tasks/create/', views.create_task_session, name='create_task_session'),
    path('daily-tasks/view/<int:session_id>/', views.view_task_session, name='view_task_session'),
    path('daily-tasks/delete/<int:session_id>/', views.delete_task_session, name='delete_task_session'),
    path('daily-tasks/toggle/<int:item_id>/', views.toggle_daily_task_completion, name='toggle_daily_task_completion'),
    path('daily-tasks/history/', views.daily_task_history, name='daily_task_history'),
    
    # URLs públicas para gestión de tareas (sin autenticación)
    path('public/tasks/<uuid:token>/', views.public_task_view, name='public_task_view'),
    
    # URL pública para información del proyecto (sin autenticación)
    path('public/project/<str:token>/', views.public_project_view, name='public_project_view'),
]
