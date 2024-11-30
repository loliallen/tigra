import datetime

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import DateRangeFilter

from apps.mobile.logic.selectors.visits import visits_with_end_at
from apps.mobile.models import Visit
from apps.account.admin.tools import model_admin_url


class ActiveVisitFilter(admin.SimpleListFilter):
    title = 'Активный визит'
    parameter_name = 'is_active_visit'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Yes')),
            ('no', _('No')),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        if self.value() == 'yes':
            return queryset.filter(
                end_at__gte=localtime(),
            )
        else:
            return queryset.filter(
                end_at__lt=localtime(),
            )

class VisitAdmin(admin.ModelAdmin):
    readonly_fields = ("date", "duration", "is_free", "free_reason", "user_", "staff_")
    fields = ("date", "duration", "is_free", "free_reason", "user_", "staff_")
    list_display = ("date", "visit_end", "user_", "children_")


    list_filter = (ActiveVisitFilter, ("date", DateRangeFilter), "is_free", "free_reason")

    def get_queryset(self, request):
        return visits_with_end_at().prefetch_related("children")

    def visit_end(self, obj: Visit):
        return (obj.date + datetime.timedelta(seconds=obj.duration)).time()
    visit_end.admin_order_field = 'visit_end'
    visit_end.short_description = 'Конец визита'

    def children_(self, obj: Visit):
        children = obj.children.all()

        if len(children):
            return mark_safe("<br/>".join([
                f"{child.name} {child.birth_date} "
                f"({child.age_str()})"
                f"{' Cегодня день рождение 🎉' if child.birth_date == localtime().date() else ''}"
                for child in children
            ]))
        else:
            return "-"
    children_.admin_order_field = 'children'
    children_.short_description = 'Дети'
    children_.allow_tags = True

    def user_(self, obj):
        return model_admin_url(obj.user)

    def staff_(self, obj):
        return model_admin_url(obj.staff)


admin.site.register(Visit, VisitAdmin)
