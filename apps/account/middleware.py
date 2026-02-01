import logging
from datetime import timedelta

from django.contrib.auth import logout
from django.http import HttpRequest
from django.utils import timezone
from django.utils.timezone import localtime

logger = logging.getLogger(__name__)


class RemoveTokenFromCheckInvinationMiddleware(object):
    def __init__(self, get_response):
        """
        One-time configuration and initialisation.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        """
        Code to be executed for each request before the view (and later
        middleware) are called.
        """
        #  TODO: удалить когда фронт перестанет слать HTTP_AUTHORIZATION в этот метод
        if request.method in ['PUT', 'POST'] and request.path == '/account/use/invintation/':
            if request.META.get('HTTP_AUTHORIZATION'):
                del request.META['HTTP_AUTHORIZATION']
        if request.method == 'POST' and request.path == '/account/users/':
            logger.info(f"{request.body}")
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Called just before Django calls the view.
        """
        return None

    def process_exception(self, request, exception):
        """
        Called when a view raises an exception.
        """
        return None

    def process_template_response(self, request, response):
        """
        Called just after the view has finished executing.
        """
        return response


class UpdateLastVisitMiddleware(object):
    def __init__(self, get_response):
        """
        One-time configuration and initialisation.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        """
        Code to be executed for each request before the view (and later
        middleware) are called.
        """
        today = (timezone.now()).date()
        user = request.user
        api_routes = ('/api/', '/account/', '/mobile/', '/promo/')
        if request.path.startswith(api_routes) and user and user.is_authenticated:
            if user.last_mobile_app_visit_date is None or user.last_mobile_app_visit_date < today:
                user.last_mobile_app_visit_date = today
                user.save()
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Called just before Django calls the view.
        """
        return None

    def process_exception(self, request, exception):
        """
        Called when a view raises an exception.
        """
        return None

    def process_template_response(self, request, response):
        """
        Called just after the view has finished executing.
        """
        return response


class CheckLastAdminActivityMiddleware(object):
    def __init__(self, get_response):
        """
        One-time configuration and initialisation.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        """
        Code to be executed for each request before the view (and later
        middleware) are called.
        """
        user = request.user
        if request.path.startswith('/admin/') and user and user.is_authenticated:
            # разлогинивать пользователей из админки с последней активностью больше 2 часов назад
            two_hours_ago = localtime() - timedelta(hours=2)
            five_minutes_ago = localtime() - timedelta(minutes=5)
            if (
                user.last_admin_activity_date
                and user.last_admin_activity_date < two_hours_ago
                and localtime(user.last_login) < two_hours_ago
            ):
                logout(request)
            elif user.last_admin_activity_date is None or user.last_admin_activity_date < five_minutes_ago:
                user.last_admin_activity_date = localtime()
                user.save()
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Called just before Django calls the view.
        """
        return None

    def process_exception(self, request, exception):
        """
        Called when a view raises an exception.
        """
        return None

    def process_template_response(self, request, response):
        """
        Called just after the view has finished executing.
        """
        return response
