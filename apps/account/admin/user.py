from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, UserChangeForm
from django.db import models
from django.db.models import (
    Count, Max, F, ExpressionWrapper, DurationField, DateTimeField, Value,
    CharField, Case, When
)
from django.db.models.functions import Cast, Concat
from django.http import HttpResponseRedirect
from django.utils import timezone
from django_admin_inline_paginator.admin import TabularInlinePaginated

from apps.mobile.visits_logic import set_visit_if_free, count_to_free_visit as cnt_to_free_visit_logic
from apps.mobile.models import Visit, FreeReason
from apps.account.admin.tools import model_admin_url, InlineChangeList
from apps.account.models import User, Child, Invintation


class VisitAdminInline(TabularInlinePaginated):
    model = Visit
    fk_name = 'user'
    extra = 0
    per_page = 5
    can_delete = False
    ordering = ('date',)
    readonly_fields = ("is_free", "is_active", "free_reason", "staff_")
    fields = ("date", "duration", "is_free", "free_reason", "staff_")

    def staff_(self, obj):
        return model_admin_url(obj.staff)
    staff_.short_description = 'Сотрудник'

    def get_formset(self, request, obj=None, **kwargs):
        formset_class = super().get_formset(request, obj, **kwargs)

        class FormSet(formset_class):
            def clean(self):
                # check if more one visit per time
                new_instance = False
                for form in self.forms:
                    current_is_new = form.instance.id is None
                    if current_is_new:
                        if not new_instance:
                            new_instance = True
                        else:
                            raise forms.ValidationError('Не более одного нового визита')
                return super().clean()

            def save_before(self, request, form, formset, change):
                # set free visits on saving
                for form in formset:
                    if form.instance.staff is None:
                        form.instance.staff = request.user
                        set_visit_if_free(form.instance)
                        form.instance.save()
        return FormSet


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


class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone",)

    phone = forms.RegexField(r'^\d{11}$', help_text='в номере должно быть 11 цифр', label='Номер телефона')


class UserForm(UserChangeForm):
    phone = forms.RegexField(r'^\d{11}$', help_text='в номере должно быть 11 цифр', label='Номер телефона')


class CustomUserAdmin(UserAdmin):
    model = User
    form = UserForm
    add_form = UserCreationForm
    #add_form_template = None
    inlines = (VisitAdminInline, ChildrenAdminInline, InvintationAdminInline)
    search_fields = ("phone", "first_name", "last_name", "email")

    readonly_fields = (
        'date_joined', 'last_login', 'used_invintation_', 'phone_code',
        'phone_confirmed', 'device_token', 'count_to_free_visit', 'free_reason',
        'last_mobile_app_visit_date',
    )
    list_display = (
        "fio", "phone", "email", "date_joined", "visits_count",
        "last_visit", "last_end", "last_mobile_app_visit_date"
    )
    list_filter = (ActiveVisitFilter, "phone_confirmed", "date_joined", "last_login", "is_staff", "groups", VisitsCountGreaterFilter, VisitsCountLowerFilter)
    actions = [export_selected_objects]

    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput},
    }

    def visits_count(self, obj):
        return obj.visits_count
    visits_count.admin_order_field = 'visits_count'
    visits_count.short_description = 'Количество визитов'

    def last_visit(self, obj):
        return obj.last_visit
    last_visit.admin_order_field = 'last_visit'
    last_visit.short_description = 'Последний визит начало'

    def last_end(self, obj):
        return obj.last_end
    last_end.admin_order_field = 'last_end'
    last_end.short_description = 'Последний визит конец'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            visits_count=Count('visits_user'),
            # дата последнего визита
            last_visit=Max('visits_user__date'),
            # время конца последнего визита
            last_end=Max(
                ExpressionWrapper(
                    (
                        F('visits_user__date') +
                        Cast(
                            # преобразуем хранящиеся в int секунды в timedelta и складываем с датой-время начала посещения
                            Concat(
                                Case(When(visits_user__duration__gt=0, then=F("visits_user__duration")), default=0),
                                Value(' seconds'),
                                output_field=CharField()
                            ),
                            output_field=DurationField()
                        )
                    ),
                    output_field=DateTimeField()
                )
            ),
        )

    def fio(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def used_invintation_(self, obj):
        return model_admin_url(obj.used_invintation)

    def count_to_free_visit(self, obj):
        return cnt_to_free_visit_logic(obj)[0]
    count_to_free_visit.short_description = 'Бесплатный визит через'

    def free_reason(self, obj):
        return FreeReason(cnt_to_free_visit_logic(obj)[1]).name
    free_reason.short_description = 'Причина бесплатного визита'

    fieldsets = [
        ("Персональная информация", {'fields': [
            'email',
            'first_name',
            'last_name',
            'phone',
            'password',
            'agree_for_video',
            'agree_for_sms_notifications',
            'comment_from_staff',
        ]}),
        ("События", {'fields': [
            'phone_code',
            'phone_confirmed',
            'used_invintation_',
            'date_joined',
            'last_mobile_app_visit_date',
            'last_login',
            'count_to_free_visit',
            'free_reason',
        ]}),
        ("Доступы", {'fields': [
            'is_staff',
            'is_superuser',
            'groups',
        ]}),
    ]

    add_fieldsets = [
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone'),
        }),
    ]

    fields_permissions = {
        'account.can_change_email': ('email',),
        'account.can_change_password': ('password',),
        'account.can_see_events': (
                'phone_code',
                'phone_confirmed',
                'used_invintation_',
                'date_joined',
                'last_login',
                'count_to_free_visit',
                'free_reason',
        ),
        'account.can_change_permissions': (
            'is_staff',
            'is_superuser',
            'groups',
        )
    }

    # hide inline models in creation
    def get_inline_instances(self, request, obj=None):
        return obj and super().get_inline_instances(request, obj) or []

    def save_formset(self, request, form, formset, change):
        # call save before method on FormSet to set up free visits
        if getattr(formset, 'save_before', None):
            formset.save_before(request, form, formset, change)
        formset.save()
