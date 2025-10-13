from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from .models import BlogPost, LandingPage


class StaticViewSitemap(Sitemap):
    """Sitemap para páginas estáticas públicas"""
    priority = 0.8
    changefreq = 'weekly'
    
    def items(self):
        # Solo URLs públicas que no requieren autenticación
        return [
            'home',                    # Página principal
            'blog_list',              # Lista del blog
            'contacto_web',           # Formulario de contacto
            'public_concepts',        # Conceptos públicos
        ]
    
    def location(self, item):
        return reverse(item)
    
    def lastmod(self, item):
        # Fecha de última modificación (puedes personalizar por página)
        return timezone.now()


class BlogPostSitemap(Sitemap):
    """Sitemap para posts del blog"""
    changefreq = 'weekly'
    priority = 0.9
    
    def items(self):
        # Solo posts publicados
        return BlogPost.objects.filter(status='published').order_by('-created_at')
    
    def lastmod(self, obj):
        return obj.updated_at if obj.updated_at else obj.created_at
    
    def location(self, obj):
        return reverse('blog_post_detail', kwargs={'slug': obj.slug})


class LandingPageSitemap(Sitemap):
    """Sitemap para landing pages públicas"""
    changefreq = 'monthly'
    priority = 0.7
    
    def items(self):
        # Solo landing pages activas
        return LandingPage.objects.filter(is_active=True).order_by('-created_at')
    
    def lastmod(self, obj):
        return obj.updated_at if obj.updated_at else obj.created_at
    
    def location(self, obj):
        return reverse('landing_page_public', kwargs={'slug': obj.slug})


class ExamSitemap(Sitemap):
    """Sitemap para exámenes públicos"""
    changefreq = 'monthly'
    priority = 0.6
    
    def items(self):
        # Solo exámenes que tienen token público
        from .models import Exam
        return Exam.objects.exclude(public_token__isnull=True).exclude(public_token='').order_by('-created_at')
    
    def lastmod(self, obj):
        return obj.updated_at if obj.updated_at else obj.created_at
    
    def location(self, obj):
        return reverse('exam_take_public', kwargs={'token': obj.public_token})


class CourseSitemap(Sitemap):
    """Sitemap para cursos públicos"""
    changefreq = 'monthly'
    priority = 0.6
    
    def items(self):
        # Solo cursos que tienen token público
        from .models import Course
        return Course.objects.exclude(public_token__isnull=True).exclude(public_token='').order_by('-created_at')
    
    def lastmod(self, obj):
        return obj.updated_at if obj.updated_at else obj.created_at
    
    def location(self, obj):
        return reverse('course_public', kwargs={'token': obj.public_token})


class DocumentSitemap(Sitemap):
    """Sitemap para documentos públicos"""
    changefreq = 'monthly'
    priority = 0.5
    
    def items(self):
        # Solo documentos que tienen token público
        from .models import Document
        return Document.objects.exclude(public_token__isnull=True).exclude(public_token='').order_by('-created_at')
    
    def lastmod(self, obj):
        return obj.updated_at if obj.updated_at else obj.created_at
    
    def location(self, obj):
        return reverse('document_public', kwargs={'token': obj.public_token})


# Diccionario de todos los sitemaps
sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogPostSitemap,
    'landing_pages': LandingPageSitemap,
    'exams': ExamSitemap,
    'courses': CourseSitemap,
    'documents': DocumentSitemap,
}