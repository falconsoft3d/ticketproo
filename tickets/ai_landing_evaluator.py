"""
Sistema de evaluación de IA para landing page submissions
"""
import json
from django.conf import settings

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def evaluate_landing_submission(submission):
    """
    Evalúa un envío de landing page usando IA
    
    Args:
        submission: Instancia de LandingPageSubmission
        
    Returns:
        dict: Resultado de la evaluación
    """
    if not OPENAI_AVAILABLE:
        raise Exception("OpenAI no está disponible")
    
    # Obtener configuración
    from .models import SystemConfiguration
    config = SystemConfiguration.get_config()
    
    if not config.openai_api_key:
        raise Exception("API Key de OpenAI no configurada")
    
    # Inicializar cliente OpenAI
    client = OpenAI(api_key=config.openai_api_key)
    
    # Preparar datos para evaluación
    evaluation_data = {
        'nombre_completo': f"{submission.nombre} {submission.apellido}",
        'email': submission.email,
        'telefono': submission.telefono,
        'empresa': submission.empresa,
        'mensaje': submission.mensaje,
        'landing_page': submission.landing_page.nombre_producto,
        'utm_source': submission.utm_source,
        'utm_medium': submission.utm_medium,
        'utm_campaign': submission.utm_campaign,
    }
    
    # Prompt para la IA
    prompt = f"""
    Analiza la siguiente información de un potencial cliente que completó un formulario de landing page:

    **DATOS DEL CONTACTO:**
    - Nombre: {evaluation_data['nombre_completo']}
    - Email: {evaluation_data['email']}
    - Teléfono: {evaluation_data['telefono']}
    - Empresa: {evaluation_data['empresa']}

    **MENSAJE/PROYECTO:**
    {evaluation_data['mensaje']}

    **CONTEXTO:**
    - Landing Page: {evaluation_data['landing_page']}
    - Fuente UTM: {evaluation_data['utm_source']}
    - Medio UTM: {evaluation_data['utm_medium']}
    - Campaña UTM: {evaluation_data['utm_campaign']}

    **INSTRUCCIONES:**
    Evalúa esta información en las siguientes 3 categorías (puntuación 1-10):

    1. **EMPRESA** (1-10): Evalúa la seriedad, profesionalismo y potencial de la empresa
       - ¿El nombre de la empresa parece legítimo?
       - ¿Es coherente con el proyecto descrito?
       - ¿Indica potencial comercial?

    2. **CONTACTO** (1-10): Evalúa la calidad de la información de contacto
       - ¿El email parece profesional?
       - ¿Proporciona información completa?
       - ¿El nombre suena real y profesional?

    3. **PROYECTO** (1-10): Evalúa el potencial del proyecto descrito
       - ¿El mensaje es claro y específico?
       - ¿Indica un proyecto real con presupuesto?
       - ¿Parece un cliente serio vs solo curiosidad?

    **RESPONDE EN FORMATO JSON:**
    {{
        "company_score": [1-10],
        "contact_score": [1-10],
        "project_score": [1-10],
        "overall_score": [promedio decimal],
        "priority_level": ["low", "medium", "high", "urgent"],
        "summary": "Resumen de 2-3 líneas de la evaluación general",
        "recommendations": "Recomendaciones específicas de seguimiento (2-3 líneas)",
        "red_flags": ["lista", "de", "señales", "de", "alerta", "si", "las", "hay"],
        "positive_signals": ["lista", "de", "señales", "positivas"]
    }}

    CRITERIOS DE PRIORIDAD:
    - low (1-4): Poco profesional, información incompleta, proyecto vago
    - medium (5-6): Información básica completa, proyecto moderadamente claro
    - high (7-8): Muy profesional, proyecto claro, empresa seria
    - urgent (9-10): Oportunidad excepcional, empresa reconocida, proyecto grande

    Responde SOLO con el JSON, sin texto adicional.
    """

    try:
        # Llamada a OpenAI
        response = client.chat.completions.create(
            model="gpt-4",  # Usar GPT-4 para mejores análisis
            messages=[
                {
                    "role": "system", 
                    "content": "Eres un experto analista de ventas y marketing que evalúa leads comerciales. Tu análisis debe ser objetivo, práctico y enfocado en identificar oportunidades comerciales reales."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Baja temperatura para respuestas más consistentes
            max_tokens=1000
        )
        
        # Extraer respuesta
        response_text = response.choices[0].message.content.strip()
        
        # Parsear JSON
        try:
            result = json.loads(response_text)
            
            # Validar que todos los campos requeridos estén presentes
            required_fields = ['company_score', 'contact_score', 'project_score', 
                             'overall_score', 'priority_level', 'summary', 'recommendations']
            
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Campo requerido faltante: {field}")
            
            # Validar rangos
            for score_field in ['company_score', 'contact_score', 'project_score']:
                if not (1 <= result[score_field] <= 10):
                    raise ValueError(f"Puntuación fuera de rango: {score_field}")
            
            # Validar nivel de prioridad
            if result['priority_level'] not in ['low', 'medium', 'high', 'urgent']:
                result['priority_level'] = 'medium'  # Default fallback
            
            return result
            
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing JSON de OpenAI: {e}")
            
    except Exception as e:
        raise Exception(f"Error llamando a OpenAI: {e}")


def batch_evaluate_submissions(limit=10):
    """
    Evalúa en lote los envíos no evaluados
    
    Args:
        limit: Número máximo de envíos a procesar
        
    Returns:
        dict: Resultados del procesamiento
    """
    from .models import LandingPageSubmission
    
    # Obtener envíos no evaluados
    submissions = LandingPageSubmission.objects.filter(
        ai_evaluated=False
    ).order_by('-created_at')[:limit]
    
    results = {
        'processed': 0,
        'errors': 0,
        'results': []
    }
    
    for submission in submissions:
        try:
            success = submission.evaluate_with_ai()
            if success:
                results['processed'] += 1
                results['results'].append({
                    'id': submission.id,
                    'status': 'success',
                    'score': submission.ai_overall_score,
                    'priority': submission.ai_priority_level
                })
            else:
                results['errors'] += 1
                results['results'].append({
                    'id': submission.id,
                    'status': 'error',
                    'error': 'Evaluation failed'
                })
        except Exception as e:
            results['errors'] += 1
            results['results'].append({
                'id': submission.id,
                'status': 'error',
                'error': str(e)
            })
    
    return results


def get_evaluation_stats():
    """
    Obtiene estadísticas de las evaluaciones
    
    Returns:
        dict: Estadísticas
    """
    from .models import LandingPageSubmission
    from django.db.models import Avg, Count
    
    total_submissions = LandingPageSubmission.objects.count()
    evaluated_submissions = LandingPageSubmission.objects.filter(ai_evaluated=True).count()
    
    stats = {
        'total_submissions': total_submissions,
        'evaluated_submissions': evaluated_submissions,
        'pending_evaluation': total_submissions - evaluated_submissions,
        'evaluation_percentage': (evaluated_submissions / total_submissions * 100) if total_submissions > 0 else 0
    }
    
    if evaluated_submissions > 0:
        # Estadísticas de puntuaciones
        evaluated = LandingPageSubmission.objects.filter(ai_evaluated=True)
        
        stats.update({
            'avg_company_score': evaluated.aggregate(avg=Avg('ai_company_score'))['avg'],
            'avg_contact_score': evaluated.aggregate(avg=Avg('ai_contact_score'))['avg'],
            'avg_project_score': evaluated.aggregate(avg=Avg('ai_project_score'))['avg'],
            'avg_overall_score': evaluated.aggregate(avg=Avg('ai_overall_score'))['avg'],
        })
        
        # Distribución por prioridad
        priority_stats = evaluated.values('ai_priority_level').annotate(count=Count('id'))
        stats['priority_distribution'] = {item['ai_priority_level']: item['count'] for item in priority_stats}
    
    return stats