from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # URLs de tickets
    path('ticket-show-chart/', views.ticket_chart, name='ticket_chart'),
    path('tickets/', views.ticket_list_view, name='ticket_list'),
    path('tickets/export/excel/', views.ticket_export_excel, name='ticket_export_excel'),
    path('tickets/create/', views.ticket_create_view, name='ticket_create'),
    path('tickets/import/', views.ticket_import_view, name='ticket_import'),
    path('tickets/import/example/', views.ticket_import_example, name='ticket_import_example'),
    path('tickets/<int:pk>/', views.ticket_detail_view, name='ticket_detail'),
    path('tickets/<int:pk>/edit/', views.ticket_edit_view, name='ticket_edit'),
    path('tickets/<int:pk>/delete/', views.ticket_delete_view, name='ticket_delete'),
    path('tickets/<int:pk>/approve/', views.ticket_approve_view, name='ticket_approve'),
    path('tickets/<int:pk>/unassign/', views.unassign_ticket_view, name='unassign_ticket'),
    
    # URLs para impresión de tickets
    path('tickets/print-preview/<int:ticket_id>/', views.ticket_print_preview, name='ticket_print_preview'),
    path('tickets/print/<int:ticket_id>/', views.ticket_print, name='ticket_print'),
    path('tickets/<int:pk>/pdf/', views.ticket_print_pdf, name='ticket_print_pdf'),
    
    # URL para exportación múltiple de tickets a PDF
    path('tickets/export/pdf/', views.tickets_export_pdf, name='tickets_export_pdf'),
    
    # URL AJAX para obtener IDs de tickets filtrados
    path('tickets/filtered-ids/', views.get_filtered_ticket_ids, name='get_filtered_ticket_ids'),
    
    # URLs de TODO List para tickets - COMENTADAS TEMPORALMENTE
    # path('tickets/<int:pk>/todo/add/', views.ticket_todo_add, name='ticket_todo_add'),
    # path('tickets/<int:pk>/todo/<int:item_id>/toggle/', views.ticket_todo_toggle, name='ticket_todo_toggle'),
    # path('tickets/<int:pk>/todo/<int:item_id>/delete/', views.ticket_todo_delete, name='ticket_todo_delete'),
    # path('tickets/<int:pk>/todo/generate-ai/', views.ticket_todo_generate_ai, name='ticket_todo_generate_ai'),
    
    # URLs públicas de cursos (sin autenticación) - DEBEN IR ANTES que la ruta genérica de tickets
    path('public/courses/<uuid:token>/', views.course_public, name='course_public'),
    path('public/courses/<uuid:token>/classes/<int:class_id>/', views.course_class_public, name='course_class_public'),
    
    # Vista pública de conceptos (sin autenticación requerida)
    path('public/concepts/', views.public_concepts_view, name='public_concepts'),
    
    # URL para vista pública de tickets (sin autenticación requerida)
    path('public/<uuid:token>/', views.public_ticket_view, name='public_ticket'),
    path('public/<uuid:token>/approve/', views.public_ticket_approve, name='public_ticket_approve'),
    path('public/<uuid:token>/survey/', views.public_ticket_survey, name='public_ticket_survey'),
    path('public/<uuid:token>/upload/', views.public_ticket_upload, name='public_ticket_upload'),
    
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
    path('projects/<int:project_id>/duplicate/', views.project_duplicate, name='project_duplicate'),
    path('projects/<int:project_id>/generate-public-token/', views.project_generate_public_token, name='project_generate_public_token'),
    
    # URLs de productos (solo para agentes)
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    
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
    path('notes/<int:note_id>/pdf/', views.note_pdf_view, name='note_pdf'),
    
    # URLs para compartir notas
    path('notes/<int:note_id>/generate-share-link/', views.note_generate_share_link, name='note_generate_share_link'),
    path('notes/<int:note_id>/disable-sharing/', views.note_disable_sharing, name='note_disable_sharing'),
    path('notes/<int:note_id>/regenerate-share-link/', views.note_regenerate_share_link, name='note_regenerate_share_link'),
    
    # URLs públicas para notas compartidas (sin login)
    path('shared/note/<str:token>/', views.shared_note_view, name='shared_note'),
    path('shared/note/<str:token>/pdf/', views.shared_note_pdf, name='shared_note_pdf'),
    
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
    path('time-entries/export/excel/', views.time_entries_export_excel, name='time_entries_export_excel'),
    path('time-entries/<int:entry_id>/', views.time_entry_detail, name='time_entry_detail'),
    path('time-entries/<int:entry_id>/edit/', views.time_entry_edit, name='time_entry_edit'),
    path('time-entries/<int:entry_id>/audit/', views.time_entry_audit_log, name='time_entry_audit_log'),
    
    # URLs públicas de control de horario (sin login)
    path('public-time/<str:token>/', views.public_time_clock, name='public_time_clock'),
    
    # Gestión de accesos públicos de horario (solo agentes)
    path('public-time-access/', views.public_time_access_list, name='public_time_access_list'),
    path('public-time-access/create/<int:user_id>/', views.public_time_access_create, name='public_time_access_create'),
    path('public-time-access/<int:access_id>/edit/', views.public_time_access_edit, name='public_time_access_edit'),
    path('public-time-access/<int:access_id>/delete/', views.public_time_access_delete, name='public_time_access_delete'),
    
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
    
    # URLs de Generador de Libros con IA (solo para agentes)
    path('ai-books/', views.ai_book_list, name='ai_book_list'),
    path('ai-books/create/', views.ai_book_create, name='ai_book_create'),
    path('ai-books/<int:pk>/', views.ai_book_detail, name='ai_book_detail'),
    path('ai-books/<int:pk>/edit/', views.ai_book_edit, name='ai_book_edit'),
    path('ai-books/<int:pk>/delete/', views.ai_book_delete, name='ai_book_delete'),
    path('ai-books/<int:pk>/export/', views.ai_book_export, name='ai_book_export'),
    path('ai-books/<int:pk>/propose-chapters/', views.ai_book_propose_chapters, name='ai_book_propose_chapters'),
    path('ai-books/<int:pk>/generate-chapters/', views.ai_book_generate_chapters_ai, name='ai_book_generate_chapters_ai'),
    path('ai-books/<int:pk>/chapters/<int:chapter_id>/', views.ai_book_chapter_detail, name='ai_book_chapter_detail'),
    path('ai-books/<int:pk>/chapters/<int:chapter_id>/edit-title/', views.ai_book_chapter_edit_title, name='ai_book_chapter_edit_title'),
    path('ai-books/<int:pk>/chapters/<int:chapter_id>/delete/', views.ai_book_chapter_delete, name='ai_book_chapter_delete'),
    path('ai-books/<int:pk>/chapters/<int:chapter_id>/generate-summary/', views.ai_book_chapter_generate_summary, name='ai_book_chapter_generate_summary'),
    path('ai-books/<int:pk>/chapters/<int:chapter_id>/generate-content/', views.ai_book_chapter_generate_content, name='ai_book_chapter_generate_content'),
    path('ai-books/<int:pk>/chapters/<int:chapter_id>/save-content/', views.ai_book_chapter_save_content, name='ai_book_chapter_save_content'),
    path('ai-books/<int:pk>/chapters/<int:chapter_id>/save-summary/', views.ai_book_chapter_save_summary, name='ai_book_chapter_save_summary'),
    
    # URLs de Generador de Artículos con IA (solo para agentes)
    path('ai-articles/', views.ai_article_project_list, name='ai_article_project_list'),
    path('ai-articles/create/', views.ai_article_project_create, name='ai_article_project_create'),
    path('ai-articles/<int:pk>/proposals/', views.ai_article_project_proposals, name='ai_article_project_proposals'),
    path('ai-articles/<int:pk>/edit/', views.ai_article_project_edit, name='ai_article_project_edit'),
    path('ai-articles/<int:pk>/generate-proposals/', views.ai_article_generate_proposals, name='ai_article_generate_proposals'),
    path('ai-articles/<int:pk>/delete/', views.ai_article_project_delete, name='ai_article_project_delete'),
    path('ai-articles/<int:pk>/<int:article_id>/', views.ai_article_detail, name='ai_article_detail'),
    path('ai-articles/<int:pk>/<int:article_id>/edit-keywords/', views.ai_article_edit_keywords, name='ai_article_edit_keywords'),
    path('ai-articles/<int:pk>/<int:article_id>/generate-content/', views.ai_article_generate_content, name='ai_article_generate_content'),
    path('ai-articles/<int:pk>/<int:article_id>/delete/', views.ai_article_delete, name='ai_article_delete'),
    
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
    
    # URLs de gestión de tareas en órdenes de trabajo (solo para agentes)
    path('work-orders/<int:work_order_pk>/tasks/', views.work_order_task_list_view, name='work_order_task_list'),
    path('work-orders/<int:work_order_pk>/tasks/create/', views.work_order_task_create_view, name='work_order_task_create'),
    path('work-orders/<int:work_order_pk>/tasks/bulk-create/', views.work_order_task_bulk_create_view, name='work_order_task_bulk_create'),
    path('work-orders/<int:work_order_pk>/tasks/<int:task_pk>/edit/', views.work_order_task_edit_view, name='work_order_task_edit'),
    path('work-orders/<int:work_order_pk>/tasks/<int:task_pk>/delete/', views.work_order_task_delete_view, name='work_order_task_delete'),
    path('work-orders/<int:work_order_pk>/tasks/<int:task_pk>/status/', views.work_order_task_status_update_view, name='work_order_task_status_update'),
    path('work-orders/<int:work_order_pk>/tasks/<int:task_pk>/time/start/', views.work_order_task_time_start_view, name='work_order_task_time_start'),
    path('work-orders/<int:work_order_pk>/tasks/<int:task_pk>/time/stop/', views.work_order_task_time_stop_view, name='work_order_task_time_stop'),
    
    # URL pública para órdenes de trabajo compartidas (sin autenticación)
    path('work-order/public/<uuid:token>/', views.work_order_public_view, name='public_work_order'),
    path('work-order/public/<uuid:token>/tasks/', views.work_order_public_task_view, name='public_work_order_tasks'),
    path('work-order/public/<uuid:token>/tasks/<int:task_pk>/time/start/', views.work_order_public_task_time_start_view, name='public_work_order_task_time_start'),
    path('work-order/public/<uuid:token>/tasks/<int:task_pk>/time/stop/', views.work_order_public_task_time_stop_view, name='public_work_order_task_time_stop'),
    
    # URLs de reportes (solo para agentes)
    path('reports/daily/', views.daily_report_view, name='daily_report'),
    path('reports/daily/pdf/', views.daily_report_pdf, name='daily_report_pdf'),
    
    # URLs de herramientas PDF (solo para agentes)
    path('tools/pdf/get-pages/', views.pdf_get_pages_view, name='pdf_get_pages'),
    path('tools/pdf/join/', views.pdf_join_view, name='pdf_join'),
    path('tools/pdf/split/', views.pdf_split_view, name='pdf_split'),
    
    # URLs de herramientas calculadora (solo para agentes)
    path('tools/calculator/', views.calculator_view, name='calculator'),
    
    # URLs de herramientas color picker (solo para agentes)
    path('tools/color-picker/', views.color_picker_view, name='color_picker'),
    
    # URLs de herramientas comandos (solo para agentes)
    path('tools/commands/', views.command_library_view, name='command_library'),
    path('tools/commands/create/', views.command_create_view, name='command_create'),
    path('tools/commands/<int:pk>/', views.command_detail_view, name='command_detail'),
    path('tools/commands/<int:pk>/edit/', views.command_edit_view, name='command_edit'),
    path('tools/commands/<int:pk>/delete/', views.command_delete_view, name='command_delete'),
    path('tools/commands/<int:pk>/copy/', views.command_copy_view, name='command_copy'),
    path('tools/commands/<int:pk>/toggle-favorite/', views.command_toggle_favorite_view, name='command_toggle_favorite'),
    
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
    
    # URLs del sistema de chat
    path('chat/', views.chat_list_view, name='chat_list'),
    path('chat/room/<int:room_id>/', views.chat_room_view, name='chat_room'),
    path('chat/start/<int:user_id>/', views.chat_start_conversation, name='chat_start'),
    path('chat/create-group/', views.chat_create_group, name='chat_create_group'),
    path('chat/users/', views.chat_users_list, name='chat_users'),
    
    # URLs AJAX para el chat
    path('chat/ajax/messages/<int:room_id>/', views.chat_ajax_load_messages, name='chat_ajax_messages'),
    path('chat/ajax/send/<int:room_id>/', views.chat_ajax_send_message, name='chat_ajax_send'),
    
    # URLs de formulario de contacto público
    path('contact/<uuid:token>/', views.public_contact_form_view, name='public_contact_form'),
    path('contact/success/', views.contact_form_success, name='contact_form_success'),
    
    # URLs de gestión de formularios de contacto (para el propietario)
    path('contact-submissions/', views.contact_submissions_list, name='contact_submissions_list'),
    path('contact-submissions/<int:pk>/', views.contact_submission_detail, name='contact_submission_detail'),
    path('contact-submissions/<int:pk>/approve/', views.contact_submission_approve, name='contact_submission_approve'),
    path('contact-submissions/<int:pk>/reject/', views.contact_submission_reject, name='contact_submission_reject'),
    
    # URLs de juegos (solo para agentes)
    path('games/tetris/', views.tetris_view, name='tetris'),
    
    # URL pública para estadísticas de empresa
    path('company/stats/<str:token>/', views.public_company_stats, name='public_company_stats'),
    
    # ============= URLs CONTACTOS =============
    path('contacts/', views.contact_list, name='contact_list'),
    path('contacts/chart/', views.contact_chart, name='contact_chart'),
    path('contacts/create/', views.contact_create, name='contact_create'),
    path('contacts/<int:pk>/', views.contact_detail, name='contact_detail'),
    path('contacts/<int:pk>/edit/', views.contact_edit, name='contact_edit'),
    path('contacts/<int:pk>/delete/', views.contact_delete, name='contact_delete'),
    
    # URLs para comentarios de contactos
    path('contact-comments/<int:pk>/delete/', views.contact_comment_delete, name='contact_comment_delete'),
    
    # URLs para adjuntos de contactos
    path('contact-attachments/<int:pk>/delete/', views.contact_attachment_delete, name='contact_attachment_delete'),
    path('contact-attachments/<int:pk>/download/', views.contact_attachment_download, name='contact_attachment_download'),
    
    # URL para crear actividad desde contacto
    path('contacts/<int:contact_id>/create-activity/', views.activity_create_from_contact, name='activity_create_from_contact'),
    
    # URL para crear actividad rápida desde contacto (AJAX)
    path('contacts/<int:contact_id>/quick-activity/', views.create_quick_activity, name='create_quick_activity'),
    
    # ============= URLs CRM =============
    path('crm/', views.crm_dashboard, name='crm_dashboard'),
    path('crm/opportunities/', views.opportunity_list, name='opportunity_list'),
    path('crm/opportunities/create/', views.opportunity_create, name='opportunity_create'),
    path('crm/opportunities/<int:pk>/', views.opportunity_detail, name='opportunity_detail'),
    path('crm/opportunities/<int:pk>/edit/', views.opportunity_edit, name='opportunity_edit'),
    path('crm/opportunities/<int:pk>/delete/', views.opportunity_delete, name='opportunity_delete'),
    path('crm/opportunities/<int:pk>/add-note/', views.opportunity_add_note, name='opportunity_add_note'),
    
    # URLs de actividades de oportunidades
    path('crm/opportunities/<int:opportunity_id>/activities/create/', views.opportunity_activity_create, name='opportunity_activity_create'),
    path('crm/opportunities/<int:opportunity_id>/activities/', views.opportunity_activity_list, name='opportunity_activity_list'),
    path('crm/activities/<int:pk>/', views.opportunity_activity_detail, name='opportunity_activity_detail'),
    path('crm/activities/<int:pk>/edit/', views.opportunity_activity_edit, name='opportunity_activity_edit'),
    path('crm/activities/<int:pk>/complete/', views.opportunity_activity_complete, name='opportunity_activity_complete'),
    path('crm/activities/<int:pk>/delete/', views.opportunity_activity_delete, name='opportunity_activity_delete'),
    path('crm/my-activities/', views.my_activities_dashboard, name='my_activities_dashboard'),
    path('crm/activities/create/', views.activity_create_standalone, name='activity_create_standalone'),
    
    # API para actividades pendientes
    path('api/user-activities/pending/', views.api_user_activities_pending, name='api_user_activities_pending'),
    
    # API para calendario de actividades
    path('api/activities/calendar/', views.api_activities_calendar, name='api_activities_calendar'),
    
    # URLs de gestión de estados CRM (solo para agentes)
    path('crm/status/', views.opportunity_status_list, name='opportunity_status_list'),
    path('crm/status/create/', views.opportunity_status_create, name='opportunity_status_create'),
    path('crm/status/<int:pk>/edit/', views.opportunity_status_edit, name='opportunity_status_edit'),
    path('crm/status/<int:pk>/delete/', views.opportunity_status_delete, name='opportunity_status_delete'),
    
    # URLs de Preguntas CRM
    path('crm/questions/', views.crm_questions_list, name='crm_questions_list'),
    path('crm/questions/create/', views.crm_question_create, name='crm_question_create'),
    path('crm/questions/<int:pk>/', views.crm_question_detail, name='crm_question_detail'),
    path('crm/questions/<int:pk>/edit/', views.crm_question_edit, name='crm_question_edit'),
    path('crm/questions/<int:pk>/delete/', views.crm_question_delete, name='crm_question_delete'),
    
    # URLs de Reuniones
    path('meetings/', views.meeting_list_view, name='meeting_list'),
    path('meetings/create/', views.meeting_create_view, name='meeting_create'),
    path('meetings/<int:pk>/', views.meeting_detail_view, name='meeting_detail'),
    path('meetings/<int:pk>/edit/', views.meeting_edit_view, name='meeting_edit'),
    path('meetings/<int:pk>/delete/', views.meeting_delete_view, name='meeting_delete'),
    path('meetings/<int:pk>/print/', views.meeting_print_view, name='meeting_print'),
    path('meetings/<int:pk>/pdf/', views.meeting_pdf_download_view, name='meeting_pdf_download'),
    path('meetings/<int:pk>/questions/', views.meeting_questions_view, name='meeting_questions'),
    path('meetings/<int:pk>/attendees/', views.meeting_attendees_view, name='meeting_attendees'),
    
    # URLs de Reuniones Soporte
    path('support-meetings/', views.support_meeting_list, name='support_meeting_list'),
    path('support-meetings/create/', views.support_meeting_create, name='support_meeting_create'),
    path('support-meetings/<int:pk>/', views.support_meeting_detail, name='support_meeting_detail'),
    path('support-meetings/<int:pk>/edit/', views.support_meeting_edit, name='support_meeting_edit'),
    path('support-meetings/<int:pk>/delete/', views.support_meeting_delete, name='support_meeting_delete'),
    path('support-meetings/<int:pk>/create-tickets/', views.support_meeting_create_tickets, name='support_meeting_create_tickets'),
    path('support-meetings/<int:pk>/generate-link/', views.support_meeting_generate_public_link, name='support_meeting_generate_link'),
    path('support-meetings/<int:pk>/disable-link/', views.support_meeting_disable_public_link, name='support_meeting_disable_link'),
    path('support-meetings/<int:meeting_pk>/points/<int:point_pk>/edit/', views.support_meeting_point_edit, name='support_meeting_point_edit'),
    path('support-meetings/<int:meeting_pk>/points/<int:point_pk>/delete/', views.support_meeting_point_delete, name='support_meeting_point_delete'),
    
    # URLs públicas de reuniones de soporte (sin autenticación)
    path('support/meeting/<str:token>/', views.support_meeting_public, name='support_meeting_public'),
    
    # URLs públicas de reuniones (sin autenticación)
    path('meetings/public/<str:token>/', views.meeting_public_view, name='meeting_public'),
    path('meetings/public/<str:token>/register/', views.meeting_register_view, name='meeting_register'),
    path('meetings/public/<str:token>/questions/', views.meeting_questions_public_view, name='meeting_questions_public'),
    
    # URLs de Cotizaciones
    path('quotations/', views.quotation_list_view, name='quotation_list'),
    path('quotations/create/', views.quotation_create_view, name='quotation_create'),
    path('quotations/<int:quotation_id>/', views.quotation_detail_view, name='quotation_detail'),
    path('quotations/<int:quotation_id>/edit/', views.quotation_edit_view, name='quotation_edit'),
    path('quotations/<int:quotation_id>/duplicate/', views.quotation_duplicate_view, name='quotation_duplicate'),
    path('quotations/<int:quotation_id>/delete/', views.quotation_delete_view, name='quotation_delete'),
    path('quotations/<int:quotation_id>/pdf/', views.quotation_pdf_view, name='quotation_pdf'),
    path('quotations/<int:quotation_id>/share/', views.quotation_share_view, name='quotation_share'),
    
    # URLs públicas para cotizaciones (sin autenticación)
    path('quotations/public/<str:token>/', views.quotation_public_view, name='quotation_public_view'),
    path('quotations/public/<str:token>/respond/', views.quotation_public_respond_view, name='quotation_public_respond'),
    
    # URLs para plantillas de cotización
    path('quotations/templates/', views.quotation_template_list_view, name='quotation_template_list'),
    path('quotations/templates/new/', views.quotation_template_create_new_view, name='quotation_template_create_new'),
    path('quotations/templates/requests/', views.quotation_template_requests_view, name='quotation_template_requests'),
    path('quotations/templates/<int:template_id>/', views.quotation_template_detail_view, name='quotation_template_detail'),
    path('quotations/templates/<int:template_id>/edit/', views.quotation_template_edit_view, name='quotation_template_edit'),
    path('quotations/templates/<int:template_id>/delete/', views.quotation_template_delete_view, name='quotation_template_delete'),
    path('quotations/templates/<int:template_id>/toggle/', views.quotation_template_toggle_active_view, name='quotation_template_toggle_active'),
    path('quotations/<int:quotation_id>/create-template/', views.quotation_template_create_view, name='quotation_template_create'),
    
    # URL pública para formulario de plantilla (sin autenticación)
    path('quotations/template/<str:token>/', views.quotation_template_public_form_view, name='quotation_template_public_form'),
    
    # URLs AJAX para líneas de cotización
    path('quotations/<int:quotation_id>/add-line/', views.quotation_add_line_view, name='quotation_add_line'),
    path('quotations/<int:quotation_id>/remove-line/<int:line_id>/', views.quotation_remove_line_view, name='quotation_remove_line'),
    path('quotations/<int:quotation_id>/edit-line/<int:line_id>/', views.quotation_edit_line_view, name='quotation_edit_line'),
    path('quotations/<int:quotation_id>/lines/', views.quotation_get_lines_view, name='quotation_get_lines'),
    path('ajax/products/', views.get_products_ajax_view, name='get_products_ajax'),
    path('meetings/public/<str:token>/ask/', views.meeting_ask_question_view, name='meeting_ask_question'),
    
    # AJAX para reuniones
    path('meetings/<int:pk>/questions/<int:question_id>/answer/', views.meeting_answer_question_view, name='meeting_answer_question'),
    
    # URLs de Capacitación (Cursos y Clases)
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    path('courses/<int:pk>/generate-public-token/', views.course_generate_public_token, name='course_generate_public_token'),
    path('courses/<int:pk>/disable-public-access/', views.course_disable_public_access, name='course_disable_public_access'),
    
    # URLs de Clases de Curso
    path('courses/<int:course_id>/classes/create/', views.course_class_create, name='course_class_create'),
    path('courses/<int:course_id>/classes/<int:pk>/', views.course_class_detail, name='course_class_detail'),
    path('courses/<int:course_id>/classes/<int:pk>/edit/', views.course_class_edit, name='course_class_edit'),
    path('courses/<int:course_id>/classes/<int:pk>/delete/', views.course_class_delete, name='course_class_delete'),
    
    # AJAX para marcar clases como vistas
    path('courses/<int:course_id>/classes/<int:class_id>/mark-viewed/', views.mark_class_as_viewed, name='mark_class_as_viewed'),
    
    # URLs de Registro Público de Cursos
    path('courses/<int:pk>/generate-registration-token/', views.course_generate_registration_token, name='course_generate_registration_token'),
    path('courses/<int:pk>/registration-tokens/', views.course_registration_tokens_list, name='course_registration_tokens_list'),
    path('courses/<int:pk>/registration-tokens/<int:token_id>/disable/', views.course_disable_registration_token, name='course_disable_registration_token'),
    path('course-register/<uuid:token>/', views.course_public_register, name='course_public_register'),
    
    # URL de debug para cursos
    path('debug/user-access/', views.debug_user_access, name='debug_user_access'),
    
    # URLs del Blog
    # URLs públicas del blog (sin autenticación)
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_post_detail, name='blog_post_detail'),
    
    # URLs de administración del blog (con autenticación)
    path('blog-admin/', views.blog_post_list_admin, name='blog_post_list_admin'),
    path('blog-admin/post/create/', views.blog_post_create, name='blog_post_create'),
    path('blog-admin/post/<int:pk>/', views.blog_post_detail_admin, name='blog_post_detail_admin'),
    path('blog-admin/post/<int:pk>/edit/', views.blog_post_edit, name='blog_post_edit'),
    path('blog-admin/post/<int:pk>/toggle-status/', views.blog_post_toggle_status, name='blog_post_toggle_status'),
    path('blog-admin/post/<int:pk>/delete/', views.blog_post_delete, name='blog_post_delete'),
    
    # URLs de categorías de blog (con autenticación)
    path('blog-admin/categories/', views.blog_category_list, name='blog_category_list'),
    path('blog-admin/categories/create/', views.blog_category_create, name='blog_category_create'),
    
    # URLs de comentarios de blog (con autenticación)
    path('blog-admin/comments/<int:pk>/approve/', views.blog_comment_approve, name='blog_comment_approve'),
    path('blog-admin/comments/<int:pk>/delete/', views.blog_comment_delete, name='blog_comment_delete'),
    
    # URLs de IA para Blog (con autenticación)
    path('blog-admin/post/<int:pk>/ai/improve-content/', views.blog_ai_improve_content, name='blog_ai_improve_content'),
    path('blog-admin/post/<int:pk>/ai/improve-complete/', views.blog_ai_improve_complete_article, name='blog_ai_improve_complete_article'),
    path('blog-admin/post/<int:pk>/ai/generate-meta/', views.blog_ai_generate_meta_description, name='blog_ai_generate_meta_description'),
    path('blog-admin/post/<int:pk>/ai/suggest-titles/', views.blog_ai_suggest_titles, name='blog_ai_suggest_titles'),
    path('blog-admin/post/<int:pk>/ai/generate-tags/', views.blog_ai_generate_tags, name='blog_ai_generate_tags'),
    path('blog-admin/post/<int:pk>/ai/analyze-readability/', views.blog_ai_analyze_readability, name='blog_ai_analyze_readability'),
    path('blog-admin/post/<int:pk>/ai/generate-image/', views.blog_ai_generate_image, name='blog_ai_generate_image'),
    path('blog-admin/post/<int:pk>/ai/apply-improvements/', views.blog_ai_apply_improvements, name='blog_ai_apply_improvements'),
    path('blog-admin/ai/test-connection/', views.blog_ai_test_connection, name='blog_ai_test_connection'),
    
    # URLs de Chat con IA
    path('ai-chat/', views.ai_chat_list_view, name='ai_chat_list'),
    path('ai-chat/<int:session_id>/', views.ai_chat_session_view, name='ai_chat_session'),
    path('ai-chat/<int:session_id>/delete/', views.ai_chat_delete_session_view, name='ai_chat_delete_session'),
    path('ai-chat-debug/<int:session_id>/', views.ai_chat_debug_view, name='ai_chat_debug'),
    path('ai-chat-simple/<int:session_id>/', views.ai_chat_simple_view, name='ai_chat_simple'),
    path('ai-chat-live/<int:session_id>/', views.ai_chat_live_view, name='ai_chat_live'),
    path('ai-chat-modern/<int:session_id>/', views.ai_chat_modern_view, name='ai_chat_modern'),
    
    # AJAX para Chat IA
    path('ai-chat/<int:session_id>/send/', views.ai_chat_ajax_send_message, name='ai_chat_ajax_send'),
    
    # AJAX para mejorar tickets con IA
    path('tickets/<int:ticket_id>/improve-ai/', views.improve_ticket_with_ai, name='improve_ticket_with_ai'),
    
    # AJAX para mejorar texto de ticket durante creación (sin ticket existente)
    path('tickets/improve-text-ai/', views.improve_ticket_text_with_ai, name='improve_ticket_text_with_ai'),
    
    # AJAX para mejorar texto de alcance con IA
    path('alcances/improve-text-ai/', views.improve_alcance_text_with_ai, name='improve_alcance_text_with_ai'),
    
    # AJAX para buscar información de empresa con IA
    path('companies/<int:company_id>/search-ai/', views.search_company_info_with_ai, name='search_company_info_with_ai'),
    
    # AJAX para buscar información de empresa con IA (sin requerir ID)
    path('companies/search-ai/', views.search_company_info_general, name='search_company_info_general'),
    
    # AJAX para mejorar contactos con IA
    path('contacts/<int:contact_id>/enhance-ai/', views.enhance_contact_with_ai, name='enhance_contact_with_ai'),
    
    # URLs de conceptos
    path('concepts/', views.concept_list_view, name='concept_list'),
    path('concepts/create/', views.concept_create_view, name='concept_create'),
    path('concepts/<int:pk>/', views.concept_detail_view, name='concept_detail'),
    path('concepts/<int:pk>/edit/', views.concept_edit_view, name='concept_edit'),
    path('concepts/<int:pk>/delete/', views.concept_delete_view, name='concept_delete'),
    
    # URLs de Exámenes
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/create/', views.exam_create, name='exam_create'),
    path('exams/<int:pk>/', views.exam_detail, name='exam_detail'),
    path('exams/<int:pk>/edit/', views.exam_edit, name='exam_edit'),
    path('exams/<int:pk>/delete/', views.exam_delete, name='exam_delete'),
    path('exams/<int:pk>/take/', views.exam_take_authenticated, name='exam_take_authenticated'),
    path('exams/attempts/', views.exam_attempts_list, name='exam_attempts_list'),
    
    # URLs públicas de exámenes (sin autenticación)
    path('exam/<str:token>/', views.exam_take_public, name='exam_take_public'),
    path('exam/<str:token>/start/', views.exam_take_questions, name='exam_take_questions'),
    path('exam/results/<int:attempt_id>/', views.exam_results, name='exam_results'),
    path('certificate/download/<int:attempt_id>/', views.download_certificate, name='download_certificate'),
    path('certificate/verify/<str:token>/', views.verify_certificate, name='verify_certificate'),
    
    # URLs de preguntas de exámenes
    path('exams/<int:exam_pk>/questions/create/', views.question_create, name='question_create'),
    path('questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
    
    # URLs de contacto web público
    path('contacto/', views.contacto_web, name='contacto_web'),
    path('contactos-web/', views.contactos_web_list, name='contactos_web_list'),
    path('contactos-web/<int:pk>/', views.contacto_web_detail, name='contacto_web_detail'),
    
    # URLs públicas de subida de documentos
    path('public-uploads/', views.public_upload_url_list, name='public_upload_url_list'),
    path('public-uploads/create/', views.public_upload_url_create, name='public_upload_url_create'),
    path('public-uploads/<int:pk>/', views.public_upload_url_detail, name='public_upload_url_detail'),
    path('public-uploads/<int:pk>/toggle/', views.public_upload_url_toggle, name='public_upload_url_toggle'),

    # ============= Generadores de Solicitudes de Empresas =============
    path('generadores-solicitudes/', views.company_request_generator_list, name='company_request_generator_list'),
    path('generadores-solicitudes/create/', views.company_request_generator_create, name='company_request_generator_create'),
    path('generadores-solicitudes/<int:pk>/', views.company_request_generator_detail, name='company_request_generator_detail'),
    path('generadores-solicitudes/<int:pk>/edit/', views.company_request_generator_edit, name='company_request_generator_edit'),
    path('generadores-solicitudes/<int:pk>/delete/', views.company_request_generator_delete, name='company_request_generator_delete'),
    path('generadores-solicitudes/<int:pk>/toggle/', views.company_request_generator_toggle_active, name='company_request_generator_toggle_active'),
    path('generadores-solicitudes/<int:generator_pk>/requests/', views.company_request_list, name='company_request_list'),

    # Ruta pública para enviar solicitudes
    path('company-request/<uuid:token>/', views.company_request_public, name='company_request_public'),
    
    # URL pública para subir documentos (sin autenticación)
    path('upload/<uuid:token>/', views.public_document_upload, name='public_document_upload'),
    
    # URLs de gestión de empleados (en Herramientas) - Mantener compatibilidad
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/change-status/', views.employee_change_status, name='employee_change_status'),
    path('employees/<int:pk>/edit-hiring-opinion/', views.employee_edit_hiring_opinion, name='employee_edit_hiring_opinion'),
    
    # URLs de nóminas de empleados
    path('employees/<int:pk>/payrolls/', views.employee_payroll_list, name='employee_payroll_list'),
    path('employees/<int:pk>/payrolls/create/', views.employee_payroll_create, name='employee_payroll_create'),
    path('employees/<int:employee_pk>/payrolls/<int:payroll_pk>/', views.employee_payroll_detail, name='employee_payroll_detail'),
    path('employees/<int:employee_pk>/payrolls/<int:payroll_pk>/edit/', views.employee_payroll_edit, name='employee_payroll_edit'),
    path('employees/<int:employee_pk>/payrolls/<int:payroll_pk>/delete/', views.employee_payroll_delete, name='employee_payroll_delete'),
    
    # URLs separadas para Candidatos y Empleados
    path('candidates/', views.candidate_list, name='candidate_list'),
    path('candidates/<int:pk>/', views.candidate_detail, name='candidate_detail'),
    path('active-employees/', views.active_employee_list, name='active_employee_list'),
    path('active-employees/<int:pk>/', views.active_employee_detail, name='active_employee_detail'),
    
    # URLs de gestión de enlaces de aplicación de empleo
    path('job-applications/', views.job_application_token_list, name='job_application_token_list'),
    path('job-applications/create/', views.job_application_token_create, name='job_application_token_create'),
    path('job-applications/<int:pk>/', views.job_application_token_detail, name='job_application_token_detail'),
    
    # URL pública para aplicar a empleos (sin autenticación)
    path('job-apply/<uuid:token>/', views.public_job_application, name='public_job_application'),

    # URLs de Acuerdos/Contratos (solo para agentes)
    path('agreements/', views.agreement_list, name='agreement_list'),
    path('agreements/create/', views.agreement_create, name='agreement_create'),
    path('agreements/<int:pk>/', views.agreement_detail, name='agreement_detail'),
    path('agreements/<int:pk>/edit/', views.agreement_edit, name='agreement_edit'),
    path('agreements/<int:pk>/delete/', views.agreement_delete, name='agreement_delete'),
    path('agreements/<int:pk>/publish/', views.agreement_publish, name='agreement_publish'),
    
    # URLs públicas de Acuerdos (sin autenticación)
    path('sign/<str:token>/', views.public_agreement_sign, name='public_agreement_sign'),
    path('sign/<str:token>/success/<int:signature_id>/', views.public_agreement_success, name='public_agreement_success'),
    path('agreement/<str:agreement_token>/download/<int:signature_id>/', views.download_signed_agreement, name='download_signed_agreement'),

    # ============= URLs LANDING PAGES =============
    # URLs de gestión de landing pages (solo para agentes)
    path('landing-pages/', views.landing_page_list, name='landing_page_list'),
    path('landing-pages/create/', views.landing_page_create, name='landing_page_create'),
    path('landing-pages/<int:pk>/', views.landing_page_detail, name='landing_page_detail'),
    path('landing-pages/<int:pk>/edit/', views.landing_page_edit, name='landing_page_edit'),
    path('landing-pages/<int:pk>/delete/', views.landing_page_delete, name='landing_page_delete'),
    path('landing-pages/<int:pk>/submissions/', views.landing_page_submissions, name='landing_page_submissions'),
    path('landing-pages/submissions/<int:submission_id>/', views.landing_page_submission_detail, name='landing_page_submission_detail'),
    path('landing-pages/submissions/<int:submission_id>/toggle-processed/', views.toggle_submission_processed, name='toggle_submission_processed'),
    path('landing-pages/submissions/<int:submission_id>/update-contact-tracking/', views.update_contact_tracking, name='update_contact_tracking'),
    path('landing-pages/contacts/', views.landing_page_contacts, name='landing_page_contacts'),
    path('landing-pages/submissions/<int:submission_id>/create-contact/', views.create_contact_from_submission_view, name='create_contact_from_submission'),
    
    # URLs AJAX para landing pages
    path('ajax/landing-pages/submissions/<int:submission_id>/create-contact/', views.ajax_create_contact_from_submission, name='ajax_create_contact_from_submission'),
    path('ajax/landing-pages/submissions/create-contacts-batch/', views.ajax_create_contacts_batch, name='ajax_create_contacts_batch'),
    path('ajax/landing-pages/submissions/<int:submission_id>/details/', views.ajax_submission_details, name='ajax_submission_details'),
    path('ajax/landing-pages/submissions/<int:submission_id>/delete/', views.ajax_landing_submission_delete, name='ajax_landing_submission_delete'),
    
    # URLs para evaluación IA de landing pages
    path('ai/landing-submissions/', views.landing_submissions_list_view, name='landing_submissions_list'),
    path('ai/landing-submissions/<int:submission_id>/', views.landing_submission_detail_view, name='landing_submission_detail'),
    path('ai/landing-submissions/<int:submission_id>/delete/', views.landing_submission_delete_view, name='landing_submission_delete'),
    path('ai/landing-submissions/<int:submission_id>/evaluate/', views.evaluate_submission_ai_view, name='evaluate_submission_ai'),
    path('ai/landing-submissions/batch-evaluate/', views.batch_evaluate_submissions_view, name='batch_evaluate_submissions'),
    path('ai/dashboard/', views.ai_evaluation_dashboard_view, name='ai_evaluation_dashboard'),
    
    # URL pública de landing page (sin autenticación)
    path('lp/<slug:slug>/', views.landing_page_public, name='landing_page_public'),
    
    # URL pública para crear tickets desde empresa (sin autenticación)
    path('public/company/<uuid:public_token>/create-ticket/', views.public_company_ticket_create, name='public_company_ticket_create'),
    
    # URLs de archivos compartidos
    path('shared-files/', views.shared_files_list_view, name='shared_files_list'),
    path('shared-files/upload/', views.shared_file_upload_view, name='shared_file_upload'),
    path('shared-files/<int:file_id>/', views.shared_file_detail_view, name='shared_file_detail'),
    path('shared-files/<int:file_id>/download/', views.shared_file_download_view, name='shared_file_download'),
    path('shared-files/<int:file_id>/delete/', views.shared_file_delete_view, name='shared_file_delete'),
    path('shared-files/stats/', views.shared_files_stats_view, name='shared_files_stats'),
    
    # URL pública para subir archivos
    path('public/upload-file/', views.public_file_upload_view, name='public_file_upload'),
    
    # URLs de grabaciones
    path('recordings/', views.recordings_list_view, name='recordings_list'),
    path('recordings/upload/', views.recording_upload_view, name='recording_upload'),
    path('recordings/<int:recording_id>/', views.recording_detail_view, name='recording_detail'),
    path('recordings/<int:recording_id>/play/', views.recording_play_view, name='recording_play'),
    path('recordings/<int:recording_id>/delete/', views.recording_delete_view, name='recording_delete'),
    path('recordings/<int:recording_id>/transcribe/', views.recording_transcribe_async_view, name='recording_transcribe'),
    path('recordings/bulk-transcribe/', views.recording_bulk_transcribe_view, name='recording_bulk_transcribe'),
    path('recordings/stats/', views.recordings_stats_view, name='recordings_stats'),
    
    # URL pública para subir grabaciones
    path('public/upload-recording/', views.public_recording_upload_view, name='public_recording_upload'),
    
    # URLs de comandos de voz IA
    path('voice-commands/', views.voice_command_interface_view, name='voice_command_interface'),
    path('voice-commands/create-ticket/', views.voice_command_create_ticket_view, name='voice_command_create_ticket'),
    
    # URLs de Analytics de Páginas Públicas
    path('analytics/page-visits/', views.page_visits_analytics_view, name='page_visits_analytics'),
    path('analytics/page-visits/detail/', views.page_visits_detail_view, name='page_visits_detail'),
    path('analytics/page-visits/export/', views.page_visits_export_view, name='page_visits_export'),
    
    # URLs de Configurador de IA para Blog
    path('ai-blog-configurators/', views.ai_blog_configurators_list_view, name='ai_blog_configurators_list'),
    path('ai-blog-configurators/create/', views.ai_blog_configurator_create_view, name='ai_blog_configurator_create'),
    path('ai-blog-configurators/<int:pk>/edit/', views.ai_blog_configurator_edit_view, name='ai_blog_configurator_edit'),
    path('ai-blog-configurators/<int:pk>/delete/', views.ai_blog_configurator_delete_view, name='ai_blog_configurator_delete'),
    path('ai-blog-configurators/<int:pk>/toggle/', views.ai_blog_configurator_toggle_view, name='ai_blog_configurator_toggle'),
    path('ai-blog-configurators/<int:pk>/run-now/', views.ai_blog_configurator_run_now_view, name='ai_blog_configurator_run_now'),
    path('ai-blog-configurators/<int:pk>/logs/', views.ai_blog_generation_logs_view, name='ai_blog_generation_logs'),

    # ============= URLs DOCUMENTACIÓN MÚLTIPLE =============
    # URLs de gestión de documentación múltiple (solo para agentes)
    path('multiple-documentation/', views.multiple_documentation_list_view, name='multiple_documentation_list'),
    path('multiple-documentation/create/', views.multiple_documentation_create_view, name='multiple_documentation_create'),
    path('multiple-documentation/<int:pk>/', views.multiple_documentation_detail_view, name='multiple_documentation_detail'),
    path('multiple-documentation/<int:pk>/edit/', views.multiple_documentation_edit_view, name='multiple_documentation_edit'),
    path('multiple-documentation/<int:pk>/delete/', views.multiple_documentation_delete_view, name='multiple_documentation_delete'),
    path('multiple-documentation/<int:pk>/add-item/', views.multiple_documentation_add_item_view, name='multiple_documentation_add_item'),
    path('multiple-documentation/<int:pk>/items/<int:item_id>/edit/', views.multiple_documentation_edit_item_view, name='multiple_documentation_edit_item'),
    path('multiple-documentation/<int:pk>/items/<int:item_id>/delete/', views.multiple_documentation_delete_item_view, name='multiple_documentation_delete_item'),
    path('multiple-documentation/<int:pk>/stats/', views.multiple_documentation_stats_view, name='multiple_documentation_stats'),
    
    # URLs públicas de documentación múltiple (sin autenticación)
    path('docs/<uuid:token>/', views.multiple_documentation_public_view, name='multiple_documentation_public'),
    path('docs/<uuid:token>/download/<int:item_id>/', views.multiple_documentation_download_item_view, name='multiple_documentation_download_item'),

    # ============= URLs PLANIFICACIÓN DE TAREAS =============
    # URLs de gestión de cronogramas (solo para usuarios autenticados)
    path('task-schedules/', views.task_schedule_list, name='task_schedule_list'),
    path('task-schedules/create/', views.task_schedule_create, name='task_schedule_create'),
    path('task-schedules/<int:pk>/', views.task_schedule_detail, name='task_schedule_detail'),
    path('task-schedules/<int:pk>/edit/', views.task_schedule_edit, name='task_schedule_edit'),
    path('task-schedules/<int:pk>/duplicate/', views.task_schedule_duplicate, name='task_schedule_duplicate'),
    path('task-schedules/<int:pk>/reschedule/', views.task_schedule_reschedule, name='task_schedule_reschedule'),
    path('task-schedules/<int:pk>/delete/', views.task_schedule_delete, name='task_schedule_delete'),
    path('task-schedules/<int:pk>/export/', views.task_schedule_export, name='task_schedule_export'),
    
    # Tareas del cronograma
    path('task-schedules/<int:schedule_pk>/tasks/create/', views.schedule_task_create, name='schedule_task_create'),
    path('schedule-tasks/<int:pk>/edit/', views.schedule_task_edit, name='schedule_task_edit'),
    path('schedule-tasks/<int:pk>/delete/', views.schedule_task_delete, name='schedule_task_delete'),
    path('schedule-tasks/<int:pk>/toggle/', views.schedule_task_toggle, name='schedule_task_toggle'),
    
    # URLs públicas de cronogramas (sin autenticación)
    path('schedule/<uuid:token>/', views.task_schedule_public, name='task_schedule_public'),
    path('schedule/<uuid:token>/gantt/', views.task_schedule_public_gantt, name='task_schedule_public_gantt'),
    path('public/schedule-tasks/<int:pk>/toggle/', views.schedule_task_toggle_public, name='schedule_task_toggle_public'),

    # URL del reloj mundial
    path('world-clock/', views.world_clock_view, name='world_clock'),

    # ============= URLs ACCIONES FINANCIERAS =============
    # URLs de gestión de acciones financieras (solo para agentes)
    path('financial-actions/', views.financial_actions_list_view, name='financial_actions_list'),
    path('financial-actions/create/', views.financial_action_create_view, name='financial_action_create'),
    path('financial-actions/<int:pk>/edit/', views.financial_action_edit_view, name='financial_action_edit'),
    path('financial-actions/<int:pk>/delete/', views.financial_action_delete_view, name='financial_action_delete'),
    path('financial-actions/<int:pk>/toggle/', views.financial_action_toggle_view, name='financial_action_toggle'),
    
    # API para el ticker
    path('api/financial-actions/ticker-data/', views.financial_actions_ticker_data_view, name='financial_actions_ticker_data'),
    
    # API para actualizar precios desde APIs externas
    path('api/financial-actions/update-prices/', views.financial_actions_update_prices_view, name='financial_actions_update_prices'),
    path('api/financial-actions/<int:pk>/update-price/', views.financial_action_update_single_price_view, name='financial_action_update_single_price'),
    
    # API para recomendaciones de IA en reuniones
    path('api/meetings/ai-recommendations/', views.meeting_ai_recommendations_view, name='meeting_ai_recommendations'),
    path('api/meetings/generate-spin/', views.generate_spin_methodology_view, name='generate_spin_methodology'),

    # ============= URLs ASISTENCIA DE CLIENTE =============
    # URLs de gestión de asistencia de cliente (solo para agentes)
    path('client-assistance/', views.client_assistance_list, name='client_assistance_list'),
    path('client-assistance/dashboard/', views.client_assistance_dashboard, name='client_assistance_dashboard'),
    path('client-assistance/create/', views.client_assistance_create, name='client_assistance_create'),
    path('client-assistance/<int:pk>/edit/', views.client_assistance_edit, name='client_assistance_edit'),
    path('client-assistance/<int:pk>/delete/', views.client_assistance_delete, name='client_assistance_delete'),
    path('client-assistance/<int:pk>/toggle/', views.client_assistance_toggle, name='client_assistance_toggle'),
    
    # URLs para ver entradas de tiempo de clientes
    path('client-time-entries/', views.client_time_entries_list, name='client_time_entries_list'),
    path('client-time-entries/<int:project_id>/', views.client_time_entries_list, name='client_time_entries_list'),
    
    # URL pública para que clientes registren horas (sin autenticación)
    path('client-hours/<str:token>/', views.client_time_entry_form, name='client_time_entry_form'),
    
    # URL pública para que clientes vean su dashboard (sin autenticación)
    path('client-dashboard/<str:token>/', views.client_dashboard_public, name='client_dashboard_public'),
    
    # ============= URLs ACORTADOR DE URLS =============
    # URLs de gestión del acortador (solo para agentes)
    path('short-urls/', views.short_url_list, name='short_url_list'),
    path('short-urls/create/', views.short_url_create, name='short_url_create'),
    path('short-urls/<int:pk>/edit/', views.short_url_edit, name='short_url_edit'),
    path('short-urls/<int:pk>/delete/', views.short_url_delete, name='short_url_delete'),
    path('short-urls/<int:pk>/stats/', views.short_url_stats, name='short_url_stats'),

]

