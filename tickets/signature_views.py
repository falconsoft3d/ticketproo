"""
ERP3 - Firmas digitales.

Flujo:
1. El usuario sube un PDF y define los firmantes.
2. En el editor coloca recuadros de firma en cada página, asignados a un firmante.
3. Cada firmante recibe su propia URL pública (/firmar/<token>/), dibuja su
   firma (garabato) y con "Firmar todo" la aplica en todos sus recuadros.
4. El servidor estampa las firmas sobre el PDF original y añade una página
   de certificado con el registro de firmas.
"""
import base64
import hashlib
import json
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .models import SignatureDocument, SignatureField, SignatureSigner
from .submenu_utils import get_erp3_submenu
from .utils import get_client_ip

MAX_PDF_SIZE = 25 * 1024 * 1024  # 25 MB
MAX_SIGNATURE_SIZE = 2 * 1024 * 1024  # 2 MB


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #

def _base_context(request, active='signatures'):
    return {
        'app_name': 'ERP3',
        'submenu_items': get_erp3_submenu(request, active),
    }


def _get_document_for_user(request, pk):
    document = get_object_or_404(SignatureDocument, pk=pk)
    if not (request.user.is_staff or request.user.is_superuser) and document.created_by_id != request.user.id:
        raise PermissionDenied(_('No tienes permiso para ver este documento'))
    return document


def _read_pdf(file_obj):
    """Valida un PDF y devuelve el número de páginas. Lanza ValueError si no es válido."""
    from PyPDF2 import PdfReader

    try:
        file_obj.seek(0)
        reader = PdfReader(file_obj)
        if reader.is_encrypted:
            if not reader.decrypt(''):
                raise ValueError(_('El PDF está protegido con contraseña.'))
        count = len(reader.pages)
    except ValueError:
        raise
    except Exception:
        raise ValueError(_('El archivo no es un PDF válido.'))
    finally:
        file_obj.seek(0)
    if count == 0:
        raise ValueError(_('El PDF no tiene páginas.'))
    return count


def _page_rotation(page):
    """Rotación efectiva de la página (atributo heredable /Rotate)."""
    node = page
    while node is not None:
        if '/Rotate' in node:
            try:
                return int(node['/Rotate'].get_object() if hasattr(node['/Rotate'], 'get_object') else node['/Rotate']) % 360
            except (TypeError, ValueError):
                return 0
        parent = node.get('/Parent')
        node = parent.get_object() if parent is not None else None
    return 0


def _display_to_pdf(dx, dy, rotation, x0, y0, W, H):
    """
    Convierte un punto en fracciones de la página mostrada (origen arriba-izquierda,
    rotación aplicada, igual que pdf.js) a coordenadas PDF (origen abajo-izquierda).
    """
    if rotation == 90:
        return x0 + dy * W, y0 + dx * H
    if rotation == 180:
        return x0 + (1 - dx) * W, y0 + dy * H
    if rotation == 270:
        return x0 + (1 - dy) * W, y0 + (1 - dx) * H
    return x0 + dx * W, y0 + (1 - dy) * H


def _decode_signature(data_url):
    """Decodifica y sanea la imagen de firma (data URL PNG). Devuelve bytes PNG."""
    from PIL import Image

    prefix = 'data:image/png;base64,'
    if not data_url or not data_url.startswith(prefix):
        raise ValueError(_('Firma no válida.'))
    raw = data_url[len(prefix):]
    if len(raw) > MAX_SIGNATURE_SIZE * 4 / 3:
        raise ValueError(_('La imagen de la firma es demasiado grande.'))
    try:
        img = Image.open(BytesIO(base64.b64decode(raw, validate=True)))
        img.load()
    except Exception:
        raise ValueError(_('Firma no válida.'))
    img = img.convert('RGBA')
    if img.width > 3000 or img.height > 3000:
        raise ValueError(_('La imagen de la firma es demasiado grande.'))
    bbox = img.getchannel('A').getbbox()
    if not bbox:
        raise ValueError(_('La firma está vacía. Dibuja tu firma antes de enviar.'))
    img = img.crop(bbox)  # recorta los márgenes vacíos
    out = BytesIO()
    img.save(out, format='PNG')
    return out.getvalue()


