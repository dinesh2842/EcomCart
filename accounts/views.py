from django.shortcuts import render,redirect,HttpResponse,get_object_or_404
from .forms import *
from .models import Account
from django.contrib import messages,auth
from django.contrib.auth import authenticate,login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from carts.views import _cart_id
from carts.models import Cart,CartItem
import requests
from orders.models import *

# def register(request):
#     context = {}  # Define context with a default empty dictionary
#     if request.method == 'POST':
#         form = RegistrationForm(request.POST)
#         if form.is_valid():
#             first_name = form.cleaned_data['first_name']
#             last_name = form.cleaned_data['last_name']
#             phone_number = form.cleaned_data['phone_number']
#             email = form.cleaned_data['email']
#             password = form.cleaned_data['password']
#             username = email.split("@")[0]

#             user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
#             user.phone_number = phone_number
#             user.save()
#         else:
#             form = RegistrationForm()
#     else:
#         form = RegistrationForm()
#     context['form'] = form  # Assign form to context
#     return render(request, 'accounts/register.html', context)



# def register(request):
#     context = {}
#     if request.method == 'POST':
#         form = RegistrationForm(request.POST)
#         if form.is_valid():
#             first_name = form.cleaned_data['first_name']
#             last_name = form.cleaned_data['last_name']
#             phone_number = form.cleaned_data['phone_number']
#             email = form.cleaned_data['email']
#             password = form.cleaned_data['password']
#             username = email.split("@")[0]

#             user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
#             user.phone_number = phone_number
#             user.save()
#         else:
#             # If the form is invalid, include the form with errors in the context
#             context['form'] = form
#     else:
#         # If it's a GET request, create an empty form
#         form = RegistrationForm()
#         context['form'] = form

#     return render(request, 'accounts/register.html', context)

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]

            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()

            #create user profile

            profile = UserProfile()
            profile.user_id = user.id #the id here comes from the user in line 80
            profile.profile_picture = 'default/default-user.png'
            profile.save()

            #User activation
            current_site=get_current_site(request)
            mail_subject='Please activate your account'
            message=render_to_string('accounts/account_verification_email.html',{
               'user':user,
               'domain':current_site,
               'uid':urlsafe_base64_encode(force_bytes(user.pk)),
               'token':default_token_generator.make_token(user)
            })
            to_email=email
            send_email=EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()
            #messages.success(request,"Thank you regsitering with us , we have sent you an verification email to your email address , please verify")
            return redirect('/accounts/login/?command=verification&email='+email)  # Redirect to login page after successful registration
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})
def login(request):
   if request.method=='POST':
     email=request.POST['email']
     password=request.POST['password']

     user=auth.authenticate(email=email,password=password)

     if user is not None:
        try:
           
           
           cart=Cart.objects.get(cart_id=_cart_id(request))
           is_cart_item_exists=CartItem.objects.filter(cart=cart).exists()
           if is_cart_item_exists:
              cart_item=CartItem.objects.filter(cart=cart)
              #getting the product variation
              product_variation=[]
              for item in cart_item:   
                 variation = item.variations.all()
                 product_variation.append(list(variation))
              #get the cart items to access from the user to access his product variation
              cart_item = CartItem.objects.filter(user=user)
            
              ex_var_list = []
              id = []
              for item in cart_item:
                  existing_variation = item.variations.all()
                  ex_var_list.append(list(existing_variation))
                  id.append(item.id)
            #   product_variation=[1,2,3,4,5]
            #   ex_var_list=[4,6,3,5]
              for pr in product_variation:
                 if pr in ex_var_list:
                    index=ex_var_list.index(pr)
                    item_id=id[index]
                    item=CartItem.objects.get(id=item_id)
                    item.quantity+=1
                    item.user=user
                    item.save()
                 else:
                    cart_item=CartItem.objects.filter(cart=cart)
                    
                    for item in cart_item:
                        item.user=user
                        item.save()

        except:
           
           pass
        auth.login(request,user)
        messages.success(request,'You are now Logged in ')
        url=request.META.get('HTTP_REFERER')
        try:
           query=requests.utils.urlparse(url).query
          
           #next=/cart/checkout/
           params=dict(x.split('=') for x in query.split('&'))
           if 'next' in params:
              nextPage = params['next']
              return redirect(nextPage)
           
        except:
           return redirect('home')
     else:
        messages.error(request,"invalid login credentials")
        print("Authentication failed for email:", email)
        return redirect('login')
   return render(request,'accounts/login.html')

@login_required(login_url='login')
def logout(request):
   auth.logout(request)
   messages.success(request,'you are logged out')
   return redirect('login')


