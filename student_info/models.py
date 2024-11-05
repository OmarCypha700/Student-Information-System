from django.db import models

# Create your models here.

class Student(models.Model):
    # Bio-Data
    student_index = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=10)
    address = models.TextField()

    # School Data
    program = models.CharField(max_length=100)
    admission_year = models.CharField(max_length=9)

    # Gardian Data
    father_name = models.CharField(max_length=100)
    father_contact = models.CharField(max_length=10)
    mother_name = models.CharField(max_length=100)
    mother_contact = models.CharField(max_length=10)

    # Profile Picture
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True,)

    def __str__(self):
        return f"{self.first_name} {self.middle_name} {self.last_name} | {self.student_index}"
    


class Document(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=50)  # e.g. Transcript, Certificate
    document_file = models.FileField(upload_to='documents/')
    upload_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_type} for {self.student}"


class DocumentType (models.Model):
    document_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.document_type}"
    