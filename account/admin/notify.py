from django.contrib import admin

from account.models import Condition


class NotifyAdmin(admin.ModelAdmin):
    readonly_fields = ("date_creation",)
    fields = ("title", "body", "date_creation", "to_users")
    list_display = ("title", "body", "date_creation")
    filter_horizontal = ("to_users",)


class ConditionInline(admin.TabularInline):
    model = Condition
    extra = 0


class ScheduledNotifyAdmin(admin.ModelAdmin):
    inlines = (ConditionInline,)
