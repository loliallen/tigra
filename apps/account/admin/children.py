from django.contrib import admin

from apps.account.models import User, Child


class ChildrenAdmin(admin.ModelAdmin):
    model = Child
    list_display = ("name", "sex", "birth_date")
    list_filter = ("sex",)
    search_fields = ("name",)
    raw_id_fields = ("my_parent",)