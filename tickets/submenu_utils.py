"""
Utilidades para generar submenús contextuales en el dashboard estilo Odoo
"""
from django.urls import reverse
from tickets.utils import is_agent


def get_crm_submenu(request, active_item=None):
    """Genera el submenú para el módulo CRM"""
    from tickets.models import Contact, Company, Opportunity
    
    user = request.user
    
    # Contar registros según permisos
    if is_agent(user):
        contacts_count = Contact.objects.count()
        companies_count = Company.objects.count()
        opportunities_count = Opportunity.objects.count()
    else:
        contacts_count = Contact.objects.filter(created_by=user).count()
        companies_count = Company.objects.filter(created_by=user).count()
        opportunities_count = Opportunity.objects.filter(
            created_by=user
        ).count() + Opportunity.objects.filter(assigned_to=user).count()
    
    submenu = [
        {
            'name': 'Contactos',
            'url': reverse('contact_list'),
            'icon': 'bi bi-person-lines-fill',
            'count': contacts_count,
            'active': active_item == 'contacts'
        },
        {
            'name': 'Empresas',
            'url': reverse('company_list'),
            'icon': 'bi bi-building',
            'count': companies_count,
            'active': active_item == 'companies'
        },
        {
            'name': 'CRM',
            'url': reverse('crm_dashboard'),
            'icon': 'bi bi-graph-up-arrow',
            'count': opportunities_count,
            'active': active_item == 'crm'
        },
        {
            'name': 'Mis Actividades',
            'url': reverse('my_activities_dashboard'),
            'icon': 'fas fa-tasks',
            'count': None,
            'active': active_item == 'activities'
        },
        {
            'name': 'Estados CRM',
            'url': reverse('opportunity_status_list'),
            'icon': 'bi bi-kanban',
            'count': None,
            'active': active_item == 'statuses'
        },
        {
            'name': 'Reuniones',
            'url': reverse('meeting_list'),
            'icon': 'bi bi-calendar-event',
            'count': None,
            'active': active_item == 'meetings'
        },
        {
            'name': 'Cotizaciones',
            'url': reverse('quotation_list'),
            'icon': 'bi bi-file-earmark-text',
            'count': None,
            'active': active_item == 'quotations'
        },
        {
            'name': 'DRF',
            'url': reverse('frd_list'),
            'icon': 'bi bi-file-earmark-ruled',
            'count': None,
            'active': active_item == 'frd'
        },
    ]
    
    return submenu


def get_hr_submenu(request, active_item=None):
    """Genera el submenú para el módulo HR"""
    submenu = [
        {
            'name': 'Dashboard',
            'url': reverse('employee_dashboard'),
            'icon': 'bi bi-speedometer2',
            'count': None,
            'active': active_item == 'dashboard'
        },
        {
            'name': 'Solicitudes',
            'url': reverse('employee_request_list'),
            'icon': 'bi bi-file-earmark-text',
            'count': None,
            'active': active_item == 'requests'
        },
        {
            'name': 'Gastos',
            'url': reverse('expense_report_list'),
            'icon': 'bi bi-receipt',
            'count': None,
            'active': active_item == 'expenses'
        },
        {
            'name': 'Reuniones Video',
            'url': reverse('video_meeting_list'),
            'icon': 'bi bi-camera-video',
            'count': None,
            'active': active_item == 'video_meetings'
        },
        {
            'name': 'AI Managers',
            'url': reverse('ai_manager_list'),
            'icon': 'bi bi-robot',
            'count': None,
            'active': active_item == 'ai_managers'
        },
        {
            'name': 'Acuerdos Internos',
            'url': reverse('internal_agreement_list'),
            'icon': 'bi bi-file-earmark-check',
            'count': None,
            'active': active_item == 'agreements'
        },
        {
            'name': 'Capacitación',
            'url': reverse('training_plan_list'),
            'icon': 'bi bi-mortarboard',
            'count': None,
            'active': active_item == 'training'
        },
        {
            'name': 'Ausencias',
            'url': reverse('employee_absence_list'),
            'icon': 'bi bi-calendar-x',
            'count': None,
            'active': active_item == 'absences'
        },
        {
            'name': 'Activos',
            'url': reverse('asset_list'),
            'icon': 'bi bi-laptop',
            'count': None,
            'active': active_item == 'assets'
        },
    ]
    
    return submenu


def get_cap_submenu(request, active_item=None):
    """Genera el submenú para el módulo CAP (Capacitación)"""
    submenu = [
        {
            'name': 'Cursos',
            'url': reverse('course_list'),
            'icon': 'bi bi-collection',
            'count': None,
            'active': active_item == 'courses'
        },
        {
            'name': 'Exámenes',
            'url': reverse('exam_list'),
            'icon': 'bi bi-question-circle',
            'count': None,
            'active': active_item == 'exams'
        },
        {
            'name': 'Preguntas',
            'url': reverse('crm_questions_list'),
            'icon': 'bi bi-chat-square-text',
            'count': None,
            'active': active_item == 'questions'
        },
        {
            'name': 'Generador QR',
            'url': reverse('qr_generator'),
            'icon': 'bi bi-qr-code',
            'count': None,
            'active': active_item == 'qr'
        },
    ]
    
    return submenu


