import csv
import io
import os
import json
from datetime import datetime
from django.urls import reverse
import pandas as pd
import zipfile
# from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from .models import Student, Document, DocumentType
from django.db.models import Count
from django.contrib.auth.decorators import login_required


############################
# DASHBOARD VIEW
#############################

@login_required(login_url='/auth/login')
def dashboard(request):
    """
    This view is responsible for all data in the dashboard page
    It gets the total number of students and other aggregated data 
    used in rendering the visualizations using Chart JS
    """

    # Get total number of students
    total_students = Student.objects.count()
    # Get total degree students
    degree_students = Student.objects.filter(program__startswith='Bsc').count()
    # Get total diploma students
    diploma_students = Student.objects.filter(program__startswith='Dip').count()
    # Get total Nursing students
    rgn = Student.objects.filter(program__icontains='Registered General Nurse').count()
    rm = Student.objects.filter(program__icontains='Registered Midwifery').count()
    ph = Student.objects.filter(program__icontains='Public Health Nursing').count()

    # Calculate the admission years for the last five years
    current_year = datetime.now().year
    past_five_years = [f"{year}/{year+1}" for year in range(current_year - 5, current_year + 1)]
    # Get unique programs
    programs = Student.objects.values_list('program', flat=True).distinct()
    
    
    # Prepare data for each program
    program_data = {}
    for program in programs:
        enrollment_data = (
            Student.objects.filter(program=program, admission_year__in=past_five_years)
            .values('admission_year')
            .annotate(student_count=Count('id'))
        )
        
        program_data[program] = {
            'labels': json.dumps([entry['admission_year'] for entry in enrollment_data]),
            'data': json.dumps([entry['student_count'] for entry in enrollment_data])
        }

    context = {
        'program_data': program_data,
        'total_students': total_students,
        'degree_students': degree_students,
        'diploma_students': diploma_students,
        'rgn': rgn,
        'rm': rm,
        'ph': ph,
    }

    return render(request, 'students/dashboard.html', context)

###########################
# BASIC CRUD FUNCTIONALITY
###########################
@login_required(login_url='/auth/login')
def student_list(request):
    """
    This GETs all the students in the database but restricted to a fixed number to ensure optimized performance
    It also gets all the programs and admission_years populated in the database to populate the filtering dropdowns
    If the program or admission year is not in the database it will not be available in the filtering dropdowns
    """

    students = Student.objects.all()[:300]
    document_types = DocumentType.objects.all()

    context = {
        'students':students,
        'programs': Student.objects.values_list('program', flat=True).distinct(),
        'admission_years': Student.objects.values_list('admission_year', flat=True).distinct(),
        'document_types':document_types
    }

    return render(request, 'students/student_list.html', context)


def filter(request):
    """
    This is the function invoked if the filter button is clicked
    It filters the database based on what is selected in the dropdowns and populates it in a table
    """

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

    """
    This is the helper fucntion responsible for saving a document when a student is manually added
    It is used within the add_student function 
    """

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


def add_student(request):

    """
    This is the function responsible for adding a student to the database manually or using the form
    It uses the helper fuction save_documents() to save documents added in the form 
    """

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


# def update_profile(request, id):



def delete_document(request,id):

    """
    This deletes a specific document from the database
    This is helpfull if you identify a minor issue with the uploaded document, you don't need to add the whole document again
    """

    document = Document.objects.get(id=id)
    student = document.student.id
    document.delete()
    messages.error(request, 'Document deleted successfully')
    return redirect('view', id=student)


def edit(request, id):

    """
    Responsible for the edit page where a specific student's details are available for editing
    """

    student = Student.objects.get(id=id)
    documents = Document.objects.filter(student=student)
    document_types = DocumentType.objects.all()

    context = {
        'student':student,
        'documents':documents,
        'document_types':document_types,
        'programs': Student.objects.values_list('program', flat=True).distinct(),
        'admission_years': Student.objects.values_list('admission_year', flat=True).distinct(),
    }
    
    return render(request,'students/edit.html', context)


