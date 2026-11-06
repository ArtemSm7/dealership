from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse

from .models import Brand, Car, Order, OrderEvent
from .serializers import BrandSerializer, CarSerializer, OrderSerializer, OrderEventSerializer

from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.exceptions import ValidationError

import json, re



def catalog_view(request):
    cars = Car.objects.all()
    brands = Brand.objects.all()

    # Поиск по тексту (марка ИЛИ модель)
    search_query = request.GET.get('search')
    if search_query:
        cars = cars.filter(
            Q(model_name__icontains=search_query) | 
            Q(brand__name__icontains=search_query)
        )

    # Фильтр по марке
    brand_id = request.GET.get('brand')
    if brand_id:
        cars = cars.filter(brand_id=brand_id)

    # Сортировка
    ordering = request.GET.get('ordering')
    if ordering:
        cars = cars.order_by(ordering)

    return render(request, 'main/catalog.html', {
        'cars': cars,
        'brands': brands,
        'current_search': search_query,
        'current_brand': brand_id,
        'current_ordering': ordering
    })


def car_detail_view(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    return render(request, 'main/car_detail.html', {'car': car})

def format_phone(phone):
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11 and digits[0] in ['7', '8']:
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return phone


def favorites_view(request):
    ids_str = request.GET.get('ids', '')
    if ids_str:
        ids = [int(id) for id in ids_str.split(',') if id.isdigit()]
        cars = Car.objects.filter(id__in=ids)
    else:
        cars = []
    return render(request, 'main/favorites.html', {'cars': cars})


@staff_member_required
def dashboard_view(request):
    orders = Order.objects.all().order_by('-created_at')
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'main/dashboard.html', {'orders': orders})

@staff_member_required
def control_center_view(request):
    return render(request, 'main/control_center.html')


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    
class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # Точный фильтр по ID марки
    filterset_fields = ['brand']
    # Текстовй поиск по названию модели
    search_fields = ['model_name', 'brand__name']
    # Сортировка по цене или году выпуска
    ordering_fields = ['price', 'year']
    
    
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'car__brand']
    
    def get_permission(self):
        """
        Разграничение доступа 
        Оставлять заявку (POST) может кто угодно, а управлять ими — только персонал.
        """
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]
    
    def perform_update(self, serializer):
        """
        Составная операция с транзакцией "Всё или ничего".
        """
        order = self.get_object()
        old_status = order.status
        new_status = serializer.validated_data.get('status', old_status)
        
        with transaction.atomic():
            # Сохранение нового статуса заявки
            updated_order = serializer.save()
            if old_status != new_status:
                # Создание события изменения статуса
                OrderEvent.objects.create(
                    order=updated_order,
                    initiator=self.request.user,
                    old_status=old_status,
                    new_status=new_status
                )
                
                # Синхронное бронирование машины
                if new_status == 'process':
                    car = updated_order.car
                    if not car.is_available:
                        raise ValidationError("Автомобиль уже забронирован.")
                    car.is_available = False
                    car.save()
                    
                # Освобождение машины, если заявку отменили
                elif new_status in ['canceled', 'new']:
                    car = updated_order.car
                    car.is_available = True
                    car.save()
                    
    def destroy(self, request, *args, **kwargs):
        """
        Жёсткая защита от удаления активных заявок.
        """
        order = self.get_object()
        if order.status == 'process':
            return JsonResponse({"non_field_errors": 
                ["Нельзя удалить заявку, находящуюся в обработке."]}, 
                status=400)
            
        car = order.car
        if not car.is_available:
            car.is_available = True
            car.save()
            
        return super().destroy(request, *args, **kwargs)