def get_co_submenu(request, active_item=None):
    """Genera el submenú para el módulo CO (Compartir)"""
    submenu = [
        {
            'name': 'Mis Archivos',
            'url': reverse('shared_files_list'),
            'icon': 'bi bi-files',
            'count': None,
            'active': active_item == 'files'
        },
        {
            'name': 'Subir Archivo',
            'url': reverse('shared_file_upload'),
            'icon': 'bi bi-cloud-upload',
            'count': None,
            'active': active_item == 'upload'
        },
        {
            'name': 'Grabaciones',
            'url': reverse('recordings_list'),
            'icon': 'bi bi-mic',
            'count': None,
            'active': active_item == 'recordings'
        },
        {
            'name': 'Formularios',
            'url': reverse('form_list'),
            'icon': 'bi bi-list-ul',
            'count': None,
            'active': active_item == 'forms'
        },
        {
            'name': 'WhatsApp',
            'url': reverse('whatsapp_dashboard'),
            'icon': 'fab fa-whatsapp',
            'count': None,
            'active': active_item == 'whatsapp'
        },
    ]
    
    return submenu


def get_gt_submenu(request, active_item=None):
    """Genera el submenú para el módulo GT (Gestión)"""
    submenu = [
        {
            'name': 'Notas Internas',
            'url': reverse('notes_list'),
            'icon': 'bi bi-journal-text',
            'count': None,
            'active': active_item == 'notes'
        },
        {
            'name': 'Categorías',
            'url': reverse('category_list'),
            'icon': 'bi bi-tags',
            'count': None,
            'active': active_item == 'categories'
        },
        {
            'name': 'Proyectos',
            'url': reverse('project_list'),
            'icon': 'bi bi-folder',
            'count': None,
            'active': active_item == 'projects'
        },
        {
            'name': 'Productos',
            'url': reverse('product_list'),
            'icon': 'bi bi-box-seam',
            'count': None,
            'active': active_item == 'products'
        },
        {
            'name': 'Landing Pages',
            'url': reverse('landing_page_list'),
            'icon': 'fas fa-rocket',
            'count': None,
            'active': active_item == 'landing'
        },
        {
            'name': 'Blog',
            'url': reverse('blog_post_list_admin'),
            'icon': 'bi bi-newspaper',
            'count': None,
            'active': active_item == 'blog'
        },
        {
            'name': 'Tareas',
            'url': reverse('task_list'),
            'icon': 'bi bi-list-task',
            'count': None,
            'active': active_item == 'tasks'
        },
        {
            'name': 'Chatbots',
            'url': reverse('chatbot_list'),
            'icon': 'bi bi-robot',
            'count': None,
            'active': active_item == 'chatbots'
        },
    ]
    
    return submenu


def get_cg_submenu(request, active_item=None):
    """Genera el submenú para el módulo CG (Código y Generadores)"""
    submenu = [
        {
            'name': 'Tareas Programadas',
            'url': reverse('scheduled_task_list'),
            'icon': 'bi bi-clock-history',
            'count': None,
            'active': active_item == 'scheduled'
        },
        {
            'name': 'Contador Juegos',
            'url': reverse('game_counter_list'),
            'icon': 'bi bi-joystick',
            'count': None,
            'active': active_item == 'games'
        },
        {
            'name': 'Contador Deporte',
            'url': reverse('exercise_counter_list'),
            'icon': 'bi bi-heart-pulse',
            'count': None,
            'active': active_item == 'exercise'
        },
        {
            'name': 'Solicitudes Cliente',
            'url': reverse('client_request_list'),
            'icon': 'bi bi-file-text',
            'count': None,
            'active': active_item == 'requests'
        },
    ]
    
    return submenu


def get_qa_submenu(request, active_item=None):
    """Genera el submenú para el módulo QA (Control de Calidad)"""
    submenu = [
        {
            'name': 'Reportes QA',
            'url': reverse('qa_complaint_list'),
            'icon': 'fas fa-list',
            'count': None,
            'active': active_item == 'complaints'
        },
        {
            'name': 'Nuevo Reporte',
            'url': reverse('qa_complaint_create'),
            'icon': 'fas fa-plus-circle',
            'count': None,
            'active': active_item == 'create'
        },
        {
            'name': 'Calificaciones',
            'url': reverse('qa_rating_list'),
            'icon': 'fas fa-star',
            'count': None,
            'active': active_item == 'ratings'
        },
        {
            'name': 'Cumplimiento',
            'url': reverse('monthly_cumplimiento_list'),
            'icon': 'fas fa-calendar-check',
            'count': None,
            'active': active_item == 'compliance'
        },
        {
            'name': 'Políticas de Privacidad',
            'url': reverse('privacy_policy_list'),
            'icon': 'bi bi-shield-check',
            'count': None,
            'active': active_item == 'privacy_policies'
        },
    ]
    
    return submenu