def build_signed_pdf(document):
    """Genera el PDF con las firmas ya realizadas estampadas + página de certificado."""
    from PyPDF2 import PdfReader, PdfWriter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A4

    document.original_pdf.open('rb')
    try:
        original_bytes = document.original_pdf.read()
    finally:
        document.original_pdf.close()

    reader = PdfReader(BytesIO(original_bytes))
    if reader.is_encrypted:
        reader.decrypt('')
    writer = PdfWriter()

    signed_signers = {s.id: s for s in document.signers.filter(status='signed')}
    images = {}
    for signer in signed_signers.values():
        if signer.signature_image:
            signer.signature_image.open('rb')
            try:
                images[signer.id] = ImageReader(BytesIO(signer.signature_image.read()))
            finally:
                signer.signature_image.close()

    fields_by_page = {}
    for field in document.fields.filter(signer_id__in=images.keys()):
        fields_by_page.setdefault(field.page, []).append(field)

    for index, page in enumerate(reader.pages, start=1):
        page_fields = fields_by_page.get(index)
        if page_fields:
            box = page.cropbox
            x0, y0 = float(box.left), float(box.bottom)
            W, H = float(box.width), float(box.height)
            rotation = _page_rotation(page)

            buf = BytesIO()
            c = rl_canvas.Canvas(buf, pagesize=(x0 + W + 1, y0 + H + 1))
            for field in page_fields:
                signer = signed_signers[field.signer_id]
                ax, ay = _display_to_pdf(field.x, field.y + field.height, rotation, x0, y0, W, H)
                if rotation in (90, 270):
                    bw, bh = field.width * H, field.height * W
                else:
                    bw, bh = field.width * W, field.height * H

                caption_h = min(8.0, bh * 0.22)
                c.saveState()
                c.translate(ax, ay)
                c.rotate(rotation)
                c.drawImage(images[signer.id], 0, caption_h, width=bw, height=bh - caption_h,
                            mask='auto', preserveAspectRatio=True, anchor='c')
                font_size = max(4.0, caption_h * 0.75)
                c.setFont('Helvetica', font_size)
                c.setFillColorRGB(0.3, 0.3, 0.3)
                signed_at = timezone.localtime(signer.signed_at).strftime('%d/%m/%Y %H:%M') if signer.signed_at else ''
                caption = f'{signer.name} · {signed_at}'
                while c.stringWidth(caption, 'Helvetica', font_size) > bw and font_size > 3:
                    font_size -= 0.5
                    c.setFont('Helvetica', font_size)
                c.drawCentredString(bw / 2, caption_h * 0.2, caption)
                c.restoreState()
            c.save()
            buf.seek(0)
            page.merge_page(PdfReader(buf).pages[0])
        writer.add_page(page)

    # Página de certificado / registro de firmas
    if signed_signers:
        buf = BytesIO()
        c = rl_canvas.Canvas(buf, pagesize=A4)
        pw, ph = A4
        y = ph - 60
        c.setFont('Helvetica-Bold', 16)
        c.drawString(50, y, _('Certificado de firmas'))
        y -= 28
        c.setFont('Helvetica', 10)
        c.drawString(50, y, f"{_('Documento')}: {document.title}")
        y -= 15
        c.drawString(50, y, f"{_('Referencia')}: SIG-{document.pk:06d}")
        y -= 15
        c.drawString(50, y, f"SHA-256 {_('del PDF original')}:")
        y -= 13
        c.setFont('Courier', 8)
        c.drawString(50, y, hashlib.sha256(original_bytes).hexdigest())
        y -= 30
        for signer in document.signers.all():
            if y < 140:
                c.showPage()
                y = ph - 60
            c.setFont('Helvetica-Bold', 11)
            c.drawString(50, y, signer.name)
            c.setFont('Helvetica', 9)
            y -= 14
            if signer.email:
                c.drawString(60, y, f"Email: {signer.email}")
                y -= 12
            if signer.status == 'signed':
                c.drawString(60, y, f"{_('Firmado')}: {timezone.localtime(signer.signed_at).strftime('%d/%m/%Y %H:%M:%S %Z')}")
                y -= 12
                c.drawString(60, y, f"IP: {signer.signed_ip or '-'}")
                y -= 12
                ua = (signer.signed_user_agent or '-')[:110]
                c.drawString(60, y, f"{_('Navegador')}: {ua}")
                y -= 12
                if signer.id in images:
                    c.drawImage(images[signer.id], 60, y - 45, width=160, height=42,
                                mask='auto', preserveAspectRatio=True, anchor='sw')
                    y -= 50
            else:
                c.drawString(60, y, _('Pendiente de firma'))
                y -= 12
            y -= 16
        c.setFont('Helvetica', 7)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(50, 30, f"{_('Generado')}: {timezone.localtime().strftime('%d/%m/%Y %H:%M:%S %Z')}")
        c.save()
        buf.seek(0)
        for p in PdfReader(buf).pages:
            writer.add_page(p)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def _regenerate_signed_pdf(document):
    pdf_bytes = build_signed_pdf(document)
    old_name = document.signed_pdf.name if document.signed_pdf else None
    document.signed_pdf.save(f'firmado_{document.pk}.pdf', ContentFile(pdf_bytes), save=False)
    document.save(update_fields=['signed_pdf', 'updated_at'])
    if old_name and old_name != document.signed_pdf.name:
        document.signed_pdf.storage.delete(old_name)


