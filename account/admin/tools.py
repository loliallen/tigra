from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.admin.views.main import ChangeList
from django.shortcuts import resolve_url
from django.utils.html import format_html
from django.utils.safestring import SafeText


def model_admin_url(obj, name: str = None, is_list: bool = False) -> str:
    if obj is None:
        return "-"
    if is_list:
        return format_html(", ".join([model_admin_url(item) for item in obj]))
    url = resolve_url(admin_urlname(obj._meta, SafeText("change")), obj.pk)
    return format_html('<a href="{}">{}</a>', url, name or str(obj))


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
