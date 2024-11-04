import datetime

from django.contrib.admin import ListFilter
from django.contrib.admin.options import IncorrectLookupParameters
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class DateListFilter(ListFilter):
    nullable = False
    parameter_name = None

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        if self.parameter_name is None:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify a 'parameter_name'."
                % self.__class__.__name__
            )
        if self.parameter_name in params:
            value = params.pop(self.parameter_name)
            self.used_parameters[self.parameter_name] = value

        self.field_generic = '%s__' % self.parameter_name
        self.date_params = {k: v for k, v in params.items() if k.startswith(self.field_generic)}

        lookup_choices = self.lookups(request, model_admin)
        if lookup_choices is None:
            lookup_choices = ()
        self.lookup_choices = list(lookup_choices)

    def lookups(self, request, model_admin):

        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        today = now.date()
        tomorrow = today + datetime.timedelta(days=1)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        next_year = today.replace(year=today.year + 1, month=1, day=1)

        lookup_kwarg_since = '%s__gte' % self.parameter_name
        lookup_kwarg_until = '%s__lt' % self.parameter_name
        links = (
            (_('Any date'), {}),
            (_('Today'), {
                lookup_kwarg_since: str(today),
                lookup_kwarg_until: str(tomorrow),
            }),
            (_('Past 7 days'), {
                lookup_kwarg_since: str(today - datetime.timedelta(days=7)),
                lookup_kwarg_until: str(tomorrow),
            }),
            (_('This month'), {
                lookup_kwarg_since: str(today.replace(day=1)),
                lookup_kwarg_until: str(next_month),
            }),
            (_('This year'), {
                lookup_kwarg_since: str(today.replace(month=1, day=1)),
                lookup_kwarg_until: str(next_year),
            }),
        )
        if self.nullable:
            self.lookup_kwarg_isnull = '%s__isnull' % self.parameter_name
            links += (
                (_('No date'), {self.field_generic + 'isnull': 'True'}),
                (_('Has date'), {self.field_generic + 'isnull': 'False'}),
            )
        return links

    def has_output(self):
        return len(self.lookup_choices) > 0

    def value(self):
        """
        Return the value (in string format) provided in the request's
        query string for this filter, if any, or None if the value wasn't
        provided.
        """
        return self.used_parameters.get(self.parameter_name)

    def expected_parameters(self):
        return [self.parameter_name]

    def choices(self, changelist):
        for title, param_dict in self.lookup_choices:
            yield {
                'selected': self.date_params == param_dict,
                'query_string': changelist.get_query_string(param_dict, [self.field_generic]),
                'display': title,
            }

    def queryset(self, request, queryset):
        try:
            return queryset.filter(**self.used_parameters)
        except (ValueError, ValidationError) as e:
            # Fields may raise a ValueError or ValidationError when converting
            # the parameters to the correct type.
            raise IncorrectLookupParameters(e)