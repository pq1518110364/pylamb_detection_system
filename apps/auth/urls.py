from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestView

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),

    path('sso/test/', TestView.as_view(), name='测试接口'),
]
