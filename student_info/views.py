import csv
import io
import os
from PIL import Image
import zipfile
from django.core.files import File
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from .models import Student, Document, DocumentType, Program, AdmissionYear
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required(login_url='/auth/login')
def student_list(request):
    students = Student.objects.all()[:300]
    programs = Program.objects.all()
    admission_years = AdmissionYear.objects.all()
    document_types = DocumentType.objects.all()

    context = {
        'students':students,
        'programs':programs,
        'admission_years':admission_years,
        'document_types':document_types
    }

    return render(request, 'students/student_list.html', context)


def filter(request):
    # Retrieve the form values from the request (POST or GET)
    program = request.POST.get('program', '')
    admission_year = request.POST.get('admission_year', '')

    # Redirect if neither filter is selected
    if not program and not admission_year:
        return redirect('student_list')  # Replace 'student_list' with the URL name of the student list view

    # Start with all students and filter if a program or admission year is selected
    students = Student.objects.all()
    if program:
        students = students.filter(program=program)
    if admission_year:
        students = students.filter(admission_year=admission_year)

    # Pass the filtered student list along with available filter options
    context = {
        'students': students,
        'programs': Student.objects.values_list('program', flat=True).distinct(),
        'admission_years': Student.objects.values_list('admission_year', flat=True).distinct(),
    }
    return render(request, 'students/student_list.html', context)


def save_documents(request, student):
    document_types = request.POST.getlist('document_types')
    documents = request.FILES.getlist('documents')

    if documents and document_types:
        if len(documents) != len(document_types):
            print("Warning: Number of documents and document types do not match.")
        
        for i in range(min(len(documents), len(document_types))):
            document_type = document_types[i]
            document_file = documents[i]

            # Check if a document of this type already exists for the student
            existing_document = Document.objects.filter(student=student, document_type=document_type).first()

            if existing_document:
                # Update existing document file
                existing_document.document_file = document_file
                existing_document.save()
            else:
                # Create a new document if it doesn't exist
                Document.objects.create(
                    student=student,
                    document_type=document_type,
                    document_file=document_file
                )


def delete_document(request,id):
    document = Document.objects.get(id=id)
    student = document.student.id
    document.delete()
    messages.error(request, 'Document deleted successfully')
    return redirect('view', id=student)


def add_student(request):
    if request.method == 'POST':
        # Extract and save student information
        student_index = request.POST.get('student_index')
        first_name = request.POST.get('first_name')
        middle_name = request.POST.get('middle_name')
        last_name = request.POST.get('last_name')
        date_of_birth = request.POST.get('date_of_birth')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        program = request.POST.get('program')
        admission_year = request.POST.get('admission_year')
        father_name = request.POST.get('father_name')
        father_contact = request.POST.get('father_contact')
        mother_name = request.POST.get('mother_name')
        mother_contact = request.POST.get('mother_contact')

        student = Student.objects.create(
            student_index = student_index,
            first_name = first_name,
            middle_name = middle_name,
            last_name = last_name,
            date_of_birth = date_of_birth,
            email = email,
            phone_number = phone_number,
            address = address,
            program = program,
            admission_year = admission_year,
            father_name = father_name,
            father_contact = father_contact,
            mother_name = mother_name,
            mother_contact = mother_contact,
        )

        # Use helper function to save documents
        save_documents(request, student)
        
        messages.success(request, "Record added successfully")
        return redirect('student_list')

    return render(request, 'student_info/add_student.html')


def edit(request, id):
    student = Student.objects.get(id=id)
    documents = Document.objects.filter(student=student)
    document_types = DocumentType.objects.all()
    programs = Program.objects.all()
    admission_years = AdmissionYear.objects.all()
    context = {
        'student':student,
        'documents':documents,
        'document_types':document_types,
        'programs':programs,
        'admission_years':admission_years,
    }
    
    return render(request,'students/edit.html', context)


def delete(request, id):
    Student.objects.get(id=id).delete()
    messages.error(request, 'Record deleted successfully')
    return redirect('student_list')


def view(request, id):
    student = Student.objects.get(id=id)
    documents = Document.objects.filter(student=student)
    context = {
        'student':student,
        'documents':documents,
    }
    return render(request,'students/view.html', context)

def update(request, id):
    if request.method == 'POST':
        student_index = request.POST.get('student_index')
        first_name = request.POST.get('first_name')
        middle_name = request.POST.get('middle_name')
        last_name = request.POST.get('last_name')
        date_of_birth = request.POST.get('date_of_birth')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        program = request.POST.get('program')
        admission_year = request.POST.get('admission_year')
        father_name = request.POST.get('father_name')
        father_contact = request.POST.get('father_contact')
        mother_name = request.POST.get('mother_name')
        mother_contact = request.POST.get('mother_contact')
        
        # Get the student instance instead of a QuerySet
        student = Student.objects.get(id=id)
        # Update the student fields and save
        student.student_index = student_index
        student.first_name = first_name
        student.middle_name = middle_name
        student.last_name = last_name
        student.date_of_birth = date_of_birth
        student.email = email
        student.phone_number = phone_number
        student.address = address
        student.program = program
        student.admission_year = admission_year
        student.father_name = father_name
        student.father_contact = father_contact
        student.mother_name = mother_name
        student.mother_contact = mother_contact
        student.save()

        # Save the documents
        save_documents(request, student)

        messages.success(request, 'Record updated successfully')
        return redirect('edit', id=student.id)
    else:
        student = Student.objects.get(id=id)
        context = {
            'student': student
        }
    return render(request, 'students/edit.html', context)


