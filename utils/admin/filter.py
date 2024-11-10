import datetime
from collections import OrderedDict

from django import forms
from django.contrib.admin import ListFilter
from django.contrib.admin.utils import prepare_lookup_value
from django.contrib.admin.widgets import AdminDateWidget
from django.core.exceptions import ImproperlyConfigured
from django.template.defaultfilters import slugify
from django.utils.encoding import force_str
from django.utils.timezone import make_aware
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import OnceCallMedia


class DateListFilter(ListFilter):
    _request_key = "DJANGO_RANGEFILTER_ADMIN_JS_LIST"
    nullable = False
    parameter_name = None

    def __init__(self, request, params, model, model_admin):
        if self.parameter_name is None:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify a 'parameter_name'."
                % self.__class__.__name__
            )

        self.lookup_kwarg_gte = "{0}__range__gte".format(self.parameter_name)
        self.lookup_kwarg_lte = "{0}__range__lte".format(self.parameter_name)
        self.used_parameters = {}
        for p in self.expected_parameters():
            if p in params:
                value = params.pop(p)
                self.used_parameters[p] = prepare_lookup_value(p, value)

        self.default_gte, self.default_lte = None, None
        if self.used_parameters:
            self.default_gte, self.default_lte = (
                self.used_parameters[self.lookup_kwarg_gte],
                self.used_parameters[self.lookup_kwarg_lte]
            )
        self.request = request
        self.model_admin = model_admin
        self.form = self.get_form(request)

    def has_output(self):
        return True

    def _make_query_filter(self, request, validated_data):
        query_params = {}
        date_value_gte = validated_data.get(self.lookup_kwarg_gte, None)
        date_value_lte = validated_data.get(self.lookup_kwarg_lte, None)

        if date_value_gte:
            query_params["{0}__gte".format(self.parameter_name)] = make_aware(
                datetime.datetime.combine(date_value_gte, datetime.time.min),
            )
        if date_value_lte:
            query_params["{0}__lte".format(self.parameter_name)] = make_aware(
                datetime.datetime.combine(date_value_lte, datetime.time.max),
            )

        return query_params

    def expected_parameters(self):
        return self._get_expected_fields()

    def _get_expected_fields(self):
        return [self.lookup_kwarg_gte, self.lookup_kwarg_lte]

    def choices(self, changelist):
        yield {
            "system_name": force_str(
                slugify(self.title) if slugify(self.title) else id(self.title)
            ),
            "query_string": changelist.get_query_string({}, remove=self._get_expected_fields()),
        }

    def queryset(self, request, queryset):
        if self.form.is_valid():
            validated_data = dict(self.form.cleaned_data.items())
            if validated_data:
                return queryset.filter(**self._make_query_filter(request, validated_data))
        return queryset

    def get_template(self):
        return "rangefilter/date_filter.html"

    template = property(get_template)

    def _get_form_fields(self):
        return OrderedDict(
            (
                (
                    self.lookup_kwarg_gte,
                    forms.DateField(
                        label="",
                        widget=AdminDateWidget(attrs={"placeholder": _("From date")}),
                        localize=True,
                        required=False,
                        initial=self.default_gte,
                    ),
                ),
                (
                    self.lookup_kwarg_lte,
                    forms.DateField(
                        label="",
                        widget=AdminDateWidget(attrs={"placeholder": _("To date")}),
                        localize=True,
                        required=False,
                        initial=self.default_lte,
                    ),
                ),
            )
        )

    def _get_form_class(self):
        fields = self._get_form_fields()

        form_class = type(str("DateRangeForm"), (forms.BaseForm,), {"base_fields": fields})

        # lines below ensure that the js static files are loaded just once
        # even if there is more than one DateRangeFilter in use
        js_list = getattr(self.request, self._request_key, None)
        if not js_list:
            js_list = OnceCallMedia()
            setattr(self.request, self._request_key, js_list)

        form_class.js = js_list

        return form_class

    def get_form(self, _request):
        form_class = self._get_form_class()
        return form_class(self.used_parameters or None)


class NumericListFilter(ListFilter):
    nullable = False
    parameter_name = None

    def __init__(self, request, params, model, model_admin):
        if self.parameter_name is None:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify a 'parameter_name'."
                % self.__class__.__name__
            )

        self.lookup_kwarg_gte = "{0}__range__gte".format(self.parameter_name)
        self.lookup_kwarg_lte = "{0}__range__lte".format(self.parameter_name)
        self.used_parameters = {}
        for p in self.expected_parameters():
            if p in params:
                value = params.pop(p)
                self.used_parameters[p] = prepare_lookup_value(p, value)

        self.default_gte, self.default_lte = None, None
        if self.used_parameters:
            self.default_gte, self.default_lte = (
                self.used_parameters[self.lookup_kwarg_gte],
                self.used_parameters[self.lookup_kwarg_lte]
            )
        self.request = request
        self.model_admin = model_admin
        self.form = self.get_form(request)

    def has_output(self):
        return True

    def get_template(self):
        return "rangefilter/numeric_filter.html"

    template = property(get_template)

    def _get_expected_fields(self):
        return [self.lookup_kwarg_gte, self.lookup_kwarg_lte]

    def expected_parameters(self):
        return self._get_expected_fields()

    def _get_form_fields(self):
        return OrderedDict(
            (
                (
                    self.lookup_kwarg_gte,
                    forms.FloatField(
                        label="",
                        widget=forms.NumberInput(attrs={"placeholder": _("From")}),
                        required=False,
                        localize=True,
                        initial=self.default_lte,
                    ),
                ),
                (
                    self.lookup_kwarg_lte,
                    forms.FloatField(
                        label="",
                        widget=forms.NumberInput(attrs={"placeholder": _("To")}),
                        localize=True,
                        required=False,
                        initial=self.default_lte,
                    ),
                ),
            )
        )

    def _get_form_class(self):
        fields = self._get_form_fields()

        form_class = type(str("NumericRangeFilter"), (forms.BaseForm,), {"base_fields": fields})

        return form_class

    def get_form(self, _request):
        form_class = self._get_form_class()
        return form_class(self.used_parameters or None)

    def queryset(self, request, queryset):
        if self.form.is_valid():
            validated_data = dict(self.form.cleaned_data.items())
            if validated_data:
                return queryset.filter(**self._make_query_filter(request, validated_data))
        return queryset

    def _make_query_filter(self, _request, validated_data):
        query_params = {}
        value_gte = validated_data.get(self.lookup_kwarg_gte, None)
        value_lte = validated_data.get(self.lookup_kwarg_lte, None)

        if value_gte:
            query_params["{0}__gte".format(self.parameter_name)] = value_gte
        if value_lte:
            query_params["{0}__lte".format(self.parameter_name)] = value_lte

        return query_params

    def choices(self, changelist):
        yield {
            "system_name": force_str(
                slugify(self.title) if slugify(self.title) else id(self.title)
            ),
            "query_string": changelist.get_query_string({}, remove=self._get_expected_fields()),
        }