def delete(request, id):

    """
    Responsible for deleting an individual student record
    """

    Student.objects.get(id=id).delete()
    messages.error(request, 'Record deleted successfully')
    return redirect('student_list')


def view(request, id):

    """
    Responsible for the view page where a specific student's details are available for viewing only
    """

    student = Student.objects.get(id=id)
    documents = Document.objects.filter(student=student)
    context = {
        'student':student,
        'documents':documents,
    }
    return render(request,'students/view.html', context)

def update(request, id):

    """
    This function update the database with the chages made in the edit view

    Returns:
    It redirects to the edit page
    """

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

    """
    Provides a csv template for uploading student's BIODATA into the database

    Returns:
    Downloads a csv file with fields to guide users on how to populate the csv file
    """

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

    """
    Reads an uploaded csv file containing all the student details and populates the database with it
    
    """
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

    """
    Downloads students record into a csv file depending on the filtering options selected

    The funtion also downloads all documents for each student in the database and stores them in a folder

    The folder is named with the student's Index number and the documents are also named with the student's index and document type
    """

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
                            # Define PDF filename in zip as "<student_index>/<document_type>.pdf"
                            pdf_filename = f"{student.student_index}_{document.document_type}.pdf"
                            
                            # Add the PDF file directly to the zip
                            with open(document_path, 'rb') as pdf_file:
                                zip_file.writestr(pdf_filename, pdf_file.read())

                        except Exception as e:
                            # Handle any errors in accessing the PDF, possibly logging for debugging
                            print(f"Error adding {document_path} to ZIP: {e}")

        # Move the buffer position to the start
        zip_buffer.seek(0)

        # Return the zip file as a response
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="students_export.zip"'
        return response

    # Render the form with available programs and admission years for filtering
    return redirect('student_list')



def import_documents(request):

    """
    Reads an uploaded csv file and and imports its data into the database

    It takes in a csv containing the document metadata and the documents (multiple selection from the windows dialog) 
    This function compares the name in the csv file with the name of the file uploaded 
    and locates the Student_Index in the csv file with the one in the database and uploads the document for that file

    """

    if request.method == 'POST':
        # Retrieve the uploaded CSV and document files
        csv_file = request.FILES.get('csv_file')
        documents = request.FILES.getlist('documents')
        
        # Check if the uploaded file is a CSV
        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file.')
            return redirect('student_list')

        # Read the CSV file into a DataFrame
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            messages.error(request, f'Error reading CSV file: {e}')
            return redirect('student_list')
        
        # Prepare document mapping for quick lookup
        document_map = {doc.name: doc for doc in documents}
        
        for index, row in df.iterrows():
            student_index = row['student_index']
            document_type = row['document_type']
            document_name = row['document_name']  # The document's filename from the CSV

            # Check if the document file was uploaded
            if document_name in document_map:
                try:
                    student = Student.objects.get(student_index=student_index)
                    uploaded_file = document_map[document_name]
                    
                    # Look for an existing document of the same type
                    document, created = Document.objects.update_or_create(
                        student=student,
                        document_type=document_type,
                        defaults={'document_file': uploaded_file}  # This will update the file
                    )
                    
                    # If the document already existed, handle file overwrite
                    if not created:
                        # Delete the old file if it exists
                        if document.document_file:
                            old_file_path = document.document_file.path
                            if os.path.exists(old_file_path):
                                os.remove(old_file_path)  # Remove the old file

                        # Now save the new file (this may be redundant due to update_or_create, but it ensures the new file is saved)
                        document.document_file.save(uploaded_file.name, uploaded_file)

                    messages.success(request, f'Successfully {"uploaded new" if created else "replaced"} document for student ID {student_index} ({document_type})')
                    
                except Student.DoesNotExist:
                    messages.error(request, f'Student with ID {student_index} does not exist.')
            else:
                messages.error(request, f'Document {document_name} not found in uploaded files.')

        return redirect('student_list')

    return render(request, 'students/student_list.html')



