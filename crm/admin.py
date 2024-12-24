from django.contrib import admin
from .models import Rates, Requests, AssignedRequest, ActiveRequest, Users, RequestPhoto, Wallet, CorrectionFactor, Operator, CorrectionFactor2
from django.utils.html import format_html, format_html_join
from django.urls import path, reverse
from django.shortcuts import redirect

# Административная панель для модели Rates
@admin.register(Rates)
class RatesAdmin(admin.ModelAdmin):
    list_display = (
        'aed_thb',
        'gbp_thb',
        'eur_thb',
        'usd_100',
        'usd_50',
        'rub_cash',
        'rub_tra',
        'aed_thb_sell',
        'gbp_thb_sell',
        'eur_thb_sell',
        'usd_100_sell',
        'usd_50_sell',
        'rub_cash_sell',
        'rub_tra_sell',
        'usdt_bot',
        'usdt_bot_sell',
    )
    list_filter = ('aed_thb', 'gbp_thb', 'eur_thb')  # Пример фильтров
    search_fields = ('aed_thb', 'gbp_thb', 'eur_thb')  # Поиск по полям
    ordering = ('aed_thb',)  # Сортировка по AED

    def has_add_permission(self, request):
        return False

@admin.register(Requests)
class RequestsAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'timestamp', 'amount_send', 'amount_come', 'amount_come_rub', 'first_name', 'status', 'display_photos', 'operator_id', 'view_details',)
    list_filter = ('timestamp', 'status', 'operator_id')  # Добавлен фильтр по статусу
    search_fields = ('first_name', 'operator_id')  # Поиск по chat_id и имени пользователя
    ordering = ('-timestamp',)  # Сортировка по времени создания в обратном порядке
    list_editable = ('status',)  # Позволяет редактировать статус прямо из списка

    def display_photos(self, obj):
        photos = obj.photos.all()
        if photos.exists():
            return format_html_join(
                '',
                '''
                <a href="data:image/jpeg;base64,{0}" target="_blank">
                    <img src="data:image/jpeg;base64,{0}" width="50" />
                </a>
                ''',
                ((photo.get_base64_image(),) for photo in photos)
            )
        return 'Нет фото'

    display_photos.short_description = 'Фотографии'

    # Добавляем дополнительные возможности для отображения и редактирования
    def get_readonly_fields(self, request, obj=None):
        # timestamp только для чтения
        return ('timestamp',)

    def has_add_permission(self, request):
        return False

    def view_details(self, obj):
        # Создание кнопки с ссылкой на кастомное представление
        url = reverse('crm:request_detail', args=[obj.id])
        return format_html('<a class="button" href="{}" target="_blank">Посмотреть</a>', url)

    view_details.short_description = "Детали"  # Название колонки
    view_details.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:request_id>/details/',
                self.admin_site.admin_view(self.redirect_to_request_detail),
                name='request-detail',
            ),
        ]
        return custom_urls + urls

    def redirect_to_request_detail(self, request, request_id):
        # Перенаправление администратора на внешний маршрут для просмотра деталей
        return redirect(f"/requests/{request_id}/")
# Административная панель для модели AssignedRequest
@admin.register(AssignedRequest)
class AssignedRequestAdmin(admin.ModelAdmin):
    list_display = ('operator_id', 'request_id', 'assigned_at')
    list_filter = ('assigned_at',)
    search_fields = ('operator_id', 'request_id')
    ordering = ('-assigned_at',)  # Сортировка по дате в обратном порядке

    def has_add_permission(self, request):
        return False
# Административная панель для модели ActiveRequest
@admin.register(ActiveRequest)
class ActiveRequestAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'request_id', 'entered_sum', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('user_id', 'request_id')
    ordering = ('-timestamp',)  # Сортировка по дате в обратном порядке

    def has_add_permission(self, request):
        return False

@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'username', 'first_name', 'phone', 'registration_date', 'total_amount', 'total_req', 'referrer_id', 'bonus', 'display_user_photos')
    list_filter = ('registration_date',)
    search_fields = ('chat_id', 'username', 'first_name', 'last_name')
    ordering = ('-registration_date',)  # Сортировка по дате регистрации в обратном порядке


    def display_user_photos(self, obj):
        photos = RequestPhoto.objects.filter(request__chat_id=obj.chat_id)
        if photos.exists():
            return format_html(''.join([
                f'''
                <a href="data:image/jpeg;base64,{photo.get_base64_image()}" target="_blank">
                    <img src="data:image/jpeg;base64,{photo.get_base64_image()}" width="50" />
                </a>
                ''' for photo in photos
            ]))
        return 'Нет фото'

    display_user_photos.short_description = 'Фотографии пользователя'

    def has_add_permission(self, request):
        return False

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'wallet')
    search_fields = ('user_id', 'wallet')
    ordering = ('user_id',)

@admin.register(CorrectionFactor)
class CorrectionFactorAdmin(admin.ModelAdmin):
    list_display = ('factor_key', 'buy_factor', 'sell_factor')
    search_fields = ('factor_key',)
    ordering = ('factor_key',)

    def has_add_permission(self, request):
        return False

@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__id', 'user__chat_id')
    ordering = ('user__id',)

@admin.register(CorrectionFactor2)
class CorrectionFactor2Admin(admin.ModelAdmin):
    list_display = ('factor_key', 'buy_factor', 'sell_factor')
    search_fields = ('factor_key',)
    ordering = ('factor_key',)

    def has_add_permission(self, request):
        return False
