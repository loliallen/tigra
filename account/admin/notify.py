from django.contrib import admin

from account.admin.tools import model_admin_url


class NotifyAdmin(admin.ModelAdmin):
    readonly_fields = ("date_creation",)
    fields = ("title", "body", "date_creation", "to_users_")
    list_display = ("title", "body", "date_creation")

    def to_users_(self, obj):
        return model_admin_url(obj.to_users.all(), is_list=True)
