from django.contrib import admin
from .models import Student, Document, DocumentType, Program, AdmissionYear


# Register your models here.
admin.site.register(Student)
admin.site.register(Document)
admin.site.register(DocumentType)
admin.site.register(Program)
admin.site.register(AdmissionYear)