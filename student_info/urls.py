from django.urls import path
# from .admin import admin_site  # Import your custom admin site instance
from .import views

urlpatterns = [
    # path('myadmin/', admin_site.urls),
    path('', views.dashboard, name='dashboard'),
    path('student_list', views.student_list, name='student_list'),
    path('view/<int:id>', views.view, name='view'),
    path('edit/<int:id>/', views.edit, name='edit'),
    path('filter/', views.filter, name='filter'),
    path('add_student', views.add_student, name='add_student'),
    path('delete/<int:id>', views.delete, name='delete'),
    path('update/<int:id>', views.update, name='update'),
    path('delete_document/<int:id>', views.delete_document, name='delete_document'),
    path('import_students', views.import_students, name='import_students'),
    path('csv_template/', views.download_csv_template, name='csv_template'),
    path('export_students/', views.export_students, name='export_students'),
    path('import_documents/', views.import_documents, name='import_documents'),
    path('document_template/', views.download_document_template, name='document_template'),
    path('import_profile/', views.import_profile, name='import_profile'),
    path('update_profile/<int:id>', views.update_profile, name='update_profile'),
    path('delete_profile/<int:id>', views.delete_profile, name='delete_profile'),
    path('profile_template/', views.download_profile_template, name='profile_template'),

]