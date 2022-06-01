from django.contrib import admin


class NotifyAdmin(admin.ModelAdmin):
    readonly_fields = ("date_creation",)
    fields = ("title", "body", "date_creation", "to_users")
    list_display = ("title", "body", "date_creation")


class ScheduledNotifyAdmin(admin.ModelAdmin):
    pass
