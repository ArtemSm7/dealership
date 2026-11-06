from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'brands', views.BrandViewSet)
router.register(r'cars', views.CarViewSet)
router.register(r'orders', views.OrderViewSet)

urlpatterns = [
    # Основные страницы
    path('', views.catalog_view, name='catalog'),
    path('car/<int:car_id>/', views.car_detail_view, name='car_detail'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('favorites/', views.favorites_view, name='favorites'),
    path('control-center/', views.control_center_view, name='control_center'),
    
    # Авторизация
    path('login/', LoginView.as_view(template_name='main/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='catalog'), name='logout'),
    
    # REST API
    path('api/', include(router.urls)),
]