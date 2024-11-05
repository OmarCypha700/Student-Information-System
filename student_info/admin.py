from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from .models import Student, Document, DocumentType

# Custom Admin Site
class MyAdminSite(AdminSite):
    site_header = "ASSINMAN NMTC STUDENT INFORMATION SYSTEM"
    site_title = "Admin Portal"
    index_title = "Welcome to Assinman NMTC Student Information System"

admin_site = MyAdminSite(name='admin')

# Register models with the custom admin site
@admin.register(Student, site=admin_site)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_index', 'name', 'admission_year', 'program', 'phone_number')  # Use 'name' instead of separate name fields
    list_filter = ('program', 'admission_year')
    search_fields = ('student_index', 'first_name', 'middle_name', 'last_name')

    def name(self, obj):
        # Combine first_name, middle_name, and last_name into one field
        return f"{obj.first_name} {obj.middle_name} {obj.last_name}".strip()

    # Customize the column header for 'name'
    name.short_description = 'Full Name'


# Register other models with the custom admin site
admin_site.register(Document)
admin_site.register(DocumentType)

# Register Django's User and Group models with the custom admin site
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)