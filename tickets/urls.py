from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # URLs de tickets
    path('tickets/', views.ticket_list_view, name='ticket_list'),
    path('tickets/export/excel/', views.ticket_export_excel, name='ticket_export_excel'),
    path('tickets/create/', views.ticket_create_view, name='ticket_create'),
    path('tickets/<int:pk>/', views.ticket_detail_view, name='ticket_detail'),
    path('tickets/<int:pk>/edit/', views.ticket_edit_view, name='ticket_edit'),
    path('tickets/<int:pk>/delete/', views.ticket_delete_view, name='ticket_delete'),
    path('tickets/<int:pk>/approve/', views.ticket_approve_view, name='ticket_approve'),
    path('tickets/<int:pk>/unassign/', views.unassign_ticket_view, name='unassign_ticket'),
    
    # URLs públicas de cursos (sin autenticación) - DEBEN IR ANTES que la ruta genérica de tickets
    path('public/courses/<uuid:token>/', views.course_public, name='course_public'),
    path('public/courses/<uuid:token>/classes/<int:class_id>/', views.course_class_public, name='course_class_public'),
    
    # Vista pública de conceptos (sin autenticación requerida)
    path('public/concepts/', views.public_concepts_view, name='public_concepts'),
    
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
    path('contacts/create/', views.contact_create, name='contact_create'),
    path('contacts/<int:pk>/', views.contact_detail, name='contact_detail'),
    path('contacts/<int:pk>/edit/', views.contact_edit, name='contact_edit'),
    path('contacts/<int:pk>/delete/', views.contact_delete, name='contact_delete'),
    
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
    
    # URLs de gestión de estados CRM (solo para agentes)
    path('crm/status/', views.opportunity_status_list, name='opportunity_status_list'),
    path('crm/status/create/', views.opportunity_status_create, name='opportunity_status_create'),
    path('crm/status/<int:pk>/edit/', views.opportunity_status_edit, name='opportunity_status_edit'),
    path('crm/status/<int:pk>/delete/', views.opportunity_status_delete, name='opportunity_status_delete'),
    
    # URLs de Reuniones
    path('meetings/', views.meeting_list_view, name='meeting_list'),
    path('meetings/create/', views.meeting_create_view, name='meeting_create'),
    path('meetings/<int:pk>/', views.meeting_detail_view, name='meeting_detail'),
    path('meetings/<int:pk>/edit/', views.meeting_edit_view, name='meeting_edit'),
    path('meetings/<int:pk>/delete/', views.meeting_delete_view, name='meeting_delete'),
    path('meetings/<int:pk>/print/', views.meeting_print_view, name='meeting_print'),
    path('meetings/<int:pk>/questions/', views.meeting_questions_view, name='meeting_questions'),
    path('meetings/<int:pk>/attendees/', views.meeting_attendees_view, name='meeting_attendees'),
    
    # URLs públicas de reuniones (sin autenticación)
    path('meetings/public/<str:token>/', views.meeting_public_view, name='meeting_public'),
    path('meetings/public/<str:token>/register/', views.meeting_register_view, name='meeting_register'),
    path('meetings/public/<str:token>/questions/', views.meeting_questions_public_view, name='meeting_questions_public'),
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
    path('landing-pages/contacts/', views.landing_page_contacts, name='landing_page_contacts'),
    path('landing-pages/submissions/<int:submission_id>/create-contact/', views.create_contact_from_submission_view, name='create_contact_from_submission'),
    
    # URLs AJAX para landing pages
    path('ajax/landing-pages/submissions/<int:submission_id>/create-contact/', views.ajax_create_contact_from_submission, name='ajax_create_contact_from_submission'),
    path('ajax/landing-pages/submissions/create-contacts-batch/', views.ajax_create_contacts_batch, name='ajax_create_contacts_batch'),
    path('ajax/landing-pages/submissions/<int:submission_id>/details/', views.ajax_submission_details, name='ajax_submission_details'),
    
    # URLs para evaluación IA de landing pages
    path('ai/landing-submissions/', views.landing_submissions_list_view, name='landing_submissions_list'),
    path('ai/landing-submissions/<int:submission_id>/', views.landing_submission_detail_view, name='landing_submission_detail'),
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

]