def download_document_template(request):

    """
    Provides a csv template for uploading student's documents into the database

    Returns:
    Downloads a csv file with sample data to guide users on how to populate the csv file
    """

    # Define the filename
    filename = "document_upload_template.csv"
    
    # Create the HTTP response with the appropriate CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header row
    writer.writerow(['student_index', 'document_type', 'document_name'])
    
    # Optionally, you can add some example data rows to guide users
    writer.writerow(['NMCASMRM200001', 'Transcript', 'NMCASMRM200001_Transcript.pdf'])
    writer.writerow(['NMCASMRM200002', 'Certificate', 'NMCASMRM200002_Certificate.pdf'])

    return response


def update_profile(request, id):

    """
    Updates only the profile picture of a student.

    Returns:
        Redirects to the student's edit page after deletion.
    """

    student = Student.objects.get(id=id)

    if request.method == 'POST':
        profile = request.FILES.get('profile')

        if not profile:
            return render(request, 'students/edit.html', {
                'student': student,
                # 'error': 'No profile picture uploaded.',
            })

        if student.profile_picture:
            old_file_path = student.profile_picture.path
            if os.path.exists(old_file_path):
                os.remove(old_file_path)  # Remove the old profile picture

        student.profile_picture = profile
        student.save()

        return redirect (reverse('edit', args=[student.id]))
    return render(request, 'students/edit.html', {'student': student})


def delete_profile(request, id):
    
    """
    Deletes only the profile picture of a student.

    Returns:
        Redirects to the student's edit page after deletion.
    """
    student = Student.objects.get(id=id)
    if student.profile_picture:
        # Remove the profile picture file from the file system
        old_file_path = student.profile_picture.path
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

        # Clear the profile picture field in the database
        student.profile_picture = None
        student.save()

    # Redirect to the student's edit page
    return redirect(reverse('edit', args=[student.id]))



def import_profile(request):
    if request.method == 'POST':
        # Retrieve the uploaded CSV and document files
        csv_file = request.FILES.get('csv_file')
        documents = request.FILES.getlist('documents')
        
        # Check if the uploaded file is a CSV
        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file containing metadata.')
            return redirect('student_list')

        # Read the CSV file into a DataFrame
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            messages.error(request, f'Error reading CSV file: {e}')
            return redirect('student_list')
        
        # Prepare document mapping for quick lookup
        document_map = {doc.name: doc for doc in documents}
        
        for index, row in df.iterrows():
            student_index = row['student_index']
            document_name = row['document_name']  # The profile picture's filename from the CSV

            # Check if the document file was uploaded
            if document_name in document_map:
                try:
                    student = Student.objects.get(student_index=student_index)
                    uploaded_file = document_map[document_name]
                    
                    # Handle file overwrite by deleting the old profile picture if it exists
                    if student.profile_picture:
                        old_file_path = student.profile_picture.path
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)  # Remove the old profile picture

                    # Save the new profile picture
                    student.profile_picture.save(uploaded_file.name, uploaded_file)
                    student.save()

                    messages.success(request, f'Successfully uploaded/updated profile picture for student ID {student_index}')
                    
                except Student.DoesNotExist:
                    messages.error(request, f'Student with ID {student_index} does not exist.')
            else:
                messages.error(request, f'Profile picture {document_name} not found in uploaded files.')

        return redirect('student_list')

    return render(request, 'students/student_list.html')


def download_profile_template(request):
    # Define the filename
    filename = "profile_upload_template.csv"
    
    # Create the HTTP response with the appropriate CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header row
    writer.writerow(['student_index', 'document_name'])
    
    # Optionally, you can add some example data rows to guide users
    writer.writerow(['NMCASMRM200001','NMCASMRM200001_Transcript.webp'])
    writer.writerow(['NMCASMRM200002','NMCASMRM200002_Certificate.webp'])

    return response