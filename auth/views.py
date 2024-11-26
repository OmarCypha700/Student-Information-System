import os
from django.core.mail import EmailMessage
from django.contrib.auth.models import Permission
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, smart_str, force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from django.urls import reverse
from validate_email import validate_email
import threading

# User = get_user_model()

# Create your views here.
class EmailThread(threading.Thread):
    def __init__(self, email_msg):
        self.email = email_msg
        threading.Thread.__init__(self)

    def run(self):
        self.email.send(fail_silently=False)

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        # email = request.POST['email']
        password = request.POST['password']
        if username and password:
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # messages.success(request, 'You have succesfully logged in' )
                return redirect('dashboard')
            messages.error(request, 'Invalid credentials,try again')
            return render(request, 'auth/login.html')
        return render(request, 'auth/login.html')
    return render(request, 'auth/login.html')


def logout_user(request):
    logout(request)
    return render(request, 'auth/login.html')

def register_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email'] 
        password = request.POST['password']
        # first_name = request.POST['first_name']
        # last_name = request.POST['last_name']

        context = {
            'fiedlValue': request.POST,
        }

        if not User.objects.filter(username=username).exists():
            if not User.objects.filter(email=email).exists():
                if len(password) < 6:
                    messages.error(request, 'Password too short, password must be more than 6 characters')
                    return render(request, 'auth/register.html', context)
                user = User.objects.create_user(username=username, 
                                                email=email, 
                                                password=password, 
                                                # first_name=first_name, 
                                                # last_name=last_name,
                                                )
                user.set_password(password)
                # perm = Permission.objects.get(name=['Can add report'])
                # user.user_permissions.add(perm)
                user.is_active = False
                user.save()
                messages.success(request, 'User registered successfully')
                return render(request, 'auth/register.html')
        messages.error(request, 'User alredy exists')
        return render(request, 'auth/register.html')
    else:   
        return render(request, 'auth/register.html')

def reset_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        context = {
            'fiedlValue': request.POST
        }
        if not validate_email(email):
            messages.error(request, 'Please provide a valid email')
            return render(request, 'auth/reset-password.html',context)
        current_site = get_current_site(request)
        user = User.objects.filter(email=email)
        
        if user.exists():
            user = User.objects.get(email=email)
            domain = current_site.domain
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)  
            link = reverse('set-new-password', kwargs={'uidb64':uid, 'token':token})
            reset_url = 'http://'+domain+link
            subject = 'Reset Password'
            body = f"Dear user, kindly follow this link to reset your password\n {reset_url}\n"
            sender = os.environ.get('EMAIL_HOST_USER') #'omarcypha@gmial.com'
            email_msg = EmailMessage(
                subject,  
                body,
                sender,
                [email])
            EmailThread(email_msg).start()
            messages.success(request, 'An email has been sent with a link to reset your password')
            return render(request, 'auth/reset-password.html')
        
        messages.error(request, 'User does no exist')
        return render(request, 'auth/reset-password.html')
    else:
        return render(request, 'auth/reset-password.html')

def confirm_reset(request,uidb64, token):
    if request.method == 'POST':
        context ={
            'uidb64': uidb64,
            'token': token
        }
        password = request.POST['password']
        password2 = request.POST['password2']
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'auth/set-newpassword.html', context)
        try:
            uid = force_bytes(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            messages.info(request, 'Something went wrong, please try again')
            return render(request, 'auth/set-newpassword.html', context)
        user.set_password(password)
        user.save()
        messages.success(request, 'Password reset successful. You can now login with your new password.')
        return HttpResponseRedirect(reverse('login'))
    else:
        context ={
                'uidb64': uidb64,
                'token': token
            }
        try:
            uid = force_bytes(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if not PasswordResetTokenGenerator().check_token(user, token):
                messages.info(request, 'Password reset link is invalid or expired, kiundly request for a new link')
                return render(request, 'auth/reset-password.html')
        except Exception:
            pass  
        return render(request, 'auth/set-newpassword.html', context)
    


def users(request):
    users = User.objects.exclude(username__in =['admin'])
    context = {
        'users': users
    }
    return render(request, 'auth/users.html', context)

def activate_user(request, id):
    user = User.objects.get(id=id)
    user.is_active = True
    user.save()
    users = User.objects.exclude(username__in =['admin'])
    context = {
        'users': users
    }
    return render(request, 'auth/users.html', context)    

def deactivate_user(request, id):
    user = User.objects.get(id=id)
    user.is_active = False
    user.save()
    users = User.objects.exclude(username__in =['admin'])
    context = {
        'users': users
    }
    return render(request, 'auth/users.html', context)