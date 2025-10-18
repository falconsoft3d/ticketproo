"""
Utilidades para el rastreador web
"""
import requests
import socket
import dns.resolver
import ssl
import subprocess
import platform
import time
from urllib.parse import urlparse
from datetime import datetime
from bs4 import BeautifulSoup


def extract_domain(target):
    """Extrae el dominio de una URL o valida una IP"""
    # Si es una URL completa
    if target.startswith('http://') or target.startswith('https://'):
        parsed = urlparse(target)
        return parsed.netloc
    # Si es solo dominio o IP
    return target


def ping_host(host):
    """Hace ping a un host y retorna si está activo y el tiempo de respuesta"""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', host]
    
    try:
        start_time = time.time()
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        end_time = time.time()
        
        is_active = result.returncode == 0
        response_time = (end_time - start_time) * 1000 if is_active else None
        
        return is_active, response_time
    except Exception as e:
        print(f"Error en ping: {e}")
        return False, None


def get_dns_records(domain):
    """Obtiene registros DNS del dominio"""
    records = {
        'ip': None,
        'cname': [],
        'txt': [],
        'mx': [],
        'ns': []
    }
    
    try:
        # IP Address (A record)
        try:
            answers = dns.resolver.resolve(domain, 'A')
            records['ip'] = str(answers[0])
        except:
            pass
        
        # CNAME records
        try:
            answers = dns.resolver.resolve(domain, 'CNAME')
            records['cname'] = [str(rdata.target) for rdata in answers]
        except:
            pass
        
        # TXT records
        try:
            answers = dns.resolver.resolve(domain, 'TXT')
            records['txt'] = [str(rdata) for rdata in answers]
        except:
            pass
        
        # MX records
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            records['mx'] = [f"{rdata.preference} {rdata.exchange}" for rdata in answers]
        except:
            pass
        
        # NS records
        try:
            answers = dns.resolver.resolve(domain, 'NS')
            records['ns'] = [str(rdata) for rdata in answers]
        except:
            pass
        
    except Exception as e:
        print(f"Error obteniendo DNS: {e}")
    
    return records


def get_http_info(url):
    """Obtiene información HTTP del sitio"""
    info = {
        'status_code': None,
        'headers': {},
        'redirect_url': None,
        'server': None,
        'page_title': None,
        'meta_description': None,
        'page_size': None,
        'load_time': None,
        'ssl_valid': None,
        'technologies': []
    }
    
    # Asegurar que la URL tenga protocolo
    if not url.startswith('http://') and not url.startswith('https://'):
        url = f'https://{url}'
    
    try:
        start_time = time.time()
        response = requests.get(
            url,
            timeout=10,
            allow_redirects=True,
            verify=True
        )
        end_time = time.time()
        
        info['status_code'] = response.status_code
        info['headers'] = dict(response.headers)
        info['server'] = response.headers.get('Server', '')
        info['page_size'] = len(response.content)
        info['load_time'] = round(end_time - start_time, 2)
        info['ssl_valid'] = url.startswith('https://')
        
        # Si hubo redirección
        if response.history:
            info['redirect_url'] = response.url
        
        # Parsear HTML para obtener título y meta
        if 'text/html' in response.headers.get('Content-Type', ''):
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Título
            if soup.title:
                info['page_title'] = soup.title.string
            
            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                info['meta_description'] = meta_desc.get('content')
            
            # Detectar tecnologías básicas
            technologies = []
            
            # Framework JS
            if soup.find('script', src=lambda x: x and 'react' in x.lower()):
                technologies.append('React')
            if soup.find('script', src=lambda x: x and 'vue' in x.lower()):
                technologies.append('Vue.js')
            if soup.find('script', src=lambda x: x and 'angular' in x.lower()):
                technologies.append('Angular')
            if soup.find('script', src=lambda x: x and 'jquery' in x.lower()):
                technologies.append('jQuery')
            
            # CMS
            if soup.find('meta', attrs={'name': 'generator', 'content': lambda x: x and 'wordpress' in x.lower()}):
                technologies.append('WordPress')
            if soup.find('meta', attrs={'name': 'generator', 'content': lambda x: x and 'drupal' in x.lower()}):
                technologies.append('Drupal')
            if soup.find('meta', attrs={'name': 'generator', 'content': lambda x: x and 'joomla' in x.lower()}):
                technologies.append('Joomla')
            
            # CSS Frameworks
            if soup.find('link', href=lambda x: x and 'bootstrap' in x.lower()):
                technologies.append('Bootstrap')
            if soup.find('link', href=lambda x: x and 'tailwind' in x.lower()):
                technologies.append('Tailwind CSS')
            
            info['technologies'] = list(set(technologies))
        
    except requests.exceptions.SSLError:
        info['ssl_valid'] = False
        # Intentar con HTTP
        try:
            url_http = url.replace('https://', 'http://')
            response = requests.get(url_http, timeout=10, allow_redirects=True)
            info['status_code'] = response.status_code
            info['headers'] = dict(response.headers)
            info['server'] = response.headers.get('Server', '')
        except:
            pass
    except Exception as e:
        print(f"Error obteniendo HTTP: {e}")
    
    return info


