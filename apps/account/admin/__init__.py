from django.contrib import admin

from apps.account.admin.user import CustomUserAdmin
from apps.account.admin.notify import NotifyAdmin, ScheduledNotifyAdmin
from apps.account.admin.invintations import InvintationsAdmin
from apps.account.models import User, Notification, SchedulerNotify, Child, Invintation

admin.site.register(User, CustomUserAdmin)
admin.site.register(Notification, NotifyAdmin)
admin.site.register(SchedulerNotify, ScheduledNotifyAdmin)
admin.site.register(Child)
admin.site.register(Invintation, InvintationsAdmin)

admin.site.site_header = 'Тигра панель администратора'