def get_hm_submenu(request, active_item=None):
    """Genera el submenú para el módulo HM (Herramientas)"""
    submenu = [
        {
            'name': 'GetPDFPage',
            'url': reverse('pdf_get_pages'),
            'icon': 'bi bi-file-earmark-pdf',
            'count': None,
            'active': active_item == 'pdf_pages'
        },
        {
            'name': 'JointPDF',
            'url': reverse('pdf_join'),
            'icon': 'bi bi-files',
            'count': None,
            'active': active_item == 'pdf_join'
        },
        {
            'name': 'Pdf2Pdfs',
            'url': reverse('pdf_split'),
            'icon': 'bi bi-file-earmark-break',
            'count': None,
            'active': active_item == 'pdf_split'
        },
        {
            'name': 'Calculadora',
            'url': reverse('calculator'),
            'icon': 'bi bi-calculator',
            'count': None,
            'active': active_item == 'calculator'
        },
        {
            'name': 'Candidatos',
            'url': reverse('candidate_list'),
            'icon': 'bi bi-person-check',
            'count': None,
            'active': active_item == 'candidates'
        },
        {
            'name': 'Empleados',
            'url': reverse('active_employee_list'),
            'icon': 'bi bi-people-fill',
            'count': None,
            'active': active_item == 'employees'
        },
        {
            'name': 'Usuarios',
            'url': reverse('user_management'),
            'icon': 'bi bi-people',
            'count': None,
            'active': active_item == 'users'
        },
    ]
    
    return submenu


def get_dc_submenu(request, active_item=None):
    """Genera el submenú para el módulo DC (Documentación)"""
    submenu = [
        {
            'name': 'Documentos',
            'url': reverse('document_list'),
            'icon': 'bi bi-file-earmark-text',
            'count': None,
            'active': active_item == 'documents'
        },
        {
            'name': 'Acuerdos',
            'url': reverse('agreement_list'),
            'icon': 'bi bi-file-earmark-check',
            'count': None,
            'active': active_item == 'agreements'
        },
        {
            'name': 'Contratos Legales',
            'url': reverse('legal_contract_list'),
            'icon': 'bi bi-file-earmark-ruled',
            'count': None,
            'active': active_item == 'contracts'
        },
        {
            'name': 'Libros IA',
            'url': reverse('ai_book_list'),
            'icon': 'bi bi-book',
            'count': None,
            'active': active_item == 'books'
        },
        {
            'name': 'Artículos IA',
            'url': reverse('ai_article_project_list'),
            'icon': 'bi bi-newspaper',
            'count': None,
            'active': active_item == 'articles'
        },
        {
            'name': 'Procedimientos',
            'url': reverse('procedure_list'),
            'icon': 'bi bi-list-columns-reverse',
            'count': None,
            'active': active_item == 'procedures'
        },
    ]
    
    return submenu


def get_ot_submenu(request, active_item=None):
    """Genera el submenú para el módulo OT (Otros/Reportes)"""
    submenu = [
        {
            'name': 'Parte Diario',
            'url': reverse('daily_report'),
            'icon': 'bi bi-calendar-day',
            'count': None,
            'active': active_item == 'daily'
        },
        {
            'name': 'Analytics',
            'url': reverse('page_visits_analytics'),
            'icon': 'fas fa-chart-bar',
            'count': None,
            'active': active_item == 'analytics'
        },
        {
            'name': 'Configurador IA Blog',
            'url': reverse('ai_blog_configurators_list'),
            'icon': 'fas fa-robot',
            'count': None,
            'active': active_item == 'ai_blog'
        },
        {
            'name': 'Licencias',
            'url': reverse('license_list'),
            'icon': 'bi bi-key',
            'count': None,
            'active': active_item == 'licenses'
        },
    ]
    
    return submenu


# Mapa de funciones de submenú por módulo
SUBMENU_FUNCTIONS = {
    'CRM': get_crm_submenu,
    'HR': get_hr_submenu,
    'CAP': get_cap_submenu,
    'CO': get_co_submenu,
    'GT': get_gt_submenu,
    'CG': get_cg_submenu,
    'QA': get_qa_submenu,
    'HM': get_hm_submenu,
    'DC': get_dc_submenu,
    'OT': get_ot_submenu,
}


def get_app_context(app_name, request, active_item=None):
    """
    Genera el contexto completo para una aplicación
    
    Args:
        app_name: Nombre del módulo (CRM, HR, CAP, etc.)
        request: HttpRequest object
        active_item: Item activo en el submenú
    
    Returns:
        dict: Contexto con app_name, submenu_items y pending_messages
    """
    submenu_function = SUBMENU_FUNCTIONS.get(app_name)
    
    context = {
        'app_name': app_name,
        'pending_messages': 0,  # TODO: Calcular mensajes pendientes reales
        'submenu_items': []
    }
    
    if submenu_function:
        context['submenu_items'] = submenu_function(request, active_item)
    
    return context
