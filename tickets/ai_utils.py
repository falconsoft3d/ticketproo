"""
Utilidades de IA para mejorar contenido del blog
"""
import requests
import json
import logging
import os
import urllib.request
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from .models import SystemConfiguration

logger = logging.getLogger(__name__)


class AIContentOptimizer:
    """Clase para optimizar contenido usando IA"""
    
    def __init__(self):
        self.api_key = self._get_openai_api_key()
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    def _get_openai_api_key(self):
        """Obtener API key de OpenAI desde configuración del sistema"""
        try:
            config = SystemConfiguration.get_config()
            return getattr(config, 'openai_api_key', None)
        except:
            return None
    
    def _make_ai_request(self, messages, max_tokens=500, temperature=0.7):
        """Hacer petición a la API de OpenAI"""
        if not self.api_key:
            return {"error": "API key de OpenAI no configurada"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en petición AI: {e}")
            return {"error": f"Error de conexión: {str(e)}"}
        except Exception as e:
            logger.error(f"Error inesperado en AI: {e}")
            return {"error": f"Error inesperado: {str(e)}"}
    
    def improve_content(self, title, content):
        """Mejorar el contenido del artículo"""
        messages = [
            {
                "role": "system",
                "content": """Eres un experto editor de contenido. Tu tarea es mejorar artículos de blog 
                manteniendo el mensaje original pero haciéndolos más claros, atractivos y profesionales. 
                Mejora la estructura, gramática, y añade valor sin cambiar el tema principal.
                IMPORTANTE: No uses formato Markdown. Usa solo texto plano con saltos de línea."""
            },
            {
                "role": "user",
                "content": f"""Mejora este artículo del blog:

Título: {title}

Contenido:
{content}

Instrucciones:
1. Mantén el tema y mensaje original
2. Mejora la estructura, gramática y fluidez
3. Usa subtítulos en MAYÚSCULAS (sin # ni ##)
4. NO uses formato Markdown - solo texto plano con saltos de línea

Por favor, devuelve únicamente el contenido mejorado sin formato Markdown."""
            }
        ]
        
        response = self._make_ai_request(messages, max_tokens=1000)
        
        if "error" in response:
            return response
        
        try:
            improved_content = response['choices'][0]['message']['content']
            return {"success": True, "content": improved_content}
        except (KeyError, IndexError) as e:
            return {"error": "Respuesta inválida de la API"}
    
    def generate_meta_description(self, title, content):
        """Generar meta descripción para SEO"""
        messages = [
            {
                "role": "system",
                "content": """Eres un experto en SEO. Crea meta descripciones atractivas de máximo 160 caracteres 
                que describan el contenido del artículo de manera convincente para los motores de búsqueda."""
            },
            {
                "role": "user",
                "content": f"""Crea una meta descripción SEO para este artículo:

Título: {title}
Contenido: {content[:500]}...

La meta descripción debe tener máximo 160 caracteres, ser atractiva y describir el valor del artículo."""
            }
        ]
        
        response = self._make_ai_request(messages, max_tokens=200)
        
        if "error" in response:
            return response
        
        try:
            meta_description = response['choices'][0]['message']['content'].strip()
            # Asegurar que no exceda 160 caracteres
            if len(meta_description) > 160:
                meta_description = meta_description[:157] + "..."
            return {"success": True, "meta_description": meta_description}
        except (KeyError, IndexError):
            return {"error": "Respuesta inválida de la API"}
    
    def suggest_titles(self, content):
        """Sugerir títulos alternativos"""
        messages = [
            {
                "role": "system",
                "content": """Eres un experto en marketing de contenidos. Crea títulos atractivos y llamativos 
                que generen clicks pero sean precisos sobre el contenido. Los títulos deben ser SEO-friendly."""
            },
            {
                "role": "user",
                "content": f"""Basándote en este contenido, sugiere 5 títulos alternativos atractivos:

Contenido: {content[:600]}...

Los títulos deben ser:
- Atractivos y llamativos
- Precisos sobre el contenido
- Optimizados para SEO
- Entre 40-60 caracteres

Devuelve solo los 5 títulos, uno por línea, sin numeración."""
            }
        ]
        
        response = self._make_ai_request(messages, max_tokens=300)
        
        if "error" in response:
            return response
        
        try:
            suggestions = response['choices'][0]['message']['content'].strip()
            titles_list = [title.strip() for title in suggestions.split('\n') if title.strip()]
            return {"success": True, "titles": titles_list[:5]}
        except (KeyError, IndexError):
            return {"error": "Respuesta inválida de la API"}
    
    def generate_tags(self, title, content):
        """Generar etiquetas/tags relevantes"""
        messages = [
            {
                "role": "system",
                "content": """Eres un experto en clasificación de contenido. Genera tags relevantes 
                para artículos de blog que ayuden con la organización y SEO."""
            },
            {
                "role": "user",
                "content": f"""Genera tags relevantes para este artículo:

Título: {title}
Contenido: {content[:500]}...

Genera 5-8 tags en español que sean:
- Relevantes al contenido
- Útiles para SEO
- Una o dos palabras máximo por tag
- Sin caracteres especiales

Devuelve solo los tags separados por comas."""
            }
        ]
        
        response = self._make_ai_request(messages, max_tokens=200)
        
        if "error" in response:
            return response
        
        try:
            tags = response['choices'][0]['message']['content'].strip()
            # Limpiar y formatear tags
            tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            clean_tags = ', '.join(tags_list[:8])
            return {"success": True, "tags": clean_tags}
        except (KeyError, IndexError):
            return {"error": "Respuesta inválida de la API"}
    
    def analyze_readability(self, content):
        """Analizar legibilidad del contenido"""
        messages = [
            {
                "role": "system",
                "content": """Eres un experto en análisis de legibilidad. Analiza textos y proporciona 
                feedback sobre qué tan fácil es leerlos y cómo mejorarlos."""
            },
            {
                "role": "user",
                "content": f"""Analiza la legibilidad de este contenido y proporciona sugerencias de mejora:

{content}

Proporciona:
1. Puntuación de legibilidad (1-10)
2. 3-5 sugerencias específicas para mejorar
3. Aspectos positivos encontrados

Formato de respuesta:
PUNTUACIÓN: X/10
SUGERENCIAS:
- [sugerencia 1]
- [sugerencia 2]
- [etc]
ASPECTOS POSITIVOS:
- [aspecto 1]
- [aspecto 2]"""
            }
        ]
        
        response = self._make_ai_request(messages, max_tokens=500)
        
        if "error" in response:
            return response
        
        try:
            analysis = response['choices'][0]['message']['content']
            return {"success": True, "analysis": analysis}
        except (KeyError, IndexError):
            return {"error": "Respuesta inválida de la API"}
    
    def improve_complete_article(self, title, content):
        """Mejorar completamente el artículo basándose en el título"""
        messages = [
            {
                "role": "system",
                "content": """Eres un experto editor de contenido y especialista en marketing digital. 
                Tu tarea es crear contenido de blog de alta calidad, atractivo y optimizado para SEO.
                Debes mejorar tanto el título como el contenido del artículo.
                IMPORTANTE: No uses formato Markdown. Usa solo texto plano con saltos de línea."""
            },
            {
                "role": "user",
                "content": f"""Mejora completamente este artículo de blog:

Título actual: {title}
Contenido actual: {content}

Instrucciones:
1. Crea un nuevo título atractivo, SEO-friendly y que genere clicks
2. Mejora y expande el contenido manteniendo el tema principal
3. Estructura el contenido con subtítulos usando MAYÚSCULAS (sin # ni ##)
4. Añade valor, ejemplos prácticos y información útil
5. Optimiza para SEO sin sacrificar calidad
6. Mantén un tono profesional pero accesible
7. NO uses formato Markdown - solo texto plano con saltos de línea

Formato de respuesta (sin Markdown):
TÍTULO MEJORADO: [nuevo título]

CONTENIDO MEJORADO:
[contenido mejorado con estructura clara usando solo texto y saltos de línea]"""
            }
        ]
        
        response = self._make_ai_request(messages, max_tokens=1500, temperature=0.8)
        
        if "error" in response:
            return response
        
        try:
            improved_text = response['choices'][0]['message']['content']
            
            # Extraer título y contenido mejorados
            lines = improved_text.split('\n')
            new_title = ""
            new_content = ""
            
            content_started = False
            for line in lines:
                if line.startswith('TÍTULO MEJORADO:'):
                    new_title = line.replace('TÍTULO MEJORADO:', '').strip()
                elif line.startswith('CONTENIDO MEJORADO:'):
                    content_started = True
                elif content_started:
                    new_content += line + '\n'
            
            # Limpiar contenido
            new_content = new_content.strip()
            
            if not new_title:
                # Si no se pudo extraer el título, usar el original
                new_title = title
            
            if not new_content:
                # Si no se pudo extraer el contenido, usar la respuesta completa
                new_content = improved_text
            
            return {
                "success": True,
                "title": new_title,
                "content": new_content,
                "full_response": improved_text
            }
            
        except (KeyError, IndexError) as e:
            return {"error": "Respuesta inválida de la API"}
    
    def generate_article_image(self, title, content=""):
        """Generar imagen para el artículo basándose en el título"""
        try:
            config = SystemConfiguration.get_config()
            if not config.openai_api_key:
                return {"error": "API Key de OpenAI no configurada"}
            
            # Crear prompt para DALL-E
            prompt = f"""Crea una imagen profesional y atractiva para un artículo de blog titulado: "{title}"
            
La imagen debe ser:
- Moderna y profesional
- Relacionada con el tema del artículo
- Adecuada para un blog corporativo
- Sin texto superpuesto
- Estilo limpio y minimalista
- Colores armoniosos y atractivos"""
            
            # Llamada a DALL-E
            headers = {
                "Authorization": f"Bearer {config.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": "standard",
                "style": "natural"
            }
            
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"Error en DALL-E: {response.status_code} - {response.text}")
                return {"error": f"Error en la generación de imagen: {response.status_code}"}
            
            result = response.json()
            image_url = result['data'][0]['url']
            
            # Descargar y guardar la imagen
            image_response = urllib.request.urlopen(image_url)
            image_content = image_response.read()
            
            # Crear nombre de archivo único
            import uuid
            filename = f"blog_images/{uuid.uuid4()}.png"
            
            # Guardar la imagen
            file_path = default_storage.save(filename, ContentFile(image_content))
            
            return {
                "success": True,
                "image_url": image_url,
                "file_path": file_path,
                "local_url": default_storage.url(file_path)
            }
            
        except Exception as e:
            logger.error(f"Error generando imagen: {e}")
            return {"error": f"Error generando imagen: {str(e)}"}