def _valid_ip(value):
    import ipaddress
    try:
        return str(ipaddress.ip_address((value or '').strip()))
    except ValueError:
        return None


def _pdf_response(file_field, filename, as_attachment=False):
    if not file_field:
        raise Http404
    try:
        f = file_field.open('rb')
    except FileNotFoundError:
        raise Http404
    response = FileResponse(f, content_type='application/pdf', as_attachment=as_attachment, filename=filename)
    response['Cache-Control'] = 'private, no-store'
    return response


def _safe_filename(title, suffix=''):
    from django.utils.text import slugify
    return f"{slugify(title) or 'documento'}{suffix}.pdf"


# --------------------------------------------------------------------------- #
# Vistas internas (ERP3)
# --------------------------------------------------------------------------- #

@login_required
def signature_document_list(request):
    if request.user.is_staff or request.user.is_superuser:
        documents = SignatureDocument.objects.all()
    else:
        documents = SignatureDocument.objects.filter(created_by=request.user)

    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '')
    if search:
        documents = documents.filter(
            Q(title__icontains=search) | Q(signers__name__icontains=search) | Q(signers__email__icontains=search)
        ).distinct()
    if status:
        documents = documents.filter(status=status)

    documents = documents.select_related('created_by').annotate(
        total_signers=Count('signers', distinct=True),
        done_signers=Count('signers', filter=Q(signers__status='signed'), distinct=True),
    ).order_by('-created_at')
    page_obj = Paginator(documents, 25).get_page(request.GET.get('page'))

    context = _base_context(request)
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'status_choices': SignatureDocument.STATUS_CHOICES,
    })
    return render(request, 'tickets/signature_document_list.html', context)


@login_required
def signature_document_create(request):
    errors = {}
    data = {}
    if request.method == 'POST':
        data = request.POST
        title = data.get('title', '').strip()
        pdf = request.FILES.get('pdf')
        names = data.getlist('signer_name')
        emails = data.getlist('signer_email')

        if not title:
            errors['title'] = _('El título es obligatorio.')
        page_count = 0
        if not pdf:
            errors['pdf'] = _('Debes subir un PDF.')
        elif pdf.size > MAX_PDF_SIZE:
            errors['pdf'] = _('El PDF no puede superar los 25 MB.')
        elif not pdf.name.lower().endswith('.pdf'):
            errors['pdf'] = _('El archivo debe ser un PDF.')
        else:
            try:
                page_count = _read_pdf(pdf)
            except ValueError as e:
                errors['pdf'] = str(e)

        signers = [(n.strip(), (emails[i] if i < len(emails) else '').strip())
                   for i, n in enumerate(names) if n.strip()]
        if not signers:
            errors['signers'] = _('Añade al menos un firmante.')

        if not errors:
            with transaction.atomic():
                document = SignatureDocument.objects.create(
                    title=title,
                    description=data.get('description', '').strip(),
                    original_pdf=pdf,
                    page_count=page_count,
                    created_by=request.user,
                )
                for i, (name, email) in enumerate(signers):
                    SignatureSigner.objects.create(document=document, name=name[:150], email=email[:254], order=i)
            messages.success(request, _('Documento subido. Ahora coloca los recuadros de firma en el PDF.'))
            return redirect('signature_document_editor', pk=document.pk)

    context = _base_context(request, 'signatures_new')
    context.update({'errors': errors, 'data': data})
    return render(request, 'tickets/signature_document_form.html', context)


