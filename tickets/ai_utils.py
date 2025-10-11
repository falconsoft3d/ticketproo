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