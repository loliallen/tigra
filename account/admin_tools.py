from django import forms
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.admin.views.main import ChangeList
from django.shortcuts import resolve_url
from django.utils.html import format_html
from django.utils.safestring import SafeText

from .models import User


def model_admin_url(obj, name: str = None) -> str:
    if obj is None:
        return "-"
    url = resolve_url(admin_urlname(obj._meta, SafeText("change")), obj.pk)
    return format_html('<a href="{}">{}</a>', url, name or str(obj))


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
