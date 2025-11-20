import json
import requests
import re
from urllib.parse import urlparse, parse_qs
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.contrib.sessions.models import Session
from user_agents import parse as parse_user_agent
from .models import PageVisit
import logging

logger = logging.getLogger(__name__)


class PageVisitTrackingMiddleware(MiddlewareMixin):
    """
    Middleware para rastrear visitas a páginas públicas
    """
    
    # Páginas públicas que queremos rastrear
    PUBLIC_PAGES = {
        '/': 'home',
        '/home/': 'home',
    }
    
    # Patrones de URLs para detectar páginas públicas específicas
    PUBLIC_PATTERNS = [
        (r'^/public/concepts/$', 'conceptos'),
        (r'^/public/courses/[^/]+/$', 'course_public'),
        (r'^/public/courses/[^/]+/classes/\d+/$', 'course_public'),
        (r'^/public/[^/]+/$', 'ticket_public'),
        (r'^/contact/[^/]+/$', 'contact'),
        (r'^/contact/success/$', 'contact'),
        (r'^/lp/[^/]+/$', 'landing'),
        (r'^/document/public/[^/]+/$', 'other'),
        (r'^/work-order/public/[^/]+/$', 'other'),
        (r'^/job-apply/[^/]+/$', 'other'),
        (r'^/company/stats/[^/]+/$', 'other'),
        (r'^/public/company/[^/]+/create-ticket/$', 'other'),
        (r'^/public/upload-file/$', 'other'),
        (r'^/public/upload-recording/$', 'other'),
    ]
    
    # Patrones de URLs a excluir del tracking
    EXCLUDE_PATTERNS = [
        r'^/admin/',
        r'^/dashboard/',
        r'^/api/',
        r'^/media/',
        r'^/static/',
        r'^/favicon',
        r'\.css$',
        r'\.js$',
        r'\.png$',
        r'\.jpg$',
        r'\.jpeg$',
        r'\.gif$',
        r'\.svg$',
        r'\.ico$',
        r'\.woff',
        r'\.ttf$',
    ]
    
    # User agents de bots conocidos
    BOT_PATTERNS = [
        r'bot', r'crawler', r'spider', r'scraper',
        r'google', r'bing', r'yahoo', r'facebook',
        r'twitter', r'linkedin', r'whatsapp',
        r'telegram', r'slack', r'discord'
    ]
    
    def process_request(self, request):
        """
        Procesa cada request para determinar si debe ser rastreado
        """
        try:
            # Solo rastrear métodos GET
            if request.method != 'GET':
                return None
            
            path = request.path
            
            # Verificar si la URL debe ser excluida
            if self._should_exclude_url(path):
                return None
            
            # Verificar si es una página pública que queremos rastrear
            page_type = self._get_page_type(path)
            if not page_type:
                return None
            
            # Obtener información del request
            ip_address = self._get_client_ip(request)
            user_agent_string = request.META.get('HTTP_USER_AGENT', '')
            
            # Verificar si es un bot
            if self._is_bot(user_agent_string):
                # Aún registramos bots pero los marcamos como tal
                pass
            
            # Programar el registro de la visita para después del response
            request._track_visit_data = {
                'page_type': page_type,
                'page_url': request.build_absolute_uri(),
                'ip_address': ip_address,
                'user_agent': user_agent_string,
                'referrer': request.META.get('HTTP_REFERER', ''),
                'session_id': request.session.session_key or '',
            }
            
        except Exception as e:
            logger.error(f"Error en PageVisitTrackingMiddleware.process_request: {e}")
        
        return None
    
    def process_response(self, request, response):
        """
        Procesa la respuesta para registrar la visita si es necesario
        """
        try:
            # Solo registrar si el response es exitoso (200-299)
            if not (200 <= response.status_code < 300):
                return response
            
            # Verificar si tenemos datos de tracking
            track_data = getattr(request, '_track_visit_data', None)
            if not track_data:
                return response
            
            # Registrar la visita de forma asíncrona
            self._record_visit(track_data, request, response)
            
        except Exception as e:
            logger.error(f"Error en PageVisitTrackingMiddleware.process_response: {e}")
        
        return response
    
    def _should_exclude_url(self, path):
        """
        Determina si una URL debe ser excluida del tracking
        """
        for pattern in self.EXCLUDE_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                return True
        return False
    
    def _get_page_type(self, path):
        """
        Determina el tipo de página basado en la URL
        """
        # Verificar páginas exactas
        if path in self.PUBLIC_PAGES:
            return self.PUBLIC_PAGES[path]
        
        # Verificar patrones de páginas públicas
        for pattern, page_type in self.PUBLIC_PATTERNS:
            if re.match(pattern, path):
                return page_type
        
        return None
    
    def _get_client_ip(self, request):
        """
        Obtiene la IP real del cliente considerando proxies
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_bot(self, user_agent):
        """
        Determina si el user agent corresponde a un bot
        """
        if not user_agent:
            return True
        
        user_agent_lower = user_agent.lower()
        for pattern in self.BOT_PATTERNS:
            if re.search(pattern, user_agent_lower):
                return True
        return False
    
    def _parse_user_agent(self, user_agent_string):
        """
        Parsea el user agent para obtener información del navegador y dispositivo
        """
        try:
            ua = parse_user_agent(user_agent_string)
            return {
                'browser': ua.browser.family,
                'browser_version': ua.browser.version_string,
                'operating_system': f"{ua.os.family} {ua.os.version_string}".strip(),
                'device_type': ua.device.family,
                'is_mobile': ua.is_mobile,
                'is_bot': ua.is_bot,
            }
        except Exception as e:
            logger.error(f"Error parseando user agent: {e}")
            return {
                'browser': 'Desconocido',
                'browser_version': '',
                'operating_system': 'Desconocido',
                'device_type': 'Desconocido',
                'is_mobile': False,
                'is_bot': False,
            }
    
    def _get_location_from_ip(self, ip_address):
        """
        Obtiene información de geolocalización desde la IP
        """
        # Verificar que la IP sea pública
        if not ip_address or ip_address.startswith(('127.', '192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.', 'localhost', '::1')):
            return {
                'country': '',
                'country_code': '',
                'region': '',
                'city': '',
            }
        
        try:
            # Usar un servicio gratuito de geolocalización
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}",
                timeout=5,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'country': data.get('country', ''),
                        'country_code': data.get('countryCode', ''),
                        'region': data.get('regionName', ''),
                        'city': data.get('city', ''),
                    }
                else:
                    logger.warning(f"IP-API returned error for {ip_address}: {data.get('message', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error obteniendo geolocalización para IP {ip_address}: {e}")
        
        return {
            'country': '',
            'country_code': '',
            'region': '',
            'city': '',
        }
    
    def _parse_utm_parameters(self, url):
        """
        Extrae parámetros UTM de la URL
        """
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            return {
                'utm_source': query_params.get('utm_source', [''])[0],
                'utm_medium': query_params.get('utm_medium', [''])[0],
                'utm_campaign': query_params.get('utm_campaign', [''])[0],
            }
        except Exception as e:
            logger.error(f"Error parseando parámetros UTM: {e}")
            return {
                'utm_source': '',
                'utm_medium': '',
                'utm_campaign': '',
            }
    
    def _get_page_title(self, response):
        """
        Intenta extraer el título de la página del HTML
        """
        try:
            if response.get('Content-Type', '').startswith('text/html'):
                content = response.content.decode('utf-8')
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
                if title_match:
                    return title_match.group(1).strip()
        except Exception as e:
            logger.error(f"Error extrayendo título de página: {e}")
        return ''
    
    def _record_visit(self, track_data, request, response):
        """
        Registra la visita en la base de datos
        """
        try:
            # Parsear user agent
            ua_info = self._parse_user_agent(track_data['user_agent'])
            
            # Obtener geolocalización
            location_info = self._get_location_from_ip(track_data['ip_address'])
            
            # Parsear parámetros UTM
            utm_info = self._parse_utm_parameters(track_data['page_url'])
            
            # Obtener título de la página
            page_title = self._get_page_title(response)
            
            # Si es una landing page, obtener información adicional
            if track_data['page_type'] == 'landing':
                page_title = self._get_landing_page_title(track_data['page_url'])
            
            # Crear el registro de visita
            visit = PageVisit.objects.create(
                page_type=track_data['page_type'],
                page_url=track_data['page_url'],
                page_title=page_title,
                ip_address=track_data['ip_address'],
                country=location_info['country'],
                country_code=location_info['country_code'],
                city=location_info['city'],
                region=location_info['region'],
                user_agent=track_data['user_agent'],
                browser=ua_info['browser'],
                browser_version=ua_info['browser_version'],
                operating_system=ua_info['operating_system'],
                device_type=ua_info['device_type'],
                is_mobile=ua_info['is_mobile'],
                is_bot=ua_info['is_bot'] or self._is_bot(track_data['user_agent']),
                referrer=track_data['referrer'],
                utm_source=utm_info['utm_source'],
                utm_medium=utm_info['utm_medium'],
                utm_campaign=utm_info['utm_campaign'],
                session_id=track_data['session_id'],
                visited_at=timezone.now(),
            )
            
            logger.info(f"Visita registrada: {visit}")
            
        except Exception as e:
            logger.error(f"Error registrando visita: {e}")
    
    def _get_landing_page_title(self, page_url):
        """
        Obtiene el título de una landing page desde la base de datos
        """
        try:
            from urllib.parse import urlparse
            from .models import LandingPage
            
            # Extraer el slug de la URL
            path = urlparse(page_url).path
            if path.startswith('/lp/') and path.endswith('/'):
                slug = path[4:-1]  # Remover /lp/ y /
                try:
                    landing_page = LandingPage.objects.get(slug=slug, is_active=True)
                    return f"Landing: {landing_page.nombre_producto}"
                except LandingPage.DoesNotExist:
                    return f"Landing: {slug}"
            
        except Exception as e:
            logger.error(f"Error obteniendo título de landing page: {e}")
        
        return "Landing Page"