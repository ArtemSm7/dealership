from django.db import models
from django.contrib.auth.models import User

class Brand(models.Model):
    name = models.CharField(
        max_length=100, 
        verbose_name="Марка"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Марка"
        verbose_name_plural = "Марки"

class Car(models.Model):
    brand = models.ForeignKey(
        Brand, 
        on_delete=models.CASCADE, 
        verbose_name="Марка"
    )
    model_name = models.CharField(
        max_length=100, 
        verbose_name="Модель"
    )
    year = models.IntegerField(verbose_name="Год выпуска")
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Цена (руб.)"
    )
    is_used = models.BooleanField(
        default=False, 
        verbose_name="С пробегом"
    )
    image_url = models.URLField(
        blank=True, 
        verbose_name="Ссылка на фото"
    )
    is_available = models.BooleanField(
        default=True, 
        verbose_name="В наличии"
    )

    def __str__(self):
        return f"{self.brand.name} {self.model_name} ({self.year})"

    class Meta:
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('process', 'В обработке'),
        ('done', 'Завершена'),
        ('canceled', 'Отменена'),
    ]

    car = models.ForeignKey(
        Car, 
        on_delete=models.CASCADE, 
        verbose_name="Автомобиль"
    )
    client_name = models.CharField(
        max_length=100, 
        verbose_name="Имя клиента"
    )
    client_phone = models.CharField(
        max_length=20, 
        verbose_name="Телефон"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='new', 
        verbose_name="Статус"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Дата заявки"
    )

    def __str__(self):
        return f"Заявка от {self.client_name} на {self.car}"

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        
class OrderEvent(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name="Заявка"
    )
    initiator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Инициатор"
    )
    old_status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES,
        verbose_name="Старый статус"
    )
    new_status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES,
        verbose_name="Новый статус"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время события"
    )
    
    def __str__(self):
        return f"Заявка #{self.order.id}: {self.old_status} -> {self.new_status}"
    
    class Meta:
        verbose_name = "Событие заявки"
        verbose_name_plural = "История заявок"
        ordering = ['-created_at']