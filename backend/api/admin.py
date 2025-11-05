from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import ProductoFinanciero, DocumentoTipo, RequisitoProductoDocumento, DocumentoAdjunto

class EmpresaModelAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Verificar que el usuario tenga perfil y empresa
            if not hasattr(request.user, 'userprofile') or not hasattr(request.user.userprofile, 'empresa'):
                return qs.none()  # No mostrar nada si no hay perfil/empresa
            qs = qs.filter(empresa=request.user.userprofile.empresa)
        return qs

    def save_model(self, request, obj, form, change):
        if not change:  # Solo en creación
            if not request.user.is_superuser:
                if not hasattr(request.user, 'userprofile') or not hasattr(request.user.userprofile, 'empresa'):
                    raise ValidationError(_('Usuario no tiene perfil o empresa asignada'))
                obj.empresa = request.user.userprofile.empresa
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if not super().has_change_permission(request, obj):
            return False
        if obj and not request.user.is_superuser:
            return obj.empresa == request.user.userprofile.empresa
        return True

    def has_delete_permission(self, request, obj=None):
        if not super().has_delete_permission(request, obj):
            return False
        if obj and not request.user.is_superuser:
            return obj.empresa == request.user.userprofile.empresa
        return True

class ProductoFinancieroAdmin(EmpresaModelAdmin):
    list_display = ['codigo', 'nombre', 'tipo', 'tasa_nominal_anual_min', 'monto_min', 'monto_max', 'activo']
    list_filter = ['tipo', 'activo']
    search_fields = ['codigo', 'nombre']
    ordering = ['codigo']
    readonly_fields = ['created_at', 'updated_at'] if hasattr(ProductoFinanciero, 'created_at') else []

class DocumentoTipoAdmin(EmpresaModelAdmin):
    list_display = ['codigo', 'nombre', 'vigencia_dias']
    search_fields = ['codigo', 'nombre']
    ordering = ['codigo']
    readonly_fields = ['created_at', 'updated_at'] if hasattr(DocumentoTipo, 'created_at') else []

class RequisitoProductoDocumentoAdmin(EmpresaModelAdmin):
    list_display = ['producto', 'tipo_trabajador', 'documento', 'obligatorio']
    list_filter = ['tipo_trabajador', 'obligatorio', 'producto']
    search_fields = ['producto__nombre', 'documento__nombre']
    autocomplete_fields = ['producto', 'documento']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            # Filtrar productos y documentos por empresa
            form.base_fields['producto'].queryset = ProductoFinanciero.objects.filter(
                empresa=request.user.userprofile.empresa
            )
            form.base_fields['documento'].queryset = DocumentoTipo.objects.filter(
                empresa=request.user.userprofile.empresa
            )
        return form

class DocumentoAdjuntoAdmin(EmpresaModelAdmin):
    list_display = ['solicitud', 'documento_tipo', 'fecha_emision', 'fecha_vencimiento', 'valido']
    list_filter = ['valido', 'documento_tipo', 'fecha_emision']
    search_fields = ['solicitud__id', 'documento_tipo__nombre']
    autocomplete_fields = ['solicitud', 'documento_tipo']
    readonly_fields = ['uploaded_at']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            # Filtrar solicitudes y tipos de documento por empresa
            form.base_fields['solicitud'].queryset = form.base_fields['solicitud'].queryset.filter(
                empresa=request.user.userprofile.empresa
            )
            form.base_fields['documento_tipo'].queryset = DocumentoTipo.objects.filter(
                empresa=request.user.userprofile.empresa
            )
        return form

# Registrar los modelos con sus respectivos admins
admin.site.register(ProductoFinanciero, ProductoFinancieroAdmin)
admin.site.register(DocumentoTipo, DocumentoTipoAdmin)
admin.site.register(RequisitoProductoDocumento, RequisitoProductoDocumentoAdmin)
admin.site.register(DocumentoAdjunto, DocumentoAdjuntoAdmin)
