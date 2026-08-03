"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path, include

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # OBS: os routers de auction/products já registram seus próprios
    # prefixos ('auctions', 'bids', 'products'), então aqui usamos só
    # 'api/v1/' — senão a URL final duplica (ex: /api/v1/products/products/)
    # e o front, ao chamar /api/v1/products/, recebe o api-root do DRF
    # em vez da lista real de produtos.
    path('api/v1/', include('auction.urls')),
    path('api/v1/', include('products.urls')),
    
    path('api/v1/users/', include('user.urls')),
    path('api/v1/details/', include('fifa_data.urls')),

    path('api/v1/team/', include('team.urls')),
    path('api/v1/payments/', include('payment.urls')),
    path('api/v1/', include('campaigns.urls')),
    path('api/v1/', include('competitions.urls')),
    path('api/v1/', include('social.urls')),

    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