def activate(request,uidb64,token):
   try:
      uid=urlsafe_base64_decode(uidb64).decode()
      user=Account._default_manager.get(pk=uid)
   except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
      user=None

   if user is not None and default_token_generator.check_token(user,token):
      user.is_active=True
      user.save()
      messages.success(request,'congratulations!your account is activated')
      return redirect('login')
   else:
      messages.error(request,'invalid activation link')
      return redirect('register')



@login_required(login_url='login')
def dashboard(request):
   orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id,is_ordered=True)
   orders_count = orders.count()
   userprofile = UserProfile.objects.get(user_id=request.user.id)
   context={
      'orders_count':orders_count,
      'userprofile':userprofile,
   }
   return render(request,'accounts/dashboard.html',context)

def forgotpassword(request):
   if request.method=='POST':
      email = request.POST['email']
      if Account.objects.filter(email=email).exists():
         user=Account.objects.get(email__exact=email)#exact is case sensitive and to get the exact email 


         #Reset password email
         current_site=get_current_site(request)
         mail_subject='Please reset your password'
         message=render_to_string('accounts/reset_password_email.html',{
               'user':user,
               'domain':current_site,
               'uid':urlsafe_base64_encode(force_bytes(user.pk)),
               'token':default_token_generator.make_token(user)
            })
         to_email=email
         send_email=EmailMessage(mail_subject,message,to=[to_email])
         send_email.send()
         messages.success(request,'Password reset email has been sent to your email address')
         return redirect('login')
      else:
         messages.error(request,'Account does not exist')
         return redirect('forgotpassword')
   return render(request,'accounts/forgotpassword.html')


def resetpassword_validate(request,uidb64,token):
   try:
      uid=urlsafe_base64_decode(uidb64).decode()
      user=Account._default_manager.get(pk=uid)
   except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
      user=None
   if user is not None and default_token_generator.check_token(user,token):
      request.session['uid']=uid
      messages.success(request,'Please Reset your password')
      return redirect('resetpassword')
   else:
      messages.error(request,'This link has been expired')
      return redirect('login')
   
def resetpassword(request):
   if request.method == 'POST':
      password=request.POST['password']
      confirm_password=request.POST['confirm_password']

      if password == confirm_password:
         uid=request.session.get('uid')
         user=Account.objects.get(pk=uid)
         user.set_password(password) #set_password is built in function in django actually it will take the password and hash it
         user.save()
         messages.success(request,'password reset successfull')
         return redirect('login')

      else:
         messages.error(request,'password does not match')
         return redirect('resetpassword')

   else:
      
      return render(request,'accounts/resetpassword.html')  
   
@login_required(login_url='login')
def my_orders(request):
   orders = Order.objects.filter(user=request.user,is_ordered=True).order_by('-created_at')
   context = {
      'orders': orders,

   }
   return render(request,'accounts/my_orders.html',context)


@login_required(login_url='login')
def edit_profile(request):
   userprofile = get_object_or_404(UserProfile,user=request.user)#there is no instance for the user that is why we are creating this userprofile object
   if request.method == 'POST':
      user_form = UserForm(request.POST,instance=request.user)#using instance we need to update the profile not to create new one
      profile_form = UserProfileForm(request.POST,request.FILES,instance=userprofile)#request.files this is for uploading a file photo is there in our model
      if user_form.is_valid() and profile_form.is_valid():
         user_form.save()
         profile_form.save()
         messages.success(request,'your profile has been updated')
         return redirect('edit_profile')
   else:
      user_form = UserForm(instance=request.user)
      profile_form = UserProfileForm(instance=userprofile)
   context={
      'user_form':user_form,
      'profile_form':profile_form,
      'userprofile':userprofile,

   }
   return render(request,'accounts/edit_profile.html',context)

@login_required(login_url='login')
def change_password(request):
   if request.method == 'POST':
      current_password = request.POST['current_password']
      new_password = request.POST['new_password']
      confirm_password = request.POST['confirm_password']

      user = Account.objects.get(username__exact=request.user.username)

      if new_password == confirm_password :
         success = user.check_password(current_password)
         if success:
            user.set_password(new_password)
            user.save()
            # auth.logout(request) #this will set the password and logout 
            messages.success(request,'password updated successfully')
            return redirect('change_password')
      
         else:
            messages.error(request,'please enter the current valid password')
            return redirect('change_password')
      else:
         messages.error(request,'password does not match')
         return redirect('change_password')



   return render(request,'accounts/change_password.html')

@login_required(login_url='login')
def order_detail(request,order_id):
   order_detail = OrderProduct.objects.filter(order__order_number=order_id)
   order = Order.objects.get(order_number=order_id)
   sub_total = 0
   for i in order_detail:
      sub_total +=i.product_price * i.quantity

   context ={
      'order_detail':order_detail,
      'order':order,
      'sub_total':sub_total,


   }
   return render(request,'orders/order_detail.html',context)

