"""
Módulo de generación de contenido de blog usando IA
"""
from openai import OpenAI
import random
import time
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import BlogPost, BlogCategory, AIBlogGenerationLog, SystemConfiguration


def run_ai_blog_generation(configurator, force=False):
    """
    Ejecuta la generación de contenido de blog para un configurador específico
    """
    start_time = time.time()
    result = {
        'success': False,
        'posts_created': 0,
        'keywords_used': [],
        'generated_content': [],
        'error': None
    }
    
    try:
        # Obtener keywords de la configuración
        keywords = [kw.strip() for kw in configurator.keywords.split(',') if kw.strip()]
        if not keywords:
            raise Exception("No hay keywords configuradas")
        
        # Verificar si ya debe ejecutarse según la frecuencia (solo si no es forzado)
        if not force and not configurator.should_run():
            result['error'] = 'El configurador no debe ejecutarse según su frecuencia programada'
            return result
        
        posts_created = 0
        generated_content = []
        keywords_used = keywords[:configurator.max_posts_per_run]  # Usar max_posts_per_run
        
        # Generar posts según el número configurado
        for i in range(min(configurator.max_posts_per_run, len(keywords))):
            try:
                keyword = keywords[i]
                
                # Generar el contenido del blog
                generated_content_data = generate_blog_post_content(configurator, keyword)
                
                if not generated_content_data:
                    continue
                
                # Crear el post en la base de datos
                from django.contrib.auth.models import User
                
                # Buscar un usuario para asignar como autor (preferiblemente admin)
                author = User.objects.filter(is_superuser=True).first()
                if not author:
                    author = User.objects.first()
                    if not author:
                        raise Exception("No hay usuarios disponibles para asignar como autor")
                
                # Generar slug único
                from django.utils.text import slugify
                base_slug = slugify(generated_content_data['title'])
                slug = base_slug
                counter = 1
                
                # Asegurarse de que el slug sea completamente único
                while BlogPost.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                # Verificar que el título no sea demasiado similar a otros existentes
                similar_titles = BlogPost.objects.filter(
                    title__icontains=generated_content_data['title'][:20]
                ).exclude(slug=slug)
                
                if similar_titles.exists():
                    # Si hay títulos similares, añadir un identificador único
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m")
                    slug = f"{base_slug}-{timestamp}-{counter}"
                
                blog_post = BlogPost.objects.create(
                    title=generated_content_data['title'],
                    slug=slug,
                    content=generated_content_data['content'],
                    excerpt=generated_content_data['excerpt'],
                    meta_description=generated_content_data['meta_description'],
                    tags=generated_content_data['tags'],
                    category=configurator.default_category,
                    status='published',  # Crear como publicado para que sea visible
                    created_by=author
                )
                
                posts_created += 1
                generated_content.append(f"Post ID: {blog_post.id} - Título: {generated_content_data['title']}")
                
                # Asociar el post al log
                if 'created_posts' not in result:
                    result['created_posts'] = []
                result['created_posts'].append(blog_post.id)
                
            except Exception as e:
                # Log del error pero continuar con los siguientes posts
                print(f"Error generando post {i+1}: {str(e)}")
                continue
        
        # Actualizar estadísticas del configurador
        configurator.total_posts_generated = (configurator.total_posts_generated or 0) + posts_created
        configurator.last_run = timezone.now()
        configurator.save()
        
        # Preparar resultado
        result['success'] = posts_created > 0
        result['posts_created'] = posts_created
        result['keywords_used'] = keywords_used
        result['generated_content'] = generated_content
        
        if posts_created == 0:
            result['error'] = 'No se pudo generar ningún post'
            
    except Exception as e:
        result['error'] = str(e)
    
    finally:
        # Calcular tiempo de ejecución
        result['execution_time'] = round(time.time() - start_time, 2)
        
        # Crear log de la ejecución (uno por cada keyword intentada)
        keywords_used = result.get('keywords_used', [])
        created_posts = result.get('created_posts', [])
        for i, keyword in enumerate(keywords_used):
            # Determinar el post asociado si existe
            associated_post_id = created_posts[i] if i < len(created_posts) else None
            
            AIBlogGenerationLog.objects.create(
                configurator=configurator,
                generation_status='success' if result['success'] and associated_post_id else 'error',
                error_message=result.get('error') if not (result['success'] and associated_post_id) else '',
                keyword_used=keyword,
                execution_time_seconds=result['execution_time'],
                generated_post_id=associated_post_id,
                prompt_used=f"Generar contenido sobre: {keyword}"
            )
    
    return result


