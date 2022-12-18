from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.db import models
from django.db.models import (
    Count, Max, F, ExpressionWrapper, DurationField, DateTimeField, Value,
    CharField, Case, When
)
from django.db.models.functions import Cast, Concat
from django.http import HttpResponseRedirect
from django.utils import timezone

from apps.mobile.models import Visit
from apps.mobile.visits_logic import set_visit_if_free
from apps.account.admin.tools import model_admin_url, InlineChangeList
from apps.account.models import User, Child, Invintation


class VisitAdminInline(admin.TabularInline):
    model = Visit
    fk_name = 'user'
    extra = 0
    can_delete = False
    ordering = ('date',)
    template = 'admin/edit_inline/tabular_paginated.html'
    per_page = 5

    readonly_fields = ("is_free", "is_active", "free_reason", "staff_")
    fields = ("date", "duration", "is_free", "free_reason", "staff_")

    def staff_(self, obj):
        return model_admin_url(obj.staff)

    def get_formset(self, request, obj=None, **kwargs):
        formset_class = super().get_formset(
            request, obj, **kwargs)

        class PaginationFormSet(formset_class):
            def __init__(self, *args, **kwargs):
                super(PaginationFormSet, self).__init__(*args, **kwargs)

                qs = self.queryset
                paginator = Paginator(qs, self.per_page)
                try:
                    page_num = int(request.GET.get('p', '0'))
                except ValueError:
                    page_num = 0

                try:
                    page = paginator.page(page_num + 1)
                except (EmptyPage, InvalidPage):
                    page = paginator.page(paginator.num_pages)

                self.cl = InlineChangeList(request, page_num, paginator)
                self.paginator = paginator

                if self.cl.show_all:
                    self._queryset = qs
                else:
                    self._queryset = page.object_list

            def clean(self):
                new_instance = False
                for form in self.forms:
                    current_is_new = form.instance.id is None
                    if current_is_new:
                        if not new_instance:
                            new_instance = True
                        else:
                            raise forms.ValidationError('Не более одного нового визита')
                super(PaginationFormSet, self).clean()

            def save_before(self, request, form, formset, change):
                for form in formset:
                    if form.instance.staff is None:
                        form.instance.staff = request.user
                        set_visit_if_free(form.instance)
                        form.instance.save()


        PaginationFormSet.per_page = self.per_page
        return PaginationFormSet


class ChildrenAdminInline(admin.TabularInline):
    model = Child
    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput},
    }
    extra = 0


class InvintationAdminInline(admin.TabularInline):
    model = Invintation
    extra = 0
    can_delete = False
    fk_name = "creator"

    readonly_fields = ("value", "used_", "visited_", "used_by_", "is_used_by_creator")
    fields = ("value", "used_", "visited_", "used_by_", "is_used_by_creator")

    def used_by_(self, obj):
        return model_admin_url(obj.used_by)

    def used_(self, obj):
        return obj.used
    used_.boolean = True

    def visited_(self, obj):
        return obj.visited
    visited_.boolean = True


class VisitsCountGreaterFilter(admin.SimpleListFilter):
    title = 'Кол-во посещений больше'
    parameter_name = 'visit_count'

    def lookups(self, request, model_admin):
        return tuple(
            (f'>={i}', f'>={i}') for i in [1, 2, 3, 5, 10, 15, 20, 30, 50]
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(
            visits_count__gte=int(self.value()[2:]),
        )


class VisitsCountLowerFilter(admin.SimpleListFilter):
    title = 'Кол-во посещений меньше'
    parameter_name = 'visit_count_lower'

    def lookups(self, request, model_admin):
        return tuple(
            (f'<={i}', f'<={i}') for i in [0, 1, 2, 3, 5, 10, 15, 20, 30, 50]
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(
            visits_count__lte=int(self.value()[2:]),
        )


class ActiveVisitFilter(admin.SimpleListFilter):
    title = 'Активный визит'
    parameter_name = 'last_end'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        if self.value() == 'yes':
            return queryset.filter(
                last_end__gte=timezone.now(),
            )
        else:
            return queryset.filter(
                last_end__lt=timezone.now(),
            )


def export_selected_objects(modeladmin, request, queryset):
    selected = queryset.values_list('pk', flat=True)
    return HttpResponseRedirect(f'/admin/account/notification/add/?to_users={",".join(str(i) for i in selected)}')
export_selected_objects.short_description = "Отправить пуш уведомления"


class CustomUserAdmin(UserAdmin):
    model = User
    inlines = (VisitAdminInline, ChildrenAdminInline, InvintationAdminInline)

    readonly_fields = ('date_joined', 'last_login', 'used_invintation_', 'phone_code',
                       'phone_confirmed', 'device_token', 'count_to_free_visit', 'free_reason',)
    list_display = ("fio", "phone", "email", "date_joined", "visits_count", "last_visit", "last_end")
    list_filter = (ActiveVisitFilter, "phone_confirmed", "date_joined", "last_login", "is_staff", VisitsCountGreaterFilter, VisitsCountLowerFilter)
    actions = [export_selected_objects]

    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput},
    }

    def visits_count(self, obj):
        return obj.visits_count
    visits_count.admin_order_field = 'visits_count'

    def last_visit(self, obj):
        return obj.last_visit
    last_visit.admin_order_field = 'last_visit'

    def last_end(self, obj):
        return obj.last_end
    last_end.admin_order_field = 'last_end'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            visits_count=Count('visits_user'),
            last_visit=Max('visits_user__date'),
            last_end=Max(ExpressionWrapper(F('visits_user__date')+Cast(Concat(Case(When(visits_user__duration__gt=0, then=F("visits_user__duration")), default=0), Value(' seconds'), output_field=CharField()), output_field=DurationField()), output_field=DateTimeField())),
        )

    def fio(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def used_invintation_(self, obj):
        return model_admin_url(obj.used_invintation)

    fieldsets = (
        (None, {'fields' : (
            'username',
            'password',
        )}),
        ("Подтверждение", { 'fields' : (
            'phone_code',
            'phone_confirmed',
            'used_invintation_',
            'groups',
        )}),
        ("Персональная информация", { 'fields' : (
            'email',
            'first_name',
            'last_name',
            'phone',
            'count_to_free_visit',
            'free_reason',
        )}),
        ("Доступы", { 'fields' : (
            'is_staff',
            'is_superuser',
        )}),
        ("Важные даты", { 'fields' : (
            'date_joined',
            'last_login',
        )}),
    )

    def save_formset(self, request, form, formset, change):
        if getattr(formset, 'save_before', None):
            formset.save_before(request, form, formset, change)
        formset.save()
