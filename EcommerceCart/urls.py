
from EcommerceCart import views
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    
    path('securelogin/', admin.site.urls),
    path('',views.home,name='home'),
    path('store/',include('store.urls')),
    path('cart/',include('carts.urls')),
    path('accounts/',include('accounts.urls')),
    path('orders/',include('orders.urls')),

]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