def generate_blog_post_content(configurator, keyword):
    """
    Genera el contenido de un post de blog usando OpenAI
    """
    try:
        # Obtener API key desde configuración del sistema
        config = SystemConfiguration.get_config()
        api_key = getattr(config, 'openai_api_key', None)
        
        if not api_key:
            print("API key de OpenAI no configurada en configuración del sistema")
            return generate_test_blog_content(keyword)
        
        # Configurar cliente OpenAI
        client = OpenAI(api_key=api_key)
        
        # Definir prompts según la configuración
        content_length_map = {
            'short': '300-500 palabras',
            'medium': '500-800 palabras', 
            'long': '800-1200 palabras'
        }
        
        content_style_map = {
            'professional': 'profesional y formal',
            'casual': 'casual y cercano',
            'technical': 'técnico y detallado',
            'educational': 'educativo y didáctico'
        }
        
        length = content_length_map.get(configurator.content_length, '500-800 palabras')
        style = content_style_map.get(configurator.content_style, 'profesional')
        
        # Usar template personalizado si existe, sino uno por defecto
        if configurator.topic_template:
            topic_prompt = configurator.topic_template.replace('{keyword}', keyword)
        else:
            topic_prompt = f"Crear un artículo informativo y útil sobre {keyword}"
        
        # Obtener títulos existentes para evitar duplicados
        existing_titles = list(BlogPost.objects.values_list('title', flat=True).order_by('-created_at')[:50])
        titles_text = "\n".join([f"- {title}" for title in existing_titles]) if existing_titles else "- No hay títulos previos"
        
        # Prompt para generar el título
        title_prompt = f"""
        Genera un título atractivo y optimizado para SEO para un artículo de blog sobre "{keyword}".
        El título debe ser:
        - Atractivo y llamativo
        - Máximo 60 caracteres
        - Incluir la palabra clave principal
        - En español
        - COMPLETAMENTE DIFERENTE a los títulos existentes
        
        TÍTULOS EXISTENTES A EVITAR:
        {titles_text}
        
        IMPORTANTE: No copies ni uses títulos similares a los de la lista anterior. Crea algo completamente original y único.
        
        Responde solo con el título, sin comillas ni explicaciones.
        """
        
        # Generar título
        title_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": title_prompt}],
            max_tokens=100,
            temperature=0.7
        )
        
        title = title_response.choices[0].message.content.strip()
        
        # Prompt para generar el contenido
        content_prompt = f"""
        Escribe un artículo de blog completo y de alta calidad sobre "{keyword}" con el título "{title}".
        
        Especificaciones:
        - Longitud: {length}
        - Estilo: {style}
        - Idioma: Español
        - FORMATO: Solo texto plano, sin ningún tipo de formato
        - NO usar símbolos de formato: #, ##, ###, *, **, ***, -, _, `, etc.
        - NO usar markdown, HTML, o cualquier otro formato
        - Organizar SOLO con saltos de línea dobles entre párrafos
        - Escribir como si fuera un documento de texto simple
        - Incluir ejemplos prácticos cuando sea relevante
        - Optimizado para SEO
        - Contenido original y útil
        - ENFOQUE ÚNICO: Asegúrate de que el enfoque y contenido sea diferente a otros artículos sobre el mismo tema
        
        TÍTULOS DE ARTÍCULOS EXISTENTES A DIFERENCIARSE:
        {titles_text}
        
        Instrucción específica: {topic_prompt}
        
        IMPORTANTE: 
        1. Crea contenido completamente original que aporte valor único
        2. NUNCA uses símbolos de formato como *, #, -, etc.
        3. Solo texto plano con párrafos separados por líneas en blanco
        4. Escribe como si estuvieras en un editor de texto simple
        
        Formato: Párrafos de texto plano separados por líneas en blanco.
        """
        
        # Generar contenido
        content_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": content_prompt}],
            max_tokens=2000,
            temperature=0.7
        )
        
        content = content_response.choices[0].message.content.strip()
        
        # Limpiar cualquier formato Markdown que pueda haberse colado
        content = clean_markdown_formatting(content)
        
        # Generar excerpt (resumen)
        excerpt_prompt = f"""
        Basándote en este artículo, crea un resumen atractivo de máximo 160 caracteres que sirva como excerpt:
        
        {content[:500]}...
        
        El resumen debe ser atractivo y motivar a leer el artículo completo.
        Responde solo con el resumen, sin comillas ni explicaciones.
        """
        
        excerpt_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": excerpt_prompt}],
            max_tokens=100,
            temperature=0.7
        )
        
        excerpt = excerpt_response.choices[0].message.content.strip()
        
        # Generar meta descripción
        meta_prompt = f"""
        Crea una meta descripción SEO de máximo 155 caracteres para un artículo titulado "{title}" sobre {keyword}.
        Debe ser atractiva e incluir la palabra clave principal.
        Responde solo con la meta descripción, sin comillas.
        """
        
        meta_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": meta_prompt}],
            max_tokens=100,
            temperature=0.7
        )
        
        meta_description = meta_response.choices[0].message.content.strip()
        
        # Generar tags
        tags_prompt = f"""
        Genera 5-8 tags relevantes para un artículo sobre "{keyword}".
        Los tags deben ser:
        - Relevantes al contenido
        - Útiles para SEO
        - En minúsculas
        - Separados por comas
        
        Responde solo con los tags separados por comas, sin explicaciones.
        """
        
        tags_response = client.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[{"role": "user", "content": tags_prompt}],
            max_tokens=150,
            temperature=0.7
        )
        
        tags = tags_response.choices[0].message.content.strip()
        
        return {
            'title': title,
            'content': content,
            'excerpt': excerpt,
            'meta_description': meta_description,
            'tags': tags
        }
        
    except Exception as e:
        print(f"Error generando contenido con IA: {str(e)}")
        # Generar contenido de prueba si OpenAI falla
        return generate_test_blog_content(keyword)


