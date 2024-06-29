"""
URL configuration for lamb_detection_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include  # 1.导入re_path(正则表达式) 2.include(为了引入其它urls)

urlpatterns = [
    path('admin/', admin.site.urls),

  # r表示里面写的正则表达式  ^表示匹配任意 表示字符串不转义，这样在正则表达式中使用 \ 只写一个就可以
    # 为每个路径改命名空间，逻辑隔离 方便后续管理
    path('auth/', include(("apps.auth.urls", '权限接口')), name="权限接口")
]

