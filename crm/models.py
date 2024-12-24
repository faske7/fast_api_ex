from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

class Rates(models.Model):
    aed_thb = models.FloatField(blank=True, null=True)
    gbp_thb = models.FloatField(blank=True, null=True)
    eur_thb = models.FloatField(blank=True, null=True)
    usd_100 = models.FloatField(blank=True, null=True)
    usd_50 = models.FloatField(blank=True, null=True)
    rub_cash = models.FloatField(blank=True, null=True)
    rub_tra = models.FloatField(blank=True, null=True)
    aed_thb_sell = models.FloatField(blank=True, null=True)
    gbp_thb_sell = models.FloatField(blank=True, null=True)
    eur_thb_sell = models.FloatField(blank=True, null=True)
    usd_100_sell = models.FloatField(blank=True, null=True)
    usd_50_sell = models.FloatField(blank=True, null=True)
    rub_cash_sell = models.FloatField(blank=True, null=True)
    rub_tra_sell = models.FloatField(blank=True, null=True)
    usdt_bot = models.FloatField(blank=True, null=True)
    usdt_bot_sell = models.FloatField(blank=True, null=True)

    class Meta:
        managed = True  # Django будет управлять таблицей
        db_table = 'rates'  # Имя таблицы в базе данных


class RequestStatus(models.TextChoices):
    NEW = 'NEW', _('Новая')
    IN_PROGRESS = 'IN_PROGRESS', _('В процессе')
    COMPLETED = 'COMPLETED', _('Завершена')
    CANCELED = 'CANCELED', _('Отменена')


class Requests(models.Model):
    id = models.AutoField(primary_key=True)
    chat_id = models.BigIntegerField()  # ID чата пользователя
    operator_id = models.BigIntegerField()  # ID чата opera
    amount = models.IntegerField()  # Сумма
    amount_send = models.IntegerField(null=True, blank=True)  # Сумма отправленных
    amount_come = models.IntegerField(null=True, blank=True)  # Сумма полученных
    amount_come_rub = models.IntegerField(null=True, blank=True)  # Сумма полученных
    first_name = models.CharField(max_length=255, null=True, blank=True)  # Имя пользователя
    timestamp = models.DateTimeField(auto_now_add=True)  # Время создания заявки
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.NEW,
    )  # Состояние заявки

    class Meta:
        managed = True  # Django no будет управлять таблицей
        db_table = 'requests'  # Имя таблицы в базе данных

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None

        # Если запись уже существует, получаем старый статус
        if not is_new:
            try:
                old_obj = Requests.objects.get(pk=self.pk)
                old_status = old_obj.status
            except ObjectDoesNotExist:
                # Если по какой-то причине старой записи не нашли — игнорируем
                pass

        super().save(*args, **kwargs)  # Сначала сохраняем текущее состояние

        # Если старый статус существует и не равен новому - выполняем логику
        if old_status and old_status != self.status:
            # from myapp.models import AssignedRequest, ActiveRequest  # Импорт здесь, чтобы избежать циклических импортов
            with transaction.atomic():
                # Если новый статус - CANCELED или COMPLETED, удаляем связанные записи
                if self.status in [RequestStatus.CANCELED, RequestStatus.COMPLETED]:
                    AssignedRequest.objects.filter(request_id=self.id).delete()
                    ActiveRequest.objects.filter(request_id=self.id).delete()

                # Если старый статус был CANCELED или COMPLETED, а новый - IN_PROGRESS, восстанавливаем
                elif old_status in [RequestStatus.CANCELED,
                                    RequestStatus.COMPLETED] and self.status == RequestStatus.IN_PROGRESS:
                    AssignedRequest.objects.create(
                        operator_id=self.operator_id,
                        request_id=self.id,
                        assigned_at=timezone.now(),
                        first_name=self.first_name,
                    )
                    ActiveRequest.objects.create(
                        user_id=self.chat_id,
                        request_id=self.id,
                        entered_sum=self.amount,
                        timestamp=timezone.now()
                    )
                elif old_status in [RequestStatus.NEW] and self.status == RequestStatus.IN_PROGRESS:
                    AssignedRequest.objects.create(
                        operator_id=self.operator_id,
                        request_id=self.id,
                        assigned_at=timezone.now(),
                        first_name=self.first_name,
                    )

    def __str__(self):
        return f"Request {self.id}от {self.first_name}: {self.get_status_display()}"

