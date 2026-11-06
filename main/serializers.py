from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Brand, Car, Order, OrderEvent

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']
        
class CarSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(), source='brand', write_only=True
    )
    
    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'brand_id', 'model_name', 'year', 
            'price', 'is_used', 'image_url', 'is_available'
        ]
        
class OrderEventSerializer(serializers.ModelSerializer):
    initiator_name = serializers.CharField(source='initiator.username', read_only=True)
    
    class Meta:
        model = OrderEvent
        fields = ['id', 'old_status', 'new_status', 'initiator_name', 'created_at']
        
class OrderSerializer(serializers.ModelSerializer):
    car_details = CarSerializer(source='car', read_only=True)
    events = OrderEventSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'car', 'car_details', 'client_name', 
            'client_phone', 'status', 'created_at', 'events'
        ]
        
    def validate_status(self, new_status):
        if self.instance is None:
            return new_status
        old_status = self.instance.status
        
        if old_status == 'canceled':
            raise ValidationError("Нельзя изменить статус отмененной заявки.")
        if old_status == 'new' and new_status == 'done':
            raise ValidationError("Нельзя сразу завершить новую заявку, минуя стадию обработки.")
        if old_status == 'done':
            raise ValidationError("Нельзя изменить статус завершенной заявки.")
        return new_status