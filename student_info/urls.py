from django.urls import path
from .import views

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('view/<int:id>', views.view, name='view'),
    path('edit/<int:id>/', views.edit, name='edit'),
    path('filter/', views.filter, name='filter'),
    path('add_student', views.add_student, name='add_student'),
    path('delete/<int:id>', views.delete, name='delete'),
    path('update/<int:id>', views.update, name='update'),
    path('delete_document/<int:id>', views.delete_document, name='delete_document'),
    path('import_students', views.import_students, name='import_students'),
    path('download_template/', views.download_csv_template, name='download_template'),
    path('export_students', views.export_students, name='export_students'),
]