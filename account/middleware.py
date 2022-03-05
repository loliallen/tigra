import logging


logger = logging.getLogger(__name__)

class RemoveTokenFromCheckInvinationMiddleware(object):
    def __init__(self, get_response):
        """
        One-time configuration and initialisation.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Code to be executed for each request before the view (and later
        middleware) are called.
        """
        #  TODO: удалить когда фронт перестанет слать HTTP_AUTHORIZATION в этот метод
        if request.method == 'PUT' and request.path == '/account/use/invintation/':
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