def get_ssl_info(domain):
    """Obtiene información del certificado SSL"""
    info = {
        'valid': False,
        'issuer': None,
        'expiry_date': None
    }
    
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                
                info['valid'] = True
                info['issuer'] = dict(x[0] for x in cert['issuer'])
                
                # Fecha de expiración
                expiry_str = cert['notAfter']
                info['expiry_date'] = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
                
    except Exception as e:
        print(f"Error obteniendo SSL: {e}")
    
    return info


def track_website(target):
    """
    Función principal que rastrea un sitio web/IP
    Retorna un diccionario con toda la información recopilada
    """
    result = {
        'target': target,
        'is_active': False,
        'ping_response_time': None,
        'ip_address': None,
        'cname_records': [],
        'txt_records': [],
        'mx_records': [],
        'ns_records': [],
        'http_status_code': None,
        'http_headers': {},
        'redirect_url': None,
        'server_software': None,
        'technologies': [],
        'ssl_valid': None,
        'ssl_issuer': None,
        'ssl_expiry_date': None,
        'page_title': None,
        'meta_description': None,
        'page_size': None,
        'load_time': None,
        'error_message': None
    }
    
    try:
        # Extraer dominio/IP
        domain = extract_domain(target)
        
        # 1. Ping
        is_active, ping_time = ping_host(domain)
        result['is_active'] = is_active
        result['ping_response_time'] = ping_time
        
        # 2. DNS Records
        dns_records = get_dns_records(domain)
        result['ip_address'] = dns_records['ip']
        result['cname_records'] = dns_records['cname']
        result['txt_records'] = dns_records['txt']
        result['mx_records'] = dns_records['mx']
        result['ns_records'] = dns_records['ns']
        
        # 3. HTTP Info
        http_info = get_http_info(target)
        result['http_status_code'] = http_info['status_code']
        result['http_headers'] = http_info['headers']
        result['redirect_url'] = http_info['redirect_url']
        result['server_software'] = http_info['server']
        result['technologies'] = http_info['technologies']
        result['page_title'] = http_info['page_title']
        result['meta_description'] = http_info['meta_description']
        result['page_size'] = http_info['page_size']
        result['load_time'] = http_info['load_time']
        
        # 4. SSL Info
        ssl_info = get_ssl_info(domain)
        result['ssl_valid'] = ssl_info['valid']
        if ssl_info['issuer']:
            result['ssl_issuer'] = str(ssl_info['issuer'])
        result['ssl_expiry_date'] = ssl_info['expiry_date']
        
    except Exception as e:
        result['error_message'] = str(e)
    
    return result
