import os
import sys
import typing

import django
from datetime import datetime
from asgiref.sync import sync_to_async
from django.utils.timezone import localtime

# Добавляем путь к Django проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Устанавливаем настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# Импортируем модели после настройки Django
from apps.account.models import User, Child
from apps.mobile.models import Visit
from apps.stores.models import Store
from apps.mobile.visits_logic import count_to_free_visit, set_visit_if_free

class SerializableUser:
    """Класс-обертка для сериализации пользователя Django."""
    def __init__(self, user: User):
        self.id = user.id
        self.phone = user.phone
        self._user = user

    @property
    @sync_to_async
    def user(self):
        if not hasattr(self, '_loaded_user'):
            self._loaded_user = User.objects.select_related('store').get(id=self.id)
        return self._loaded_user


class DjangoClient:

    @staticmethod
    @sync_to_async
    def get_stores() -> list:
        """Получить список всех магазинов."""
        return list(Store.objects.all())

    @staticmethod
    @sync_to_async
    def get_or_create_user(
            phone: str,
            first_name: typing.Optional[str] = None,
            last_name: typing.Optional[str] = None
    ) -> SerializableUser:
        """Получить или создать пользователя."""
        phone = phone.replace('+', '')  # Убираем + если есть
        first_name = first_name or '-'
        last_name = last_name or '-'
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            try:
                # в старой базе телефоны начинаются с 8
                user = User.objects.get(phone='8' + phone[1:])
            except User.DoesNotExist:
                user = User.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    phone_confirmed=True,
                    source_platform='telegram_bot',
                    # Подтверждаем телефон, так как он получен через Telegram
                )
        return SerializableUser(user)

    @staticmethod
    @sync_to_async
    def update_user_store(user: SerializableUser, store_id: int) -> SerializableUser:
        """Обновить магазин пользователя."""
        user_obj = User.objects.get(id=user.id)
        user_obj.store_id = store_id
        user_obj.save()
        return SerializableUser(user_obj)

    @staticmethod
    @sync_to_async
    def get_user_children(user: SerializableUser) -> list:
        """Получить список детей пользователя."""
        return list(Child.objects.filter(my_parent_id=user.id))

    @staticmethod
    @sync_to_async
    def add_child(user: SerializableUser, name: str, birth_date_str: str) -> Child:
        """Добавить ребенка."""
        birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y").date()
        age = (datetime.now().date() - birth_date).days // 365
        
        child = Child.objects.create(
            my_parent_id=user.id,
            name=name,
            birth_date=birth_date,
            age=age,
            sex='M'  # По умолчанию, можно добавить выбор пола в боте
        )
        return child

    @staticmethod
    @sync_to_async
    def create_visit(user: SerializableUser, duration_hours: int, children_ids: list, store_id: int = None) -> Visit:
        """Создать новое посещение."""
        visit = Visit(
            user_id=user.id,
            date=datetime.now(),
            duration=duration_hours * 60,  # Переводим минуты в секунды
            is_active=True,
            store_id=store_id,
            is_confirmed=False,
        )
        set_visit_if_free(visit)
        visit.save()
        if children_ids:
            visit.children.set(Child.objects.filter(id__in=children_ids))
        # Обновляем объект, чтобы получить связанные данные
        visit = Visit.objects.select_related('store').prefetch_related('children').get(id=visit.id)
        return visit

    @staticmethod
    @sync_to_async
    def get_user_visits(user: SerializableUser) -> list:
        """Получить список посещений пользователя."""
        return list(Visit.objects.filter(user_id=user.id)
                   .prefetch_related('children')
                   .order_by('-date'))

    @staticmethod
    @sync_to_async
    def user_count_to_free_visit(user: SerializableUser) -> str:
        """Сколько еще нужно до бесплатного визита."""
        user = User.objects.get(id=user.id)
        cnt = count_to_free_visit(user)[0]
        if cnt == 0:
            last_visit = Visit.objects.filter(user_id=user.id).last()
            if (localtime() - last_visit.date).days < 10:
                return 1
        return cnt

    @staticmethod
    @sync_to_async
    def user_has_free_visit(user: SerializableUser) -> bool:
        """Есть ли у пользователя бесплатный визит."""
        user = User.objects.get(id=user.id)
        if count_to_free_visit(user)[0] == 0:
            last_visit = Visit.objects.filter(user_id=user.id).last()
            if (localtime() - last_visit.date).days < 10:
                return True
        return False


    @staticmethod
    @sync_to_async
    def get_visit_children(visit: Visit) -> list:
        """Получить список детей для посещения."""
        return list(visit.children.all())

    @staticmethod
    @sync_to_async
    def get_visit_children_names(visit: Visit) -> list:
        """Получить список имен детей для посещения."""
        return [child.name for child in visit.children.all()]

    @staticmethod
    @sync_to_async
    def update_last_telegram_bot_visit_date(user: SerializableUser) -> None:
        user = User.objects.get(id=user.id)
        today = localtime().date()
        if user.last_telegram_bot_visit_date is None or user.last_telegram_bot_visit_date < today:
            user.last_telegram_bot_visit_date = today
            user.save()