def download_csv_template(request):
    # Define CSV headers based on expected fields
    headers = [
        'student_index', 'first_name', 'middle_name', 'last_name',
        'date_of_birth', 'email', 'phone_number', 'address',
        'program', 'admission_year', 'father_name', 'father_contact',
        'mother_name', 'mother_contact'
    ]
    
    # Create an in-memory file to store the CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    
    # Optionally, write example rows (empty in this case)
    writer.writerow({
        'student_index': '', 'first_name': '', 'middle_name': '', 'last_name': '',
        'date_of_birth': '', 'email': '', 'phone_number': '', 'address': '',
        'program': '', 'admission_year': '', 'father_name': '', 'father_contact': '',
        'mother_name': '', 'mother_contact': ''
    })
    
    # Prepare response
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_import_template.csv"'
    return response


def import_students(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('file')
        if not csv_file.name.endswith('.csv'):
            return render(request, 'import.html', {'error': 'Only CSV files are allowed.'})

        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        errors = []
        success_count = 0

        for row in reader:
            try:
                # Retrieve required fields, provide default values for optional fields
                student_index = row.get('student_index')
                if not student_index:
                    errors.append("Missing 'student_index' in row.")
                    continue  # Skip rows without student_index

                first_name = row.get('first_name', '')
                last_name = row.get('last_name', '')
                middle_name = row.get('middle_name', '')  # Defaults to empty string if missing
                date_of_birth = row.get('date_of_birth', None)
                email = row.get('email', '')
                phone_number = row.get('phone_number', '')
                address = row.get('address', '')
                program = row.get('program', '')
                admission_year = row.get('admission_year', '')
                father_name = row.get('father_name', '')
                father_contact = row.get('father_contact', '')
                mother_name = row.get('mother_name', '')
                mother_contact = row.get('mother_contact', '')

                # Create or update the Student record
                student, created = Student.objects.update_or_create(
                    student_index=student_index,
                    defaults={
                        'first_name': first_name,
                        'middle_name': middle_name,
                        'last_name': last_name,
                        'date_of_birth': date_of_birth,
                        'email': email,
                        'phone_number': phone_number,
                        'address': address,
                        'program': program,
                        'admission_year': admission_year,
                        'father_name': father_name,
                        'father_contact': father_contact,
                        'mother_name': mother_name,
                        'mother_contact': mother_contact
                    }
                )
                success_count += 1

            except KeyError as e:
                messages.error(request, f"Missing key in CSV: {str(e)}")
                # errors.append(f"Missing key in CSV: {str(e)}")

        messages.success(request, f'{success_count} student(s) imported successfully.')
        return redirect('student_list')

    return render(request, 'students/student_list.html')



def export_students(request):
    if request.method == 'POST':
        # Retrieve export options
        export_csv = 'export_csv' in request.POST
        export_documents = 'export_documents' in request.POST

        # Retrieve filters from the form
        program = request.POST.get('program')
        admission_year = request.POST.get('admission_year')

        # Filter students based on selected program and admission year
        students = Student.objects.all()
        if program:
            students = students.filter(program=program)
        if admission_year:
            students = students.filter(admission_year=admission_year)

        # Initialize an in-memory bytes buffer for file creation
        response = HttpResponse(content_type='application/zip')
        zip_buffer = io.BytesIO()
        
        # Prepare to write to zip archive if documents are selected
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:

            # Step 1: Export Student Information in CSV if selected
            if export_csv:
                csv_buffer = io.StringIO()
                csv_writer = csv.writer(csv_buffer)
                csv_writer.writerow(['student_index', 'first_name', 'middle_name', 'last_name', 
                                     'date_of_birth', 'email', 'phone_number', 'address', 'program',
                                     'admission_year', 'father_name', 'father_contact', 'mother_name',
                                     'mother_contact'])
                
                # Write student information to CSV
                for student in students:
                    csv_writer.writerow([
                        student.student_index, student.first_name, student.middle_name,
                        student.last_name, student.date_of_birth, student.email,
                        student.phone_number, student.address, student.program,
                        student.admission_year, student.father_name, student.father_contact,
                        student.mother_name, student.mother_contact
                    ])

                # Add CSV file to the zip archive
                zip_file.writestr('student_information.csv', csv_buffer.getvalue())
                csv_buffer.close()

            # Step 2: Export Student Documents if selected
            if export_documents:
                for student in students:
                    documents = Document.objects.filter(student=student)
                    for document in documents:
                        document_path = document.document_file.path
                        try:
                            # Open the image and convert it to PDF
                            with Image.open(document_path) as img:
                                img = img.convert('RGB')  # Ensure the image is in RGB mode
                                pdf_buffer = io.BytesIO()
                                img.save(pdf_buffer, format="PDF")

                                # Define PDF filename in zip as "<student_index>/<document_type>.pdf"
                                pdf_filename = f"{student.student_index}/{document.document_type}.pdf"
                                zip_file.writestr(pdf_filename, pdf_buffer.getvalue())
                                pdf_buffer.close()

                        except Exception as e:
                            # Handle any errors in conversion, possibly logging for debugging
                            print(f"Error converting {document_path} to PDF: {e}")

        # Return the zip file as a response
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="students_export.zip"'
        return response

    # Render the form with available programs and admission years for filtering
    # programs = Student.objects.values_list('program', flat=True).distinct()
    # admission_years = Student.objects.values_list('admission_year', flat=True).distinct()
    return redirect('student_list')