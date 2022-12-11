from django.contrib import admin

from apps.mobile.models import Visit
from apps.account.admin.tools import model_admin_url


class VisitAdmin(admin.ModelAdmin):
    readonly_fields = ("date", "duration", "is_free", "free_reason", "user_", "staff_")
    fields = ("date", "duration", "is_free", "free_reason", "user_", "staff_")
    list_display = ("date", "duration", "is_free", "free_reason", "user_", "staff_")

    list_filter = ("date", "is_free", "free_reason")

    def user_(self, obj):
        return model_admin_url(obj.user)

    def staff_(self, obj):
        return model_admin_url(obj.staff)


admin.site.register(Visit, VisitAdmin)