@login_required
def signature_document_detail(request, pk):
    document = _get_document_for_user(request, pk)
    signers = list(document.signers.annotate(field_count=Count('fields')))
    for s in signers:
        s.absolute_sign_url = request.build_absolute_uri(s.get_sign_url())
    context = _base_context(request)
    context.update({
        'document': document,
        'signers': signers,
        'fields_total': document.fields.count(),
    })
    return render(request, 'tickets/signature_document_detail.html', context)


@login_required
def signature_document_editor(request, pk):
    document = _get_document_for_user(request, pk)
    signers = list(document.signers.all())
    fields = [
        {'id': f.id, 'signer': f.signer_id, 'page': f.page, 'x': f.x, 'y': f.y, 'w': f.width, 'h': f.height}
        for f in document.fields.all()
    ]
    context = _base_context(request)
    context.update({
        'document': document,
        'signers': signers,
        'signers_json': [
            {'id': s.id, 'name': s.name, 'color': s.color, 'signed': s.status == 'signed'} for s in signers
        ],
        'fields_json': fields,
    })
    return render(request, 'tickets/signature_document_editor.html', context)


@login_required
@require_POST
def signature_document_fields_save(request, pk):
    document = _get_document_for_user(request, pk)
    try:
        payload = json.loads(request.body.decode('utf-8'))
        items = payload.get('fields', [])
        assert isinstance(items, list)
    except Exception:
        return JsonResponse({'ok': False, 'error': _('Datos no válidos.')}, status=400)

    signers = {s.id: s for s in document.signers.all()}
    editable_ids = {sid for sid, s in signers.items() if s.status != 'signed'}

    new_fields = []
    for item in items:
        try:
            signer_id = int(item['signer'])
            page = int(item['page'])
            x, y, w, h = (float(item[k]) for k in ('x', 'y', 'w', 'h'))
        except (KeyError, TypeError, ValueError):
            return JsonResponse({'ok': False, 'error': _('Datos no válidos.')}, status=400)
        if signer_id not in editable_ids:
            continue  # los campos de firmantes que ya firmaron no se modifican
        if not (1 <= page <= document.page_count):
            continue
        w = min(max(w, 0.01), 1.0)
        h = min(max(h, 0.01), 1.0)
        x = min(max(x, 0.0), 1.0 - w)
        y = min(max(y, 0.0), 1.0 - h)
        new_fields.append(SignatureField(document=document, signer_id=signer_id, page=page, x=x, y=y, width=w, height=h))

    with transaction.atomic():
        document.fields.filter(signer_id__in=editable_ids).delete()
        SignatureField.objects.bulk_create(new_fields)
    document.refresh_status()
    return JsonResponse({'ok': True, 'count': document.fields.count()})


@login_required
@require_POST
def signature_signer_add(request, pk):
    document = _get_document_for_user(request, pk)
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    if not name:
        messages.error(request, _('El nombre del firmante es obligatorio.'))
    else:
        last = document.signers.order_by('-order').first()
        SignatureSigner.objects.create(document=document, name=name[:150], email=email[:254],
                                       order=(last.order + 1) if last else 0)
        # Un nuevo firmante reabre un documento completado
        document.refresh_status()
        messages.success(request, _('Firmante añadido. Coloca sus recuadros de firma en el editor.'))
    if request.POST.get('from') == 'editor':
        return redirect('signature_document_editor', pk=document.pk)
    return redirect('signature_document_detail', pk=document.pk)


@login_required
@require_POST
def signature_signer_delete(request, pk, signer_id):
    document = _get_document_for_user(request, pk)
    signer = get_object_or_404(SignatureSigner, pk=signer_id, document=document)
    if signer.status == 'signed':
        messages.error(request, _('No se puede eliminar un firmante que ya firmó.'))
    else:
        signer.delete()
        document.refresh_status()
        messages.success(request, _('Firmante eliminado.'))
    return redirect('signature_document_detail', pk=document.pk)