def test_ai_connection():
    """Probar la conexión con la API de IA"""
    optimizer = AIContentOptimizer()
    
    if not optimizer.api_key:
        return {"success": False, "message": "API key de OpenAI no configurada"}
    
    # Test simple
    response = optimizer._make_ai_request([
        {"role": "user", "content": "Responde solo 'OK' si puedes leerme"}
    ], max_tokens=10)
    
    if "error" in response:
        return {"success": False, "message": response["error"]}
    
    try:
        content = response['choices'][0]['message']['content']
        return {"success": True, "message": "Conexión exitosa con IA"}
    except:
        return {"success": False, "message": "Respuesta inválida de la API"}


class AudioTranscriber:
    """Clase para transcribir audio usando IA"""
    
    def __init__(self):
        self.api_key = self._get_openai_api_key()
        self.whisper_url = "https://api.openai.com/v1/audio/transcriptions"
    
    def _get_openai_api_key(self):
        """Obtener API key de OpenAI desde configuración del sistema"""
        try:
            config = SystemConfiguration.get_config()
            return getattr(config, 'openai_api_key', None)
        except:
            return None
    
    def transcribe_audio_file(self, audio_file_path, language='es'):
        """Transcribir archivo de audio usando Whisper API"""
        if not self.api_key:
            return {
                "success": False, 
                "error": "API key de OpenAI no configurada",
                "transcription": "",
                "confidence": 0.0
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            # Abrir el archivo de audio
            with open(audio_file_path, 'rb') as audio_file:
                files = {
                    'file': audio_file,
                    'model': (None, 'whisper-1'),
                    'language': (None, language),
                    'response_format': (None, 'verbose_json')
                }
                
                response = requests.post(
                    self.whisper_url, 
                    headers=headers, 
                    files=files,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "transcription": result.get('text', ''),
                        "confidence": self._calculate_confidence(result),
                        "language": result.get('language', language),
                        "duration": result.get('duration', 0)
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Error de API: {response.status_code} - {response.text}",
                        "transcription": "",
                        "confidence": 0.0
                    }
                    
        except Exception as e:
            logger.error(f"Error transcribiendo audio: {str(e)}")
            return {
                "success": False,
                "error": f"Error transcribiendo audio: {str(e)}",
                "transcription": "",
                "confidence": 0.0
            }
    
    def _calculate_confidence(self, whisper_result):
        """Calcular confianza aproximada basada en los segmentos"""
        try:
            segments = whisper_result.get('segments', [])
            if not segments:
                return 85.0  # Confianza por defecto si no hay segmentos
            
            # Promedio de confianza de palabras si está disponible
            total_confidence = 0
            word_count = 0
            
            for segment in segments:
                words = segment.get('words', [])
                for word in words:
                    if 'probability' in word:
                        total_confidence += word['probability']
                        word_count += 1
            
            if word_count > 0:
                return (total_confidence / word_count) * 100
            else:
                # Si no hay datos de confianza, usar estimación basada en duración vs texto
                text_length = len(whisper_result.get('text', ''))
                duration = whisper_result.get('duration', 1)
                words_per_second = (text_length / 5) / duration  # Aproximado
                
                # Más palabras por segundo generalmente significa mejor transcripción
                if words_per_second > 2:
                    return 90.0
                elif words_per_second > 1:
                    return 80.0
                else:
                    return 70.0
                    
        except Exception:
            return 75.0  # Confianza por defecto en caso de error
    
    def improve_transcription_with_ai(self, transcription_text, context_hint=""):
        """Mejorar transcripción usando GPT para corregir errores"""
        if not self.api_key or not transcription_text.strip():
            return transcription_text
        
        content_optimizer = AIContentOptimizer()
        
        prompt = f"""Por favor, corrige y mejora la siguiente transcripción de audio manteniendo el significado original.
        
Corrige errores ortográficos, gramaticales y de puntuación, pero mantén el estilo natural del habla.
No agregues información que no esté en el texto original.

{f"Contexto: {context_hint}" if context_hint else ""}

Transcripción original:
{transcription_text}

Transcripción corregida:"""

        messages = [
            {"role": "system", "content": "Eres un experto en corrección de transcripciones de audio. Tu trabajo es corregir errores manteniendo el significado y estilo original."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = content_optimizer._make_ai_request(messages, max_tokens=1000, temperature=0.3)
            
            if "error" not in response:
                improved_text = response['choices'][0]['message']['content'].strip()
                return improved_text
            else:
                logger.warning(f"Error mejorando transcripción: {response['error']}")
                return transcription_text
                
        except Exception as e:
            logger.error(f"Error mejorando transcripción con IA: {str(e)}")
            return transcription_text


def transcribe_recording(recording_id):
    """Función auxiliar para transcribir una grabación específica"""
    from .models import Recording
    
    try:
        recording = Recording.objects.get(id=recording_id)
        
        # Cambiar estado a procesando
        recording.transcription_status = 'processing'
        recording.save()
        
        transcriber = AudioTranscriber()
        
        # Obtener ruta absoluta del archivo
        audio_path = recording.audio_file.path
        
        # Transcribir
        result = transcriber.transcribe_audio_file(audio_path, 'es')
        
        if result['success']:
            # Mejorar transcripción con IA
            context = f"Título: {recording.title}. Descripción: {recording.description}"
            improved_text = transcriber.improve_transcription_with_ai(
                result['transcription'], 
                context
            )
            
            # Actualizar grabación
            recording.transcription_text = improved_text
            recording.transcription_confidence = result['confidence']
            recording.transcription_language = result.get('language', 'es')
            recording.transcription_status = 'completed'
            recording.transcribed_at = timezone.now()
            recording.save()
            
            logger.info(f"Transcripción completada para grabación {recording_id}")
            return {
                "success": True,
                "transcription": improved_text,
                "confidence": result['confidence']
            }
        else:
            # Error en transcripción
            recording.transcription_status = 'failed'
            recording.save()
            
            logger.error(f"Error transcribiendo grabación {recording_id}: {result['error']}")
            return {
                "success": False,
                "error": result['error']
            }
            
    except Recording.DoesNotExist:
        return {"success": False, "error": "Grabación no encontrada"}
    except Exception as e:
        logger.error(f"Error en transcripción de grabación {recording_id}: {str(e)}")
        return {"success": False, "error": str(e)}


class VoiceCommandProcessor:
    """Procesador de comandos de voz para crear tickets automáticamente"""
    
    def __init__(self):
        self.transcriber = AudioTranscriber()
    
    def process_voice_command(self, audio_file_path, user):
        """
        Procesa un comando de voz y extrae información para crear un ticket
        
        Args:
            audio_file_path (str): Ruta al archivo de audio
            user: Usuario que hace el comando
            
        Returns:
            dict: Resultado del procesamiento con información del ticket
        """
        try:
            # 1. Transcribir el audio
            transcription_result = self.transcriber.transcribe_audio_file(audio_file_path)
            
            if not transcription_result.get('success'):
                return {
                    "success": False, 
                    "error": f"Error en transcripción: {transcription_result.get('error', 'Desconocido')}"
                }
            
            command_text = transcription_result['transcription']
            
            # 2. Analizar el comando con IA para extraer información del ticket
            ticket_info = self._extract_ticket_info_from_command(command_text, user)
            
            if not ticket_info.get('success'):
                return ticket_info
            
            # 3. Crear el ticket automáticamente
            ticket_result = self._create_ticket_from_info(ticket_info['ticket_data'], user)
            
            return {
                "success": True,
                "transcription": command_text,
                "ticket_info": ticket_info['ticket_data'],
                "ticket": ticket_result
            }
            
        except Exception as e:
            logger.error(f"Error procesando comando de voz: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _extract_ticket_info_from_command(self, command_text, user):
        """
        Usa GPT para extraer información estructurada del comando de voz
        """
        try:
            # Obtener contexto del usuario para mejorar el análisis
            user_context = self._get_user_context(user)
            
            messages = [
                {
                    "role": "system",
                    "content": """Eres un asistente especializado en extraer información de comandos de voz para crear tickets de soporte técnico.

Tu tarea es analizar el comando de voz y extraer la siguiente información en formato JSON:
{
    "title": "Título descriptivo del problema",
    "description": "Descripción detallada del problema",
    "priority": "baja|media|alta|critica",
    "category": "categoria_detectada",
    "urgency": "baja|media|alta",
    "tags": ["tag1", "tag2", "tag3"],
    "estimated_time": "tiempo_estimado_en_minutos",
    "action_required": "accion_sugerida"
}

Reglas importantes:
- El título debe ser conciso pero descriptivo (máximo 100 caracteres)
- La descripción debe incluir todos los detalles mencionados
- La prioridad debe basarse en la urgencia y impacto descritos
- Las categorías pueden ser: técnico, soporte, facturación, general, desarrollo, infraestructura
- Los tags deben ser palabras clave relevantes (máximo 5)
- El tiempo estimado debe ser realista en minutos
- La acción sugerida debe ser específica y práctica

Si el comando no es claro o no contiene suficiente información, indica qué información falta."""
                },
                {
                    "role": "user",
                    "content": f"""Analiza este comando de voz para crear un ticket:

Comando: "{command_text}"

Contexto del usuario:
{user_context}

Extrae la información del ticket en formato JSON válido."""
                }
            ]
            
            # Configurar OpenAI client
            from .models import SystemConfiguration
            config = SystemConfiguration.get_config()
            
            if not config.openai_api_key:
                return {"success": False, "error": "API key de OpenAI no configurada"}
            
            import openai
            client = openai.OpenAI(api_key=config.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=800,
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Intentar parsear el JSON
            import json
            try:
                # Extraer JSON del texto de respuesta
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    ticket_data = json.loads(json_str)
                    
                    # Validar que tiene los campos requeridos
                    required_fields = ['title', 'description', 'priority']
                    for field in required_fields:
                        if field not in ticket_data:
                            return {
                                "success": False, 
                                "error": f"Campo requerido faltante: {field}"
                            }
                    
                    return {"success": True, "ticket_data": ticket_data}
                else:
                    return {
                        "success": False, 
                        "error": "No se pudo extraer información estructurada del comando"
                    }
                    
            except json.JSONDecodeError as e:
                return {
                    "success": False, 
                    "error": f"Error parseando respuesta de IA: {str(e)}"
                }
            
        except Exception as e:
            logger.error(f"Error extrayendo información del ticket: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_user_context(self, user):
        """Obtiene contexto relevante del usuario para mejorar el análisis"""
        try:
            context_parts = [
                f"Usuario: {user.get_full_name() or user.username}",
                f"Email: {user.email}",
            ]
            
            # Agregar información de perfil si existe
            if hasattr(user, 'userprofile'):
                profile = user.userprofile
                if profile.company:
                    context_parts.append(f"Empresa: {profile.company.name}")
                if profile.position:
                    context_parts.append(f"Cargo: {profile.position}")
            
            # Agregar estadísticas de tickets recientes si es posible
            from .models import Ticket
            recent_tickets = Ticket.objects.filter(
                created_by=user
            ).order_by('-created_at')[:3]
            
            if recent_tickets.exists():
                context_parts.append("Tickets recientes:")
                for ticket in recent_tickets:
                    context_parts.append(f"- {ticket.title} ({ticket.category})")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.warning(f"Error obteniendo contexto del usuario: {str(e)}")
            return f"Usuario: {user.username}"
    
    def _create_ticket_from_info(self, ticket_data, user):
        """
        Crea un ticket real en el sistema usando la información extraída
        """
        try:
            from .models import Ticket, Category, Company
            
            # Buscar o crear categoría
            category_name = ticket_data.get('category', 'general')
            category, created = Category.objects.get_or_create(
                name__iexact=category_name,
                defaults={'name': category_name.title(), 'description': f'Categoría creada automáticamente: {category_name}'}
            )
            
            # Obtener empresa del usuario si existe
            company = None
            if hasattr(user, 'userprofile') and user.userprofile.company:
                company = user.userprofile.company
            
            # Mapear prioridad textual a las opciones del modelo
            priority_map = {
                'baja': 'low',
                'media': 'medium', 
                'alta': 'high',
                'critica': 'urgent',
                'crítica': 'urgent'
            }
            
            # Crear el ticket
            try:
                # Validar y convertir tiempo estimado
                estimated_time = ticket_data.get('estimated_time', 60)
                if isinstance(estimated_time, str):
                    # Extraer números de la cadena
                    import re
                    numbers = re.findall(r'\d+', estimated_time)
                    estimated_time = int(numbers[0]) if numbers else 60
                elif not isinstance(estimated_time, (int, float)):
                    estimated_time = 60
                
                hours_estimated = float(estimated_time) / 60.0
                
                ticket = Ticket.objects.create(
                    title=ticket_data['title'][:200],  # Limitar longitud
                    description=ticket_data['description'],
                    priority=priority_map.get(ticket_data.get('priority', 'media').lower(), 'medium'),
                    category=category,
                    company=company,
                    created_by=user,
                    assigned_to=None,  # Se asignará automáticamente según reglas
                    status='open',
                    hours=hours_estimated,  # Convertir minutos a horas
                )
            except Exception as e:
                logger.error(f"Error creando ticket: {str(e)}")
                return {"success": False, "error": f"Error creando ticket: {str(e)}"}
            
            # Generar número de ticket si no existe
            if not ticket.ticket_number:
                ticket.generate_ticket_number()
                ticket.save()
            
            logger.info(f"Ticket creado automáticamente por comando de voz: {ticket.id}")
            
            return {
                "success": True,
                "ticket_id": ticket.id,
                "ticket_number": ticket.ticket_number or f"T-{ticket.id}",
                "title": ticket.title
            }
            
        except Exception as e:
            logger.error(f"Error creando ticket: {str(e)}")
            return {"success": False, "error": str(e)}


# ============================================
# FUNCIONES DE TRANSCRIPCIÓN DE REUNIONES
# ============================================

def transcribe_meeting_async(meeting_id):
    """
    Transcribir reunión de forma asíncrona
    """
    import threading
    thread = threading.Thread(target=transcribe_meeting, args=(meeting_id,))
    thread.daemon = True
    thread.start()


def transcribe_meeting(meeting_id):
    """
    Transcribir archivo de reunión usando OpenAI Whisper
    """
    from .models import VideoMeeting, SystemConfiguration
    
    try:
        meeting = VideoMeeting.objects.get(id=meeting_id)
        config = SystemConfiguration.objects.first()
        
        if not config or not config.openai_api_key:
            logger.error("OpenAI API key no configurada")
            meeting.transcription_status = 'failed'
            meeting.save()
            return False
        
        if not meeting.recording_file:
            logger.error("No hay archivo de grabación")
            meeting.transcription_status = 'failed'
            meeting.save()
            return False
        
        # Marcar como procesando
        meeting.transcription_status = 'processing'
        meeting.save()
        
        # Preparar archivo para OpenAI
        file_path = meeting.recording_file.path
        
        # Verificar si el archivo existe
        if not os.path.exists(file_path):
            logger.error(f"Archivo no encontrado: {file_path}")
            meeting.transcription_status = 'failed'
            meeting.save()
            return False
        
        # Transcribir con OpenAI Whisper
        headers = {
            "Authorization": f"Bearer {config.openai_api_key}"
        }
        
        with open(file_path, 'rb') as audio_file:
            files = {
                'file': audio_file,
                'model': (None, 'whisper-1'),
                'language': (None, 'es'),  # Español
                'response_format': (None, 'json')
            }
            
            response = requests.post(
                'https://api.openai.com/v1/audio/transcriptions',
                headers=headers,
                files=files,
                timeout=300  # 5 minutos timeout
            )
        
        if response.status_code == 200:
            transcription_data = response.json()
            transcription_text = transcription_data.get('text', '')
            
            # Guardar transcripción
            meeting.transcription_text = transcription_text
            meeting.transcription_status = 'completed'
            
            # Generar resumen y puntos clave con IA
            if transcription_text:
                try:
                    ai_analysis = analyze_meeting_content(transcription_text, config.openai_api_key)
                    if ai_analysis:
                        meeting.ai_summary = ai_analysis.get('summary', '')
                        meeting.key_points = ai_analysis.get('key_points', '')
                        meeting.action_items = ai_analysis.get('action_items', '')
                except Exception as e:
                    logger.error(f"Error generando análisis de IA: {str(e)}")
            
            meeting.save()
            logger.info(f"Transcripción completada para reunión {meeting_id}")
            return True
            
        else:
            logger.error(f"Error en transcripción: {response.status_code} - {response.text}")
            meeting.transcription_status = 'failed'
            meeting.save()
            return False
            
    except VideoMeeting.DoesNotExist:
        logger.error(f"Reunión {meeting_id} no encontrada")
        return False
    except Exception as e:
        logger.error(f"Error transcribiendo reunión {meeting_id}: {str(e)}")
        try:
            meeting = VideoMeeting.objects.get(id=meeting_id)
            meeting.transcription_status = 'failed'
            meeting.save()
        except:
            pass
        return False


def analyze_meeting_content(transcription_text, api_key):
    """
    Analizar contenido de la transcripción para generar resumen y puntos clave
    """
    try:
        prompt = f"""
Analiza la siguiente transcripción de reunión y proporciona:

1. Un resumen ejecutivo conciso (máximo 200 palabras)
2. Los puntos clave discutidos (formato de lista con viñetas)
3. Los elementos de acción identificados (formato de checklist con responsables cuando sea posible)

Transcripción:
{transcription_text}

Por favor, responde en formato JSON con las siguientes claves:
- summary: resumen ejecutivo
- key_points: puntos clave (formato markdown con viñetas)
- action_items: elementos de acción (formato markdown con checkboxes)
"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un asistente especializado en análisis de reuniones. Genera resúmenes claros y actionables."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.3
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']
            
            # Intentar parsear como JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Si no es JSON válido, estructurar manualmente
                return {
                    'summary': content[:500] + '...' if len(content) > 500 else content,
                    'key_points': '- Análisis disponible en el contenido de respuesta',
                    'action_items': '- [ ] Revisar transcripción completa'
                }
        else:
            logger.error(f"Error en análisis de IA: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error analizando contenido de reunión: {str(e)}")
        return None


def extract_audio_from_video(video_path):
    """
    Extraer audio de archivo de video para transcripción
    Nota: Requiere ffmpeg instalado en el sistema
    """
    try:
        import subprocess
        import tempfile
        
        # Crear archivo temporal para el audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            audio_path = temp_audio.name
        
        # Usar ffmpeg para extraer audio
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # Audio codec
            '-ar', '16000',  # Sample rate
            '-ac', '1',  # Mono
            audio_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return audio_path
        else:
            logger.error(f"Error extrayendo audio: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Error extrayendo audio de video: {str(e)}")
        return None