class Users(models.Model):
    id = models.AutoField(primary_key=True)  # Автоинкрементирующий ID пользователя
    chat_id = models.BigIntegerField(unique=True)  # Уникальный ID чата пользователя
    username = models.CharField(max_length=255, null=True, blank=True)  # Имя пользователя
    first_name = models.CharField(max_length=255, null=True, blank=True)  # Имя пользователя
    last_name = models.CharField(max_length=255, null=True, blank=True)  # Фамилия пользователя
    registration_date = models.DateTimeField(auto_now_add=True)  # Дата регистрации
    total_amount = models.IntegerField(default=0)  # Общая сумма
    total_req = models.IntegerField(default=0)  # Количество заказов
    referrer_id = models.IntegerField(default=0)  # Количество заказов
    bonus = models.FloatField(default=0)  # Количество заказов
    phone = models.BigIntegerField(unique=True)  # Уникальный ID чата пользователя

    class Meta:
        managed = True
        db_table = 'users'  # Имя таблицы в базе данных
        ordering = ['-registration_date']  # Сортировка по дате регистрации (новые сверху)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.chat_id})"

class RequestPhoto(models.Model):
    id = models.AutoField(primary_key=True)
    request = models.ForeignKey(
        Requests,
        related_name='photos',
        on_delete=models.CASCADE,
        db_column='request_id'
    )
    user = models.ForeignKey(
        Users,
        related_name='photos',
        on_delete=models.CASCADE,
        db_column='chat_id'
    )
    image_data = models.BinaryField()
    uploaded_at = models.DateTimeField()

    def get_base64_image(self):
        import base64
        return base64.b64encode(self.image_data).decode('utf-8')

    class Meta:
        managed = False
        db_table = 'request_photos'

    # Модель AssignedRequest

class AssignedRequest(models.Model):
    operator_id = models.BigIntegerField()  # ID оператора
    request_id = models.IntegerField(unique=True)  # ID заявки
    assigned_at = models.DateTimeField()  # Время назначения
    first_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'assigned_requests'  # Имя таблицы в базе данных

# Модель ActiveRequest
class ActiveRequest(models.Model):
    user_id = models.BigIntegerField(primary_key=True)  # ID пользователя
    request_id = models.IntegerField()  # ID заявки
    entered_sum = models.IntegerField()  # Сумма
    timestamp = models.DateTimeField()  # Время создания

    class Meta:
        managed = True
        db_table = 'active_requests'  # Имя таблицы в базе данных

    def __str__(self):
        return f"ActiveRequest for User {self.user_id} - Request {self.request_id}"

class Wallet(models.Model):
    user_id = models.BigIntegerField(primary_key=True)
    wallet = models.CharField(max_length=255, null=False, blank=False)

    class Meta:
        db_table = 'wallet'
        managed = True

    def __str__(self):
        return f"Wallet: {self.user_id}"

class CorrectionFactor(models.Model):
    factor_key = models.CharField(max_length=255, primary_key=True, db_index=True)
    buy_factor = models.FloatField(null=False, blank=False)
    sell_factor = models.FloatField(null=False, blank=False)

    class Meta:
        db_table = 'correction_factors'
        managed = True

    def __str__(self):
        return f"CorrectionFactor: {self.factor_key}"

class Operator(models.Model):
    user = models.OneToOneField(
        Users,
        on_delete=models.CASCADE,
        primary_key=True,  # Устанавливаем поле как первичный ключ
        related_name='operator_profile'
    )
    user_chat = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        to_field='chat_id',
        related_name='operator_chat_profile',
        db_column='user_chat_id',
        null=True,  # Если связь необязательна
        blank=True
    )
    role = models.CharField(max_length=100, null=True, blank=True)
    # Добавьте дополнительные поля, если необходимо
    # Например:
    # role = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Operator {self.user.chat_id}"

    class Meta:
        db_table = 'operators'
        managed = True

class Message(models.Model):
    request = models.ForeignKey(
        'Requests',
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.CharField(max_length=50, choices=[("operator", "Operator"), ("user", "User")])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)


    class Meta:
        db_table = "messages"  # Указываем явное имя таблицы

class CorrectionFactor2(models.Model):
    factor_key = models.CharField(max_length=255, primary_key=True, db_index=True)
    buy_factor = models.FloatField(null=False, blank=False)
    sell_factor = models.FloatField(null=False, blank=False)

    class Meta:
        db_table = 'correction_factors_night'
        managed = True

    def __str__(self):
        return f"CorrectionFactor2: {self.factor_key}"

