from django.contrib import admin

from apps.account.admin.tools import model_admin_url



class InvintationsAdmin(admin.ModelAdmin):
    readonly_fields = ("value", "creator_", "used_by_", "used_", "visited_", "is_used_by_creator")
    fields = ("value", "creator_", "used_by_", "used_", "visited_", "is_used_by_creator")

    list_display = ("value", "creator_", "used_by_", "used_", "visited_", "is_used_by_creator")
    list_filter = ("is_used_by_creator",)

    def creator_(self, obj):
        return model_admin_url(obj.creator)

    def used_by_(self, obj):
        return model_admin_url(obj.used_by)

    def used_(self, obj):
        return obj.used
    used_.boolean = True

    def visited_(self, obj):
        return obj.visited
    visited_.boolean = True
