from django.urls import path
from .import views

urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('request-reset-link', views.reset_password, name='reset_password'),
    path('set-new-password/<uidb64>/<token>', views.confirm_reset, name='set-new-password'),
    path('users', views.users, name='users'),
    path('activate/<id>', views.activate_user, name='activate'),
    path('deactivate/<id>', views.deactivate_user, name='deactivate')
]