@login_required
@require_POST
def signature_signer_reset_link(request, pk, signer_id):
    """Genera una nueva URL de firma (invalida la anterior)."""
    import uuid
    document = _get_document_for_user(request, pk)
    signer = get_object_or_404(SignatureSigner, pk=signer_id, document=document)
    if signer.status == 'signed':
        messages.error(request, _('Este firmante ya firmó.'))
    else:
        signer.token = uuid.uuid4()
        signer.save(update_fields=['token'])
        messages.success(request, _('Se generó un nuevo enlace de firma. El anterior ya no funciona.'))
    return redirect('signature_document_detail', pk=document.pk)


@login_required
@require_POST
def signature_document_delete(request, pk):
    document = _get_document_for_user(request, pk)
    for f in [document.original_pdf, document.signed_pdf] + [s.signature_image for s in document.signers.all()]:
        if f:
            try:
                f.storage.delete(f.name)
            except Exception:
                pass
    document.delete()
    messages.success(request, _('Documento eliminado.'))
    return redirect('signature_document_list')


@login_required
def signature_document_pdf(request, pk):
    """PDF original (para el editor) o firmado (?signed=1)."""
    document = _get_document_for_user(request, pk)
    if request.GET.get('signed'):
        return _pdf_response(document.signed_pdf, _safe_filename(document.title, '_firmado'),
                             as_attachment=bool(request.GET.get('download')))
    return _pdf_response(document.original_pdf, _safe_filename(document.title),
                         as_attachment=bool(request.GET.get('download')))


# --------------------------------------------------------------------------- #
# Vistas públicas (firmante, sin login)
# --------------------------------------------------------------------------- #

def signature_sign_public(request, token):
    signer = get_object_or_404(SignatureSigner.objects.select_related('document'), token=token)
    document = signer.document
    if signer.status == 'pending':
        signer.status = 'viewed'
        signer.viewed_at = timezone.now()
        signer.save(update_fields=['status', 'viewed_at'])

    fields = [
        {'id': f.id, 'page': f.page, 'x': f.x, 'y': f.y, 'w': f.width, 'h': f.height}
        for f in signer.fields.all()
    ]
    context = {
        'signer': signer,
        'document': document,
        'fields_json': fields,
        'already_signed': signer.status == 'signed',
    }
    return render(request, 'tickets/signature_sign_public.html', context)


def signature_sign_public_pdf(request, token):
    signer = get_object_or_404(SignatureSigner.objects.select_related('document'), token=token)
    document = signer.document
    if request.GET.get('signed'):
        if signer.status != 'signed':
            raise Http404
        return _pdf_response(document.signed_pdf, _safe_filename(document.title, '_firmado'), as_attachment=True)
    return _pdf_response(document.original_pdf, _safe_filename(document.title))


@require_POST
def signature_sign_public_submit(request, token):
    signer = get_object_or_404(SignatureSigner.objects.select_related('document'), token=token)
    document = signer.document

    if signer.status == 'signed':
        return JsonResponse({'ok': False, 'error': _('Este documento ya fue firmado por ti.')}, status=400)
    if not signer.fields.exists():
        return JsonResponse({'ok': False, 'error': _('Este documento aún no tiene recuadros de firma asignados.')}, status=400)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'ok': False, 'error': _('Datos no válidos.')}, status=400)
    if not payload.get('accept'):
        return JsonResponse({'ok': False, 'error': _('Debes aceptar firmar electrónicamente el documento.')}, status=400)
    try:
        png = _decode_signature(payload.get('signature', ''))
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    with transaction.atomic():
        signer = SignatureSigner.objects.select_for_update().get(pk=signer.pk)
        if signer.status == 'signed':
            return JsonResponse({'ok': False, 'error': _('Este documento ya fue firmado por ti.')}, status=400)
        signer.signature_image.save(f'firma_{signer.pk}.png', ContentFile(png), save=False)
        signer.status = 'signed'
        signer.signed_at = timezone.now()
        signer.signed_ip = _valid_ip(get_client_ip(request))
        signer.signed_user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        signer.save()

    try:
        _regenerate_signed_pdf(document)
    except Exception:
        import logging
        logging.getLogger(__name__).exception('Error generando PDF firmado %s', document.pk)
    document.refresh_status()

    return JsonResponse({'ok': True, 'download_url': f"{signer.get_sign_url()}pdf/?signed=1"})
