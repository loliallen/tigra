from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, UserChangeForm
from django.db import models
from django_object_actions import DjangoObjectActions
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import resolve
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime
from django_admin_inline_paginator.admin import TabularInlinePaginated
from rangefilter.filters import DateRangeFilter
from django.utils.translation import gettext_lazy as _

from apps.account.logic.facades.users import make_report
from apps.account.logic.selectors.users import users_with_visits
from apps.mobile.visits_logic import set_visit_if_free, count_to_free_visit as cnt_to_free_visit_logic
from apps.mobile.models import Visit, FreeReason
from apps.account.admin.tools import model_admin_url
from apps.account.models import User, Child, Invintation, AccountDocuments
from utils.admin.filter import DateListFilter, NumericListFilter
from apps.stores.models import Store


class VisitAdminInline(TabularInlinePaginated):
    model = Visit
    fk_name = 'user'
    extra = 0
    per_page = 5
    can_delete = False
    ordering = ('date',)
    readonly_fields = ("is_free", "is_active", "free_reason", "staff_")
    fields = ("date", "duration", "is_free", "free_reason", "is_confirmed", "staff_", "children", "store")

    class Form(forms.ModelForm):
        duration = forms.ChoiceField(choices=(
            (60 * 30, '30 минут'),
            (60 * 60, '1 час'),
            (2 * 60 * 60, '2 часа'),
            (11 * 60 * 60, 'до конца дня'),
        ),)
        is_confirmed = forms.BooleanField(initial=True, required=False, disabled=True)

    form = Form

    def staff_(self, obj):
        return model_admin_url(obj.staff)
    staff_.short_description = 'Сотрудник'

    def get_parent_object_from_request(self, request):
        resolved = resolve(request.path_info)
        if resolved.kwargs.get('object_id'):
            return self.parent_model.objects.get(pk=resolved.kwargs['object_id'])
        return None

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "children":
            user = self.get_parent_object_from_request(request)
            kwargs["queryset"] = Child.objects.filter(my_parent=user)
            kwargs["widget"] = forms.widgets.CheckboxSelectMultiple()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "store":
            customer = self.get_parent_object_from_request(request=request)
            admin = request.user
            if customer.store or admin.store:
                # если магазин выбран только у одного либо они совпадают
                if not (customer.store and admin.store and customer.store != admin.store):
                    store = customer.store or request.user.store
                    kwargs["queryset"] = Store.objects.filter(id=store.id)
                    kwargs["initial"] = store
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_formset(self, request, obj=None, **kwargs):
        formset_class = super().get_formset(request, obj, **kwargs)

        class FormSet(formset_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                for form in self.forms:
                    customer = kwargs['instance']
                    form.fields["children"].queryset = Child.objects.filter(my_parent=customer)
                    # Делаем поле store обязательным для новых визитов
                    if not form.instance.pk:
                        form.fields['store'].required = True
                    admin = request.user
                    show_all_stores = True
                    if customer.store or admin.store:
                        # если магазин выбран только у одного либо они совпадают
                        if not (customer.store and admin.store and customer.store != admin.store):
                            store = customer.store or admin.store
                            if not form.instance.pk:
                                form.fields['store'].queryset = Store.objects.filter(id=store.id)
                                show_all_stores = False
                    if show_all_stores:
                        form.fields['store'].queryset = Store.objects.all()
                    if not form.initial['is_confirmed']:
                        form.fields['is_confirmed'].disabled = False

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


class DocumentsAdminInline(admin.TabularInline):
    model = AccountDocuments
    extra = 0
    can_delete = True
    fk_name = "user"

    readonly_fields = ("created_at", "added_by")
    fields = ("created_at", "file", "added_by")

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
                    if form.instance.added_by is None:
                        form.instance.added_by = request.user
                        form.instance.save()

        return FormSet


class VisitsCountGreaterFilter(NumericListFilter):
    title = 'Кол-во посещений'
    parameter_name = 'visits_count'


class LastVisitFilter(DateListFilter):
    title = 'Дата последнего визита'
    parameter_name = 'last_visit'


class ActiveVisitFilter(admin.SimpleListFilter):
    title = 'Активный визит'
    parameter_name = 'last_end'

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
                last_end__gte=timezone.now(),
            )
        else:
            return queryset.filter(
                last_end__lt=timezone.now(),
            )


def send_push_selected_objects(modeladmin, request, queryset):
    selected = queryset.values_list('pk', flat=True)
    return HttpResponseRedirect(f'/admin/account/notification/add/?to_users={",".join(str(i) for i in selected)}')
send_push_selected_objects.short_description = "Отправить пуш уведомления"


class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone",)

    phone = forms.RegexField(r'^\d{11}$', help_text='в номере должно быть 11 цифр', label='Номер телефона')


class UserForm(UserChangeForm):
    phone = forms.RegexField(r'^\d{11}$', help_text='в номере должно быть 11 цифр', label='Номер телефона')


class CustomUserAdmin(DjangoObjectActions, UserAdmin):
    model = User
    form = UserForm
    add_form = UserCreationForm
    #add_form_template = None
    inlines = (VisitAdminInline, ChildrenAdminInline, InvintationAdminInline, DocumentsAdminInline)
    search_fields = ("phone", "first_name", "last_name", "email")

    readonly_fields = (
        'date_joined', 'last_login', 'used_invintation_', 'phone_code',
        'phone_confirmed', 'device_token', 'count_to_free_visit', 'free_reason',
        'last_mobile_app_visit_date',
    )
    list_display = (
        "fio", "phone", "visits_count", "last_visit", "last_end", "child_name"
    )
    list_filter = (
        ActiveVisitFilter,
        LastVisitFilter,
        "phone_confirmed",
        ("date_joined", DateRangeFilter),
        ("last_login", DateRangeFilter),
        "is_staff",
        "groups",
        VisitsCountGreaterFilter
    )
    actions = [send_push_selected_objects]
    changelist_actions = ('make_report',)

    def make_report(self, request, obj):
        file = make_report()
        response = HttpResponse(file.getvalue(), content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="report.xls"'
        return response

    make_report.label = "Сгенерировть отчет"

    def visits_count(self, obj):
        return obj.visits_count
    visits_count.admin_order_field = 'visits_count'
    visits_count.short_description = 'Количество визитов'

    def last_visit(self, obj):
        return obj.last_visit
    last_visit.admin_order_field = 'last_visit'
    last_visit.short_description = 'Последний визит начало'

    def last_end(self, obj):
        time = localtime(obj.last_end).time()
        try:
            if (obj.last_end - obj.last_visit).seconds >= 11 * 60 * 60:
                return f"{time} (до конца дня)"
        except:
            pass
        return time
    last_end.admin_order_field = 'last_end'
    last_end.short_description = 'Последний визит конец'

    def child_name(self, obj):
        return mark_safe("<br/>".join([
            child.admin_str() for child in obj.children.all()
        ]))
    child_name.admin_order_field = 'child_name'
    child_name.short_description = 'Дети'
    child_name.allow_tags = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return users_with_visits(queryset).prefetch_related("children")

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
            'store',
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
