from django.contrib import admin

from account.admin.user import CustomUserAdmin
from account.admin.notify import NotifyAdmin
from account.admin.invintations import InvintationsAdmin
from account.models import User, Notification, Child, Invintation

admin.site.register(User, CustomUserAdmin)
admin.site.register(Notification, NotifyAdmin)
admin.site.register(Child)
admin.site.register(Invintation, InvintationsAdmin)

admin.site.site_header = 'Тигра панель администратора'