def generate_test_blog_content(keyword):
    """
    Genera contenido de prueba sin usar OpenAI para testing
    """
    return {
        'title': f"Guía Completa sobre {keyword.title()}",
        'content': f"""Introducción a {keyword.title()}

En este artículo completo, exploraremos todo lo que necesitas saber sobre {keyword}. Desde conceptos básicos hasta aplicaciones avanzadas.

¿Qué es {keyword.title()}?

{keyword.title()} es un tema fascinante que ha ganado mucha relevancia en los últimos años. Su importancia radica en su capacidad para transformar la manera en que trabajamos y nos organizamos.

Beneficios Principales

Eficiencia mejorada: Una de las principales ventajas de implementar {keyword} es la notable mejora en la eficiencia operativa.

Facilidad de uso: {keyword.title()} es accesible para usuarios de todos los niveles de experiencia técnica.

Resultados comprobados: Existen numerosos casos de éxito documentados que demuestran la efectividad de esta solución.

Implementación Práctica

Para comenzar con {keyword}, te recomendamos seguir estos pasos fundamentales:

Paso 1: Preparación inicial
Antes de comenzar, asegúrate de tener todos los recursos necesarios y un plan claro de implementación.

Paso 2: Configuración
El proceso de configuración incluye la personalización según las necesidades específicas de tu organización.

Paso 3: Puesta en marcha
Una vez configurado correctamente, puedes proceder con la implementación gradual del sistema.

Mejores Prácticas

Mantén siempre la documentación actualizada para facilitar el mantenimiento y las futuras actualizaciones.

Realiza pruebas regulares para asegurar que todo funcione correctamente y detectar posibles problemas.

Capacita a tu equipo adecuadamente para maximizar el aprovechamiento de las funcionalidades disponibles.

Conclusión

{keyword.title()} representa una excelente oportunidad para mejorar los procesos y obtener mejores resultados. Su implementación correcta puede generar beneficios significativos para cualquier organización que busque modernizar sus operaciones.

¿Estás listo para comenzar tu aventura con {keyword}? No esperes más y da el primer paso hacia la transformación digital.""",
        'excerpt': f"Descubre todo sobre {keyword} en esta guía completa. Aprende desde lo básico hasta técnicas avanzadas con ejemplos prácticos.",
        'meta_description': f"Guía completa sobre {keyword}: conceptos, beneficios, implementación y mejores prácticas. Todo lo que necesitas saber.",
        'tags': f"{keyword}, guía, tutorial, mejores prácticas, implementación"
    }


def clean_markdown_formatting(content):
    """
    Elimina cualquier formato Markdown que pueda haberse colado en el contenido
    """
    import re
    
    # Eliminar headers (# ## ###)
    content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
    
    # Eliminar texto en negrita (**texto** o __texto__)
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
    content = re.sub(r'__(.*?)__', r'\1', content)
    
    # Eliminar texto en cursiva (*texto* o _texto_)
    content = re.sub(r'\*(.*?)\*', r'\1', content)
    content = re.sub(r'_(.*?)_', r'\1', content)
    
    # Eliminar listas con guiones o asteriscos
    content = re.sub(r'^[\s]*[-\*\+]\s+', '', content, flags=re.MULTILINE)
    
    # Eliminar listas numeradas
    content = re.sub(r'^\d+\.\s+', '', content, flags=re.MULTILINE)
    
    # Eliminar código en línea (`código`)
    content = re.sub(r'`(.*?)`', r'\1', content)
    
    # Eliminar bloques de código (```código```)
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    
    # Eliminar enlaces [texto](url)
    content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
    
    # Eliminar líneas horizontales (--- o ***)
    content = re.sub(r'^[\s]*[-\*]{3,}[\s]*$', '', content, flags=re.MULTILINE)
    
    # Limpiar espacios múltiples y líneas vacías excesivas
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    content = re.sub(r'[ \t]+', ' ', content)
    
    return content.strip()