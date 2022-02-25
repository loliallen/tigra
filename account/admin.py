from django.contrib import admin
from django import forms
from django.contrib.auth.hashers import make_password
from django.contrib.auth.admin import UserAdmin
from django.db import models
from django.contrib.admin.views.main import ChangeList
from django.core.paginator import EmptyPage, InvalidPage, Paginator


from mobile.models import Visit
from .models import User, Child, Invintation, TmpHash, Notification
# Register your models here.



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

class InlineChangeList(object):
    can_show_all = True
    multi_page = True
    get_query_string = ChangeList.__dict__['get_query_string']

    def __init__(self, request, page_num, paginator):
        self.show_all = 'all' in request.GET
        self.page_num = page_num
        self.paginator = paginator
        self.result_count = paginator.count
        self.params = dict(request.GET.items())


class VisitAdminInline(admin.TabularInline):
    model = Visit
    fk_name = 'user'
    extra = 0
    template = 'admin/edit_inline/tabular_paginated.html'
    per_page = 5

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


class CustomUserAdmin(UserAdmin):
    model = User
    inlines = (VisitAdminInline, ChildrenAdminInline, InvintationAdminInline)

    readonly_fields = ('date_joined', 'last_login', 'used_invintation')

    fieldsets = (
        (None, { 'fields' : (
            'username',
            'password',
        )}),
        ("Confirmation", { 'fields' : (
            'phone_code',
            'phone_confirmed',
            'device_token',
        )}),
        ("Personal Info", { 'fields' : (
            'email',
            'first_name',
            'last_name',
            'phone',
            # 'children',
        )}),
        ("Permissions", { 'fields' : (
            'is_staff',
            'is_superuser',
        )}),
        ("important Dates", { 'fields' : (
            'date_joined',
            'last_login',
        )}),
        ("Additional Fields", {'fields': (
            # 'visits',
            # 'my_invintations',
            'used_invintation',
        )}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Notification)
admin.site.register(Child)
admin.site.register(Invintation)
