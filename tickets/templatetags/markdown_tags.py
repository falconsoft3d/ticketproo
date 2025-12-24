from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter(name='markdown_to_html')
def markdown_to_html(value):
    """
    Convierte texto Markdown a HTML simple
    """
    if not value:
        return ''
    
    # Escapar HTML existente para seguridad
    import html
    text = html.escape(value)
    
    # Convertir bloques de código (triple backticks)
    def replace_code_block(match):
        lang = match.group(1) or ''
        code = match.group(2)
        return f'<pre><code class="language-{lang}">{code}</code></pre>'
    
    text = re.sub(r'```(\w*)\n(.*?)```', replace_code_block, text, flags=re.DOTALL)
    
    # Convertir código inline
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Convertir títulos
    text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Convertir negritas
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convertir cursivas
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Convertir enlaces
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', text)
    
    # Convertir listas no ordenadas
    text = re.sub(r'^\- (.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', text, flags=re.DOTALL)
    text = re.sub(r'</ul>\s*<ul>', '', text)  # Unir listas consecutivas
    
    # Convertir saltos de línea dobles en párrafos
    paragraphs = text.split('\n\n')
    html_parts = []
    
    for para in paragraphs:
        para = para.strip()
        if para:
            # No envolver en <p> si ya es un elemento de bloque
            if not any(para.startswith(f'<{tag}') for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'ul', 'ol', 'blockquote', 'div']):
                para = f'<p>{para}</p>'
            html_parts.append(para)
    
    text = '\n'.join(html_parts)
    
    # Convertir separadores horizontales
    text = re.sub(r'^---$', r'<hr>', text, flags=re.MULTILINE)
    
    # Reemplazar saltos de línea simples con <br>
    text = text.replace('\n', '<br>\n')
    
    return mark_safe(text)