# URL pública para redirección (debe estar fuera del include de tickets)
urlpatterns += [
    path('s/<str:short_code>/', views.short_url_redirect, name='short_url_redirect'),
    
    # ============= URLs CONJUNTOS DE PRODUCTOS =============
    # URLs de gestión de conjuntos de productos (solo para agentes)
    path('product-sets/', views.product_set_list, name='product_set_list'),
    path('product-sets/create/', views.product_set_create, name='product_set_create'),
    path('product-sets/<int:pk>/', views.product_set_detail, name='product_set_detail'),
    path('product-sets/<int:pk>/edit/', views.product_set_edit, name='product_set_edit'),
    path('product-sets/<int:pk>/delete/', views.product_set_delete, name='product_set_delete'),
    path('product-sets/<int:pk>/toggle-public/', views.product_set_toggle_public, name='product_set_toggle_public'),
    path('product-sets/<int:pk>/stats/', views.product_set_stats, name='product_set_stats'),
    
    # URLs para Precotizador
    path('precotizador/', views.precotizador_list, name='precotizador_list'),
    path('precotizador/crear/', views.precotizador_create, name='precotizador_create'),
    path('precotizador/<int:pk>/', views.precotizador_detail, name='precotizador_detail'),
    path('precotizador/<int:pk>/editar/', views.precotizador_edit, name='precotizador_edit'),
    path('precotizador/<int:pk>/eliminar/', views.precotizador_delete, name='precotizador_delete'),
    path('precotizador/<int:pk>/toggle-public/', views.precotizador_toggle_public_requests, name='precotizador_toggle_public_requests'),
    path('precotizador/<int:pk>/cotizar/', views.precotizador_quote, name='precotizador_quote'),
    path('cotizacion/<int:pk>/', views.precotizador_quote_detail, name='precotizador_quote_detail'),
    path('cotizacion/<int:pk>/editar/', views.precotizador_quote_edit, name='precotizador_quote_edit'),
    path('cotizacion/<int:pk>/eliminar/', views.precotizador_quote_delete, name='precotizador_quote_delete'),
    path('cotizacion/<int:pk>/compartir/', views.precotizador_quote_share, name='precotizador_quote_share'),
    
    # URLs públicas para cotizaciones (sin autenticación)
    path('cotizacion-publica/<str:token>/', views.precotizador_quote_public, name='precotizador_quote_public'),
    path('solicitar-cotizacion/<str:token>/', views.precotizador_public_request, name='precotizador_public_request'),
    
    # URL pública para conjuntos de productos (sin autenticación)
    path('products/<str:token>/', views.product_set_public, name='product_set_public'),
    
    # ============= URLs PARA DOCUMENTACIONES DE EMPRESAS =============
    # URLs privadas (requieren autenticación)
    path('documentaciones/', views.company_documentation_list, name='company_documentation_list'),
    path('documentaciones/crear/', views.company_documentation_create, name='company_documentation_create'),
    path('documentaciones/<int:pk>/', views.company_documentation_detail, name='company_documentation_detail'),
    path('documentaciones/<int:pk>/editar/', views.company_documentation_edit, name='company_documentation_edit'),
    path('documentaciones/<int:pk>/eliminar/', views.company_documentation_delete, name='company_documentation_delete'),
    path('documentaciones/<int:pk>/toggle-public/', views.company_documentation_toggle_public, name='company_documentation_toggle_public'),
    
    # URLs para edición individual de enlaces
    path('documentaciones/<int:doc_pk>/urls/crear/', views.company_documentation_url_create, name='company_documentation_url_create'),
    path('documentaciones/<int:doc_pk>/urls/<int:url_pk>/editar/', views.company_documentation_url_edit, name='company_documentation_url_edit'),
    path('documentaciones/<int:doc_pk>/urls/<int:url_pk>/eliminar/', views.company_documentation_url_delete, name='company_documentation_url_delete'),
    path('documentaciones/<int:doc_pk>/urls/<int:url_pk>/toggle/', views.company_documentation_url_toggle, name='company_documentation_url_toggle'),
    
    # URL pública para documentaciones (sin autenticación)
    path('documentacion/<str:token>/', views.company_documentation_public, name='company_documentation_public'),
    
    # ============= URLs PARA CONDICIONES DE USO =============
    path('condiciones-uso/', views.terms_of_use_list, name='terms_of_use_list'),
    path('condiciones-uso/crear/', views.terms_of_use_create, name='terms_of_use_create'),
    path('condiciones-uso/<int:pk>/', views.terms_of_use_detail, name='terms_of_use_detail'),
    path('condiciones-uso/<int:pk>/editar/', views.terms_of_use_edit, name='terms_of_use_edit'),
    path('condiciones-uso/<int:pk>/eliminar/', views.terms_of_use_delete, name='terms_of_use_delete'),
    path('condiciones-uso/<int:pk>/toggle/', views.terms_of_use_toggle, name='terms_of_use_toggle'),
    
    # ============= URLs PARA GENERADORES DE CONTACTOS =============
    # URLs privadas (requieren autenticación)
    path('generadores-contacto/', views.contact_generator_list, name='contact_generator_list'),
    path('generadores-contacto/crear/', views.contact_generator_create, name='contact_generator_create'),
    path('generadores-contacto/<int:pk>/', views.contact_generator_detail, name='contact_generator_detail'),
    path('generadores-contacto/<int:pk>/editar/', views.contact_generator_edit, name='contact_generator_edit'),
    path('generadores-contacto/<int:pk>/eliminar/', views.contact_generator_delete, name='contact_generator_delete'),
    path('generadores-contacto/<int:pk>/toggle-active/', views.contact_generator_toggle_active, name='contact_generator_toggle_active'),
    
    # URL pública para capturar contactos (sin autenticación)
    path('contacto/<str:token>/', views.contact_generator_public, name='contact_generator_public'),
    
    # URL pública para mostrar último ticket y solicitudes
    path('public/dashboard/', views.public_tickets_and_requests_view, name='public_tickets_and_requests'),
    
    # URL AJAX para actualizar estado de solicitudes
    path('ajax/update-request-status/<int:request_id>/', views.update_company_request_status, name='update_company_request_status'),
    
    # ============= URLs PARA SISTEMA DE FORMULARIOS =============
    # URLs privadas (requieren autenticación)
    path('formularios/', views.form_list, name='form_list'),
    path('formularios/crear/', views.form_create, name='form_create'),
    path('formularios/<int:pk>/', views.form_detail, name='form_detail'),
    path('formularios/<int:pk>/generar-preguntas-ia/', views.form_generate_ai_questions, name='form_generate_ai_questions'),
    path('formularios/<int:pk>/agregar-preguntas-ia/', views.form_add_ai_questions, name='form_add_ai_questions'),
    path('formularios/<int:pk>/editar/', views.form_edit, name='form_edit'),
    path('formularios/<int:pk>/eliminar/', views.form_delete, name='form_delete'),
    path('formularios/<int:pk>/respuestas/', views.form_responses, name='form_responses'),
    path('formularios/<int:form_pk>/respuestas/<int:response_pk>/', views.form_response_detail, name='form_response_detail'),
    path('formularios/<int:pk>/analisis-ia/', views.form_ai_analysis, name='form_ai_analysis'),
    path('formularios/<int:pk>/analisis-ia/historial/', views.form_ai_analysis_history, name='form_ai_analysis_history'),
    path('formularios/<int:form_pk>/analisis-ia/<int:analysis_pk>/', views.form_ai_analysis_detail, name='form_ai_analysis_detail'),
    
    # URLs para gestión de preguntas
    path('formularios/<int:form_pk>/preguntas/crear/', views.form_question_create, name='form_question_create'),
    path('formularios/<int:form_pk>/preguntas/<int:question_pk>/editar/', views.form_question_edit, name='form_question_edit'),
    path('formularios/<int:form_pk>/preguntas/<int:question_pk>/eliminar/', views.form_question_delete, name='form_question_delete'),
    
    # URLs para gestión de opciones
    path('formularios/<int:form_pk>/preguntas/<int:question_pk>/opciones/crear/', views.form_option_create, name='form_option_create'),
    path('formularios/<int:form_pk>/opciones/<int:option_pk>/actualizar-puntuacion/', views.form_option_update_score, name='form_option_update_score'),
    path('formularios/<int:form_pk>/opciones/<int:option_pk>/editar/', views.form_option_edit, name='form_option_edit'),
    path('formularios/<int:form_pk>/opciones/<int:option_pk>/eliminar/', views.form_option_delete, name='form_option_delete'),
    
    # URLs públicas para responder formularios
    path('form/<uuid:token>/', views.form_public, name='form_public'),
    
    # ============= URLs PARA SISTEMA DE ALCANCES =============
    # URL pública de alcances (sin autenticación)
    path('alcances/', views.alcance_publico_list, name='alcance_publico_list'),
    
    # URLs de gestión de alcances (requieren autenticación)
    path('alcances/gestion/', views.alcance_list, name='alcance_list'),
    path('alcances/crear/', views.alcance_create, name='alcance_create'),
    path('alcances/<int:pk>/editar/', views.alcance_edit, name='alcance_edit'),
    path('alcances/<int:pk>/eliminar/', views.alcance_delete, name='alcance_delete'),
    
    # ============= URLs PARA CONTROL DE LICENCIAS =============
    path('licencias/', views.license_list, name='license_list'),
    path('licencias/crear/', views.license_create, name='license_create'),
    path('licencias/<int:pk>/', views.license_detail, name='license_detail'),
    path('licencias/<int:pk>/editar/', views.license_edit, name='license_edit'),
    path('licencias/<int:pk>/eliminar/', views.license_delete, name='license_delete'),
    path('licencias/<int:pk>/qr/', views.license_qr_view, name='license_qr'),
    
    # URL pública para licencias (sin autenticación)
    path('license/<uuid:uuid>/', views.license_public, name='license_public'),
    path('api/license/<uuid:uuid>/', views.license_api, name='license_api'),
    
    # ============= URLs PARA CONTROL DE ACTIVOS =============
    path('activos/', views.asset_list, name='asset_list'),
    path('activos/crear/', views.asset_create, name='asset_create'),
    path('activos/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('activos/<int:pk>/editar/', views.asset_edit, name='asset_edit'),
    path('activos/<int:pk>/eliminar/', views.asset_delete, name='asset_delete'),
    path('activos/<int:pk>/asignar/', views.asset_assign, name='asset_assign'),
    path('activos/<int:pk>/historial/', views.asset_history, name='asset_history'),
    path('activos/<int:pk>/mantenimiento/', views.asset_maintenance, name='asset_maintenance'),
    
    # ============= URLs PARA WHATSAPP =============
    path('whatsapp/', views.whatsapp_dashboard, name='whatsapp_dashboard'),
    path('whatsapp/connect/', views.whatsapp_connect, name='whatsapp_connect'),
    path('whatsapp/disconnect/', views.whatsapp_disconnect, name='whatsapp_disconnect'),
    path('whatsapp/status/', views.whatsapp_status, name='whatsapp_status'),
    path('whatsapp/simulate-connection/', views.whatsapp_simulate_connection, name='whatsapp_simulate_connection'),
    path('whatsapp/keywords/create/', views.whatsapp_keyword_create, name='whatsapp_keyword_create'),
    path('whatsapp/keywords/<int:pk>/edit/', views.whatsapp_keyword_edit, name='whatsapp_keyword_edit'),
    path('whatsapp/keywords/<int:pk>/delete/', views.whatsapp_keyword_delete, name='whatsapp_keyword_delete'),
    path('whatsapp/messages/', views.whatsapp_messages, name='whatsapp_messages'),
    
    # URLs de Image to Prompt
    path('image-prompts/', views.image_prompt_list, name='image_prompt_list'),
    path('image-prompts/create/', views.image_prompt_create, name='image_prompt_create'),
    path('image-prompts/<int:pk>/', views.image_prompt_detail, name='image_prompt_detail'),
    path('image-prompts/<int:pk>/edit/', views.image_prompt_edit, name='image_prompt_edit'),
    path('image-prompts/<int:pk>/delete/', views.image_prompt_delete, name='image_prompt_delete'),
    
    # Prompts públicos
    path('prompts/', views.public_image_prompts, name='public_image_prompts'),
    path('prompts/<int:pk>/', views.public_image_prompt_detail, name='public_image_prompt_detail'),
    
    # Company AI Dashboard
    path('company-ai-dashboard/', views.company_ai_dashboard_list, name='company_ai_dashboard_list'),
    path('company-ai-dashboard/<int:pk>/', views.company_ai_dashboard_detail, name='company_ai_dashboard_detail'),
    path('company-ai-dashboard/<int:pk>/generate-summary/', views.company_ai_generate_summary, name='company_ai_generate_summary'),
    path('company-ai-summary/<int:pk>/', views.company_ai_summary_detail, name='company_ai_summary_detail'),
    
    # Dashboard de Desempeño de Usuarios IA
    path('user-ai-performance/', views.user_ai_performance_dashboard, name='user_ai_performance_dashboard'),
    path('user-ai-performance/<int:user_id>/', views.user_ai_performance_detail, name='user_ai_performance_detail'),
    path('user-ai-performance/<int:user_id>/generate/', views.user_ai_performance_generate, name='user_ai_performance_generate'),
    
    # Gerentes IA
    path('ai-managers/', views.ai_manager_list, name='ai_manager_list'),
    path('ai-managers/create/', views.ai_manager_create, name='ai_manager_create'),
    path('ai-managers/<int:pk>/', views.ai_manager_detail, name='ai_manager_detail'),
    path('ai-managers/<int:pk>/edit/', views.ai_manager_edit, name='ai_manager_edit'),
    path('ai-managers/<int:pk>/delete/', views.ai_manager_delete, name='ai_manager_delete'),
    path('ai-managers/<int:pk>/meeting/', views.ai_manager_meeting_create, name='ai_manager_meeting_create'),
    path('ai-managers/<int:pk>/meetings/', views.ai_manager_meetings, name='ai_manager_meetings'),
    path('ai-managers/<int:pk>/summary/generate/', views.ai_manager_generate_summary, name='ai_manager_generate_summary'),
    path('ai-manager-meeting/<int:pk>/', views.ai_manager_meeting_detail, name='ai_manager_meeting_detail'),
    path('ai-manager-summary/<int:pk>/', views.ai_manager_summary_detail, name='ai_manager_summary_detail'),
    
    # Rastreador Web
    path('web-tracker/', views.website_tracker_list, name='website_tracker_list'),
    path('web-tracker/create/', views.website_tracker_create, name='website_tracker_create'),
    path('web-tracker/<int:pk>/', views.website_tracker_detail, name='website_tracker_detail'),
    path('web-tracker/<int:pk>/delete/', views.website_tracker_delete, name='website_tracker_delete'),
    
    # Generador de Contratos Legales
    path('legal-contracts/', views.legal_contract_list, name='legal_contract_list'),
    path('legal-contracts/create/', views.legal_contract_create, name='legal_contract_create'),
    path('legal-contracts/<int:pk>/', views.legal_contract_detail, name='legal_contract_detail'),
    path('legal-contracts/<int:pk>/edit/', views.legal_contract_edit, name='legal_contract_edit'),
    path('legal-contracts/<int:pk>/delete/', views.legal_contract_delete, name='legal_contract_delete'),
    path('legal-contracts/<int:pk>/update-content/', views.legal_contract_update_content, name='legal_contract_update_content'),
    path('legal-contracts/<int:pk>/generate/', views.legal_contract_generate, name='legal_contract_generate'),
    path('legal-contracts/<int:pk>/download-pdf/', views.legal_contract_download_pdf, name='legal_contract_download_pdf'),
    path('legal-contracts/<int:pk>/toggle-public/', views.legal_contract_toggle_public, name='legal_contract_toggle_public'),
    
    # URL pública para contratos (sin autenticación)
    path('contract/<uuid:token>/', views.legal_contract_public, name='legal_contract_public'),
    path('contract/<uuid:token>/download/', views.legal_contract_public_pdf, name='legal_contract_public_pdf'),
    
    # Revisión de Contratos de Proveedores
    path('supplier-contracts/', views.supplier_contract_review_list, name='supplier_contract_review_list'),
    path('supplier-contracts/create/', views.supplier_contract_review_create, name='supplier_contract_review_create'),
    path('supplier-contracts/<int:pk>/', views.supplier_contract_review_detail, name='supplier_contract_review_detail'),
    path('supplier-contracts/<int:pk>/edit/', views.supplier_contract_review_edit, name='supplier_contract_review_edit'),
    path('supplier-contracts/<int:pk>/delete/', views.supplier_contract_review_delete, name='supplier_contract_review_delete'),
    path('supplier-contracts/<int:pk>/generate/', views.supplier_contract_review_generate, name='supplier_contract_review_generate'),
    path('supplier-contracts/<int:pk>/update-status/', views.supplier_contract_review_update_status, name='supplier_contract_review_update_status'),
    path('supplier-contracts/<int:pk>/download-pdf/', views.supplier_contract_review_download_pdf, name='supplier_contract_review_download_pdf'),
    
    # Enlaces de pago PayPal
    path('paypal-links/', views.paypal_link_list, name='paypal_link_list'),
    path('paypal-links/create/', views.paypal_link_create, name='paypal_link_create'),
    path('paypal-links/debug/', views.paypal_debug_config, name='paypal_debug_config'),
    path('paypal-links/generate-catalog-token/', views.paypal_generate_public_catalog_token, name='paypal_generate_public_catalog_token'),
    path('paypal-links/<int:pk>/', views.paypal_link_detail, name='paypal_link_detail'),
    path('paypal-links/<int:pk>/edit/', views.paypal_link_edit, name='paypal_link_edit'),
    path('paypal-links/<int:pk>/delete/', views.paypal_link_delete, name='paypal_link_delete'),
    path('paypal-links/<int:pk>/cancel/', views.paypal_link_cancel, name='paypal_link_cancel'),
    
    # URLs públicas de PayPal (sin autenticación)
    path('public/products/<uuid:token>/', views.public_products_catalog, name='public_products_catalog'),
    path('public/products/<uuid:token>/buy/<int:product_id>/', views.create_payment_from_product, name='create_payment_from_product'),
    path('paypal-payment/<uuid:token>/', views.paypal_payment_page, name='paypal_payment_page'),
    path('paypal-link-orders/<uuid:token>/', views.paypal_link_orders, name='paypal_link_orders'),  # Ver todas las órdenes de un link
    path('paypal-order/<uuid:token>/', views.paypal_order_summary, name='paypal_order_summary'),  # Legacy - redirige a paypal_link_orders
    path('paypal-download/<uuid:token>/', views.paypal_file_download, name='paypal_file_download'),  # Legacy
    path('order/<uuid:token>/', views.paypal_order_detail, name='paypal_order_detail'),  # Detalle de orden individual
    path('order-download/<uuid:token>/', views.paypal_order_download, name='paypal_order_download'),  # Descarga por orden
    
    # API/Webhooks de PayPal
    path('paypal/webhook/', views.paypal_webhook, name='paypal_webhook'),
    path('paypal/create-order/', views.paypal_create_order, name='paypal_create_order'),
    path('paypal/capture-order/', views.paypal_capture_order, name='paypal_capture_order'),
    
    # URLs de API para contadores de landing pages
    path('api/landing-pages/<slug:slug>/meeting-click/', views.landing_page_meeting_click, name='api_landing_meeting_click'),
    path('api/landing-pages/<slug:slug>/contact-click/', views.landing_page_contact_click, name='api_landing_contact_click'),
    
    # URLs de solicitudes de empleados
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('employee-requests/', views.employee_request_list, name='employee_request_list'),
    path('employee-requests/create/', views.employee_request_create, name='employee_request_create'),
    path('employee-requests/<int:pk>/', views.employee_request_detail, name='employee_request_detail'),
    path('employee-requests/<int:pk>/edit/', views.employee_request_edit, name='employee_request_edit'),
    path('employee-requests/<int:pk>/delete/', views.employee_request_delete, name='employee_request_delete'),
    
    # URLs de acuerdos internos
    path('internal-agreements/', views.internal_agreement_list, name='internal_agreement_list'),
    path('internal-agreements/create/', views.internal_agreement_create, name='internal_agreement_create'),
    path('internal-agreements/<int:pk>/', views.internal_agreement_detail, name='internal_agreement_detail'),
    path('internal-agreements/<int:pk>/edit/', views.internal_agreement_edit, name='internal_agreement_edit'),
    path('internal-agreements/<int:pk>/delete/', views.internal_agreement_delete, name='internal_agreement_delete'),
    path('internal-agreements/<int:pk>/sign/', views.internal_agreement_sign, name='internal_agreement_sign'),
    
    # URLs de planes de capacitación
    path('training-plans/', views.training_plan_list, name='training_plan_list'),
    path('training-plans/create/', views.training_plan_create, name='training_plan_create'),
    path('training-plans/<int:pk>/', views.training_plan_detail, name='training_plan_detail'),
    path('training-plans/<int:pk>/edit/', views.training_plan_edit, name='training_plan_edit'),
    
    # URLs de enlaces de capacitación
    path('training-plans/<int:plan_pk>/links/create/', views.training_link_create, name='training_link_create'),
    path('training-links/<int:pk>/edit/', views.training_link_edit, name='training_link_edit'),
    path('training-links/<int:pk>/delete/', views.training_link_delete, name='training_link_delete'),
    path('training-links/<int:pk>/complete/', views.training_link_complete, name='training_link_complete'),
    path('training-links/<int:pk>/uncomplete/', views.training_link_uncomplete, name='training_link_uncomplete'),
    
    # Mi progreso de capacitación
    path('my-training-progress/', views.my_training_progress, name='my_training_progress'),
    
    # URLs de recomendaciones IA
    path('ai-recommendations/', views.ai_recommendation_list, name='ai_recommendation_list'),
    path('ai-recommendations/create/', views.ai_recommendation_create, name='ai_recommendation_create'),
    path('ai-recommendations/<int:pk>/', views.ai_recommendation_detail, name='ai_recommendation_detail'),
    path('ai-recommendations/<int:pk>/edit/', views.ai_recommendation_edit, name='ai_recommendation_edit'),
    path('ai-recommendations/<int:pk>/delete/', views.ai_recommendation_delete, name='ai_recommendation_delete'),
    
    # URLs de ausencias de empleados
    path('employee-absences/', views.employee_absence_list, name='employee_absence_list'),
    path('employee-absences/create/', views.employee_absence_create, name='employee_absence_create'),
    path('employee-absences/<int:pk>/', views.employee_absence_detail, name='employee_absence_detail'),
    path('employee-absences/<int:pk>/edit/', views.employee_absence_edit, name='employee_absence_edit'),
    path('employee-absences/<int:pk>/approve/', views.employee_absence_approve, name='employee_absence_approve'),
    path('employee-absences/<int:pk>/delete/', views.employee_absence_delete, name='employee_absence_delete'),
    path('employee-absences/calendar/', views.employee_absence_calendar, name='employee_absence_calendar'),
    path('employee-absences/report/pdf/', views.employee_absence_report_pdf, name='employee_absence_report_pdf'),
    
    # URLs de tipos de ausencias
    path('absence-types/', views.absence_type_list, name='absence_type_list'),
    path('absence-types/create/', views.absence_type_create, name='absence_type_create'),
    path('absence-types/<int:pk>/edit/', views.absence_type_edit, name='absence_type_edit'),
    path('absence-types/<int:pk>/delete/', views.absence_type_delete, name='absence_type_delete'),
    path('absence-types/<int:pk>/toggle-active/', views.absence_type_toggle_active, name='absence_type_toggle_active'),
    
    # URLs de protocolos de empresa
    path('company-protocols/', views.company_protocol_list, name='company_protocol_list'),
    path('company-protocols/create/', views.company_protocol_create, name='company_protocol_create'),
    path('company-protocols/<int:pk>/', views.company_protocol_detail, name='company_protocol_detail'),
    path('company-protocols/<int:pk>/edit/', views.company_protocol_edit, name='company_protocol_edit'),
    path('company-protocols/<int:pk>/delete/', views.company_protocol_delete, name='company_protocol_delete'),
    path('company-protocols/<int:pk>/print-pdf/', views.company_protocol_print_pdf, name='company_protocol_print_pdf'),
    
    # URLs API de IA para protocolos
    path('company-protocols/<int:pk>/ai/generate-content/', views.company_protocol_ai_generate_content, name='company_protocol_ai_generate_content'),
    path('company-protocols/<int:pk>/ai/analyze-readability/', views.company_protocol_ai_analyze_readability, name='company_protocol_ai_analyze_readability'),
    path('company-protocols/<int:pk>/ai/get-suggestions/', views.company_protocol_ai_get_suggestions, name='company_protocol_ai_get_suggestions'),
    path('company-protocols/<int:pk>/ai/generate-summary/', views.company_protocol_ai_generate_summary, name='company_protocol_ai_generate_summary'),
    path('company-protocols/<int:pk>/ai/improve-content/', views.company_protocol_ai_improve_content, name='company_protocol_ai_improve_content'),
    
    # URLs públicas de protocolos
    path('company-protocols/<int:pk>/toggle-public/', views.company_protocol_toggle_public, name='company_protocol_toggle_public'),
    path('public/protocols/<uuid:uuid>/', views.company_protocol_public_view, name='company_protocol_public_view'),
    path('api/company-protocols/stats/', views.company_protocol_stats_api, name='company_protocol_stats_api'),
    
    # URLs de QA - Quejas y Sugerencias
    path('qa/', views.qa_dashboard, name='qa_dashboard'),
    path('qa/complaints/', views.qa_complaint_list, name='qa_complaint_list'),
    path('qa/complaints/create/', views.qa_complaint_create, name='qa_complaint_create'),
    path('qa/complaints/<int:pk>/', views.qa_complaint_detail, name='qa_complaint_detail'),
    path('qa/complaints/<int:pk>/edit/', views.qa_complaint_edit, name='qa_complaint_edit'),
    path('qa/complaints/<int:pk>/delete/', views.qa_complaint_delete, name='qa_complaint_delete'),
    path('qa/complaints/<int:pk>/assign/', views.qa_complaint_assign, name='qa_complaint_assign'),
    path('qa/complaints/<int:pk>/resolve/', views.qa_complaint_resolve, name='qa_complaint_resolve'),
    
    # URLs de Cumplimiento Mensual
    path('qa/cumplimiento/', views.monthly_cumplimiento_list, name='monthly_cumplimiento_list'),
    path('qa/cumplimiento/create/', views.monthly_cumplimiento_create, name='monthly_cumplimiento_create'),
    path('qa/cumplimiento/<int:pk>/', views.monthly_cumplimiento_detail, name='monthly_cumplimiento_detail'),
    path('qa/cumplimiento/<int:pk>/edit/', views.monthly_cumplimiento_edit, name='monthly_cumplimiento_edit'),
    path('qa/cumplimiento/<int:pk>/delete/', views.monthly_cumplimiento_delete, name='monthly_cumplimiento_delete'),
    path('qa/cumplimiento/<int:pk>/toggle/', views.monthly_cumplimiento_toggle, name='monthly_cumplimiento_toggle'),
    
    # URL pública para cumplimiento mensual (móvil)
    path('cumplimiento/<uuid:uuid>/', views.monthly_cumplimiento_public, name='monthly_cumplimiento_public'),
    
    # URL para menú de cumplimientos de usuario
    path('cumplimientos/<uuid:uuid>/', views.user_cumplimientos_menu, name='user_cumplimientos_menu'),
    
    # URLs del Tutor IA
    path('ai-tutor/', views.ai_tutor_list, name='ai_tutor_list'),
    path('ai-tutor/create/', views.ai_tutor_create, name='ai_tutor_create'),
    path('ai-tutor/<int:pk>/', views.ai_tutor_detail, name='ai_tutor_detail'),
    path('ai-tutor/<int:pk>/edit/', views.ai_tutor_edit, name='ai_tutor_edit'),
    path('ai-tutor/<int:pk>/delete/', views.ai_tutor_delete, name='ai_tutor_delete'),
    path('ai-tutor/<int:pk>/progress/', views.ai_tutor_progress_report, name='ai_tutor_progress_report'),
    path('ai-tutor/<int:pk>/upload/', views.ai_tutor_upload_attachment, name='ai_tutor_upload_attachment'),
    path('ai-tutor/feedback/<int:pk>/generate/', views.ai_tutor_generate_feedback_ajax, name='ai_tutor_generate_feedback_ajax'),
    path('ai-tutor/optimize-config/', views.ai_tutor_optimize_config, name='ai_tutor_optimize_config'),
    
    # URLs de Rendición de Gastos
    path('expense-reports/', views.expense_report_list, name='expense_report_list'),
    path('expense-reports/create/', views.expense_report_create, name='expense_report_create'),
    path('expense-reports/<int:pk>/', views.expense_report_detail, name='expense_report_detail'),
    path('expense-reports/<int:pk>/edit/', views.expense_report_edit, name='expense_report_edit'),
    path('expense-reports/<int:pk>/delete/', views.expense_report_delete, name='expense_report_delete'),
    path('expense-reports/<int:pk>/submit/', views.expense_report_submit, name='expense_report_submit'),
    path('expense-reports/<int:pk>/approve/', views.expense_report_approve, name='expense_report_approve'),
    path('expense-reports/<int:pk>/reject/', views.expense_report_reject, name='expense_report_reject'),
    path('expense-reports/<int:pk>/mark-paid/', views.expense_report_mark_paid, name='expense_report_mark_paid'),
    
    # URLs de Items de Gastos
    path('expense-reports/<int:report_pk>/items/create/', views.expense_item_create, name='expense_item_create'),
    path('expense-items/<int:pk>/edit/', views.expense_item_edit, name='expense_item_edit'),
    path('expense-items/<int:pk>/delete/', views.expense_item_delete, name='expense_item_delete'),
    
    # URLs de Comentarios de Gastos
    path('expense-reports/<int:report_pk>/comments/create/', views.expense_comment_create, name='expense_comment_create'),
    
    # URLs de Reuniones de Video
    path('video-meetings/', views.video_meeting_list, name='video_meeting_list'),
    path('video-meetings/create/', views.video_meeting_create, name='video_meeting_create'),
    path('video-meetings/<int:pk>/', views.video_meeting_detail, name='video_meeting_detail'),
    path('video-meetings/<int:pk>/edit/', views.video_meeting_edit, name='video_meeting_edit'),
    path('video-meetings/<int:pk>/delete/', views.video_meeting_delete, name='video_meeting_delete'),
    path('video-meetings/<int:pk>/transcription/', views.video_meeting_transcription, name='video_meeting_transcription_edit'),
    path('video-meetings/<int:pk>/transcribe/', views.video_meeting_transcribe, name='video_meeting_transcribe'),
    path('video-meetings/<int:pk>/transcription-status/', views.video_meeting_transcription_status, name='video_meeting_transcription_status'),
    path('video-meetings/<int:pk>/download-transcription/', views.video_meeting_download_transcription, name='video_meeting_download_transcription'),
    
    # URLs de Notas de Reunión
    path('video-meetings/<int:meeting_pk>/notes/<int:note_pk>/delete/', views.meeting_note_delete, name='meeting_note_delete'),
    
    # URLs de Generador de Citas IA
    path('quote-generator/', views.quote_generator_list, name='quote_generator_list'),
    path('quote-generator/create/', views.quote_generator_create, name='quote_generator_create'),
    path('quote-generator/<int:pk>/', views.quote_generator_detail, name='quote_generator_detail'),
    path('quote-generator/<int:pk>/edit/', views.quote_generator_edit, name='quote_generator_edit'),
    path('quote-generator/<int:pk>/regenerate/', views.quote_generator_regenerate, name='quote_generator_regenerate'),
    
    # URLs para cuentas regresivas
    path('countdown-timer/', views.countdown_timer_list, name='countdown_timer_list'),
    path('countdown-timer/create/', views.countdown_timer_create, name='countdown_timer_create'),
    path('countdown-timer/<int:pk>/', views.countdown_timer_detail, name='countdown_timer_detail'),
    path('countdown-timer/<int:pk>/edit/', views.countdown_timer_edit, name='countdown_timer_edit'),
    path('countdown-timer/<int:pk>/delete/', views.countdown_timer_delete, name='countdown_timer_delete'),
    
    # URLs de Procedimientos
    path('procedures/', views.procedure_list, name='procedure_list'),
    path('procedures/create/', views.procedure_create, name='procedure_create'),
    path('procedures/<int:pk>/', views.procedure_detail, name='procedure_detail'),
    path('procedures/<int:pk>/edit/', views.procedure_edit, name='procedure_edit'),
    path('procedures/<int:pk>/delete/', views.procedure_delete, name='procedure_delete'),
    path('procedures/<int:pk>/toggle-active/', views.procedure_toggle_active, name='procedure_toggle_active'),
    
    # URLs del Generador QR
    path('qr-generator/', views.qr_generator, name='qr_generator'),
    path('qr-generator/create/', views.qr_create, name='qr_create'),
    path('qr-generator/<int:pk>/', views.qr_detail, name='qr_detail'),
    path('qr-generator/<int:pk>/edit/', views.qr_edit, name='qr_edit'),
    path('qr-generator/<int:pk>/delete/', views.qr_delete, name='qr_delete'),
    path('qr-generator/<int:pk>/toggle-public/', views.qr_toggle_public, name='qr_toggle_public'),
    
    # URL pública para mostrar QR (sin autenticación)
    # QR público con token
    path('qr/<str:token>/', views.qr_public, name='qr_public'),
    
    # URLs de Quick TODO
    path('api/quick-todos/', views.quick_todo_list, name='quick_todo_list'),
    path('api/quick-todos/create/', views.quick_todo_create, name='quick_todo_create'),
    path('api/quick-todos/<int:todo_id>/toggle/', views.quick_todo_toggle, name='quick_todo_toggle'),
    path('api/quick-todos/<int:todo_id>/delete/', views.quick_todo_delete, name='quick_todo_delete'),
    path('api/quick-todos/clear-completed/', views.quick_todo_clear_completed, name='quick_todo_clear_completed'),
    
    # URLs de Respaldo de Base de Datos
    path('database/backup/', views.database_backup, name='database_backup'),
    path('database/restore/', views.database_restore, name='database_restore'),
    path('database/backup/download/<str:filename>/', views.download_backup, name='download_backup'),
    path('database/backup/delete/<str:filename>/', views.delete_backup, name='delete_backup'),
    
    # URLs Públicas de CRM Questions (sin autenticación)
    path('public/company/<uuid:company_uuid>/questions/', views.public_crm_questions, name='public_crm_questions'),
    path('public/company/<uuid:company_uuid>/questions/ask/', views.public_crm_question_create, name='public_crm_question_create'),
    
    # URLs de Tareas Programadas
    path('scheduled-tasks/', views.scheduled_task_list, name='scheduled_task_list'),
    path('scheduled-tasks/create/', views.scheduled_task_create, name='scheduled_task_create'),
    path('scheduled-tasks/<int:pk>/', views.scheduled_task_detail, name='scheduled_task_detail'),
    path('scheduled-tasks/<int:pk>/edit/', views.scheduled_task_edit, name='scheduled_task_edit'),
    path('scheduled-tasks/<int:pk>/delete/', views.scheduled_task_delete, name='scheduled_task_delete'),
    path('scheduled-tasks/<int:pk>/toggle-active/', views.scheduled_task_toggle_active, name='scheduled_task_toggle_active'),
    path('scheduled-tasks/<int:pk>/execute/', views.scheduled_task_execute, name='scheduled_task_execute'),
    
    # URLs de API
    path('api/', include('tickets.api_urls')),
]

