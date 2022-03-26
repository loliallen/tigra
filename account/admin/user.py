from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.db import models
from django.db.models import Count

from mobile.models import Visit
from mobile.visits_logic import set_visit_if_free
from account.admin.tools import model_admin_url, InlineChangeList
from account.models import User, Child, Invintation


class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('__all__')

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_pasword(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


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


class UsersFilter(admin.SimpleListFilter):
    title = 'Кол-во посещений'
    parameter_name = 'visit_count'

    def lookups(self, request, model_admin):
        return tuple(
            (f'{i}+', f'{i}+') for i in [1, 3, 5, 10, 15, 20, 30, 50]
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(
            visits_count__gte=int(self.value()[:-1]),
        )


class CustomUserAdmin(UserAdmin):
    model = User
    inlines = (VisitAdminInline, ChildrenAdminInline, InvintationAdminInline)

    readonly_fields = ('date_joined', 'last_login', 'used_invintation_', 'phone_code',
                       'phone_confirmed', 'device_token', 'count_to_free_visit', 'free_reason',)
    list_display = ("fio", "phone", "email", "date_joined", "visits_count")
    list_filter = ("phone_confirmed", "date_joined", "last_login", "is_staff", UsersFilter)

    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput},
    }

    def visits_count(self, obj):
        return obj.visits_count
    visits_count.admin_order_field = 'visits_count'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(visits_count=Count('visits_user'))

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
