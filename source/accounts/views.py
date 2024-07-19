from django.contrib import messages
from django.contrib.auth import login, authenticate, REDIRECT_FIELD_NAME
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LogoutView as BaseLogoutView, PasswordChangeView as BasePasswordChangeView,
    PasswordResetDoneView as BasePasswordResetDoneView, PasswordResetConfirmView as BasePasswordResetConfirmView,
)
from django.views.generic.base import TemplateView
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme as is_safe_url
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import View, FormView
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponseNotAllowed


from .utils import (
    send_activation_email, send_reset_password_email, send_forgotten_username_email, send_activation_change_email,
)
from .forms import (
    SignInViaUsernameForm, SignInViaEmailForm, SignInViaEmailOrUsernameForm, SignUpForm,
    RestorePasswordForm, RestorePasswordViaEmailOrUsernameForm, RemindUsernameForm,
    ResendActivationCodeForm, ResendActivationCodeViaEmailForm, ChangeProfileForm, ChangeEmailForm,
)
from .models import (Activation,Patient, SurveyModel)

from rest_framework.decorators import api_view

from django.http import JsonResponse, HttpResponseNotFound, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import base64
from django.core.files.base import ContentFile
import datetime
import pytz
import json

from .models import ImageModel
from django.shortcuts import get_object_or_404,get_list_or_404
from .serializers import PatientSerializer


@csrf_exempt
def addPatient(request):
    if request.method == 'POST':
        try:
            data = request.POST
            name = data.get('name')
            age = data.get('age')
            emergencyContact = data.get('emergencyContact')
            caretakerId = data.get('caretakerId')
            pincode = data.get('pincode')
            
            patient = Patient.objects.create(
                name=name,
                age = age,
                emergencyContact =emergencyContact,
                caretakerId= caretakerId,
                pincode=pincode )
            
            return JsonResponse({'message': 'data saved successfully'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
        
@csrf_exempt
def upload_image(request):
    if request.method == 'POST':
        # Assuming the data is sent as JSON from React
        patient_id = request.POST.get('patientId')
        image_file = request.FILES.get('image')

        # Create and save the ImageModel instance
        image_instance = ImageModel(patientId=patient_id, image=image_file.read())
        image_instance.save()

        return JsonResponse({'message': 'Image uploaded successfully!'})

    return JsonResponse({'error': 'Invalid request method'})

@csrf_exempt
def get_image(request):
    if request.method == 'GET':
        patient_id = request.GET.get('patientId')
        create_date_str = request.GET.get('createDate')

        # Convert createDate string to datetime object
        create_date = datetime.datetime.strptime(create_date_str, '%d-%m-%Y').date()

        # Retrieve the image instance based on patientId and createDate
        image_instance = get_object_or_404(ImageModel, patientId=patient_id,createDate=create_date)

        # Return the image binary data as a response
        response = HttpResponse(image_instance.image, content_type='image/jpeg')  # Adjust content_type as per your image type
        response['Content-Disposition'] = 'attachment; filename="image.jpg"'  # Adjust filename and extension
        return response

    return JsonResponse({'error': 'Invalid request method'})

@csrf_exempt
def store_survey(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = request.POST  # Use request.POST for form data or request.body for JSON data
            patient_id = data.get('patientId')
            memory = data.get('memory')
            orientation = data.get('orientation')
            judgment = data.get('judgment')
            community = data.get('community')
            hobbies = data.get('hobbies')
            personal_care = data.get('personalCare')
            createDate = datetime.datetime.now().strftime('%Y-%m-%d')
            print(data,patient_id,memory)
            # Create SurveyModel instance
            survey = SurveyModel.objects.create(
                patientId=patient_id,
                memory=memory,
                orientation=orientation,
                judgment=judgment,
                community=community,
                hobbies=hobbies,
                personalCare=personal_care,
                createDate=createDate
            )
            # Return success response
            return JsonResponse({'message': 'Survey data saved successfully'}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return HttpResponseNotAllowed(['POST'])


def convert_to_epoch(date_string):
    # Parse the date string into a datetime object
    date_format = "%Y-%m-%d"  # Define the format of the input date string
    date_obj = datetime.datetime.strptime(date_string, date_format)
   
    # Convert the datetime object to epoch time
    epoch_time = int(date_obj.timestamp())
   
    return epoch_time

@csrf_exempt
def get_survey_data(request):
    if request.method == 'GET':
        patient_id = request.GET.get('patientId')

        if not patient_id:
            return JsonResponse({'error': 'Missing patientId parameter'}, status=400)

        try:
            # Retrieve list of SurveyModel instances for given patientId
            surveys = get_list_or_404(SurveyModel, patientId=patient_id)

            # Prepare response data
            survey_data = []
            for survey in surveys:
                create_date_str = survey.createDate.strftime('%Y-%m-%d')
                survey_data.append({
                    'patientId': survey.patientId,
                    'cdrValue': survey.cdrValues,
                    'createDate'  :   convert_to_epoch(create_date_str)
                })

            # Return JSON response with survey data
            return JsonResponse(survey_data, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return HttpResponseNotAllowed(['GET'])


@api_view(['GET'])
def getAllPatientDetails(request):
    caretaker_id = request.query_params.get('caretakerId', None)
    if caretaker_id is None:
        return Response({"error": "caretakerId parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    patients = Patient.objects.filter(caretakerId=caretaker_id)
    if not patients.exists():
        return Response({"error": "No patients found for the given caretakerId"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = PatientSerializer(patients, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)



class GuestOnlyView(View):
    def dispatch(self, request, *args, **kwargs):
        # Redirect to the index page if the user already authenticated
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)

        return super().dispatch(request, *args, **kwargs)


class LogInView(GuestOnlyView, FormView):
    template_name = 'accounts/log_in.html'

    @staticmethod
    def get_form_class(**kwargs):
        if settings.DISABLE_USERNAME or settings.LOGIN_VIA_EMAIL:
            return SignInViaEmailForm

        if settings.LOGIN_VIA_EMAIL_OR_USERNAME:
            return SignInViaEmailOrUsernameForm

        return SignInViaUsernameForm

    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        # Sets a test cookie to make sure the user has cookies enabled
        request.session.set_test_cookie()

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        request = self.request

        # If the test cookie worked, go ahead and delete it since its no longer needed
        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()

        # The default Django's "remember me" lifetime is 2 weeks and can be changed by modifying
        # the SESSION_COOKIE_AGE settings' option.
        if settings.USE_REMEMBER_ME:
            if not form.cleaned_data['remember_me']:
                request.session.set_expiry(0)

        login(request, form.user_cache)

        redirect_to = request.POST.get(REDIRECT_FIELD_NAME, request.GET.get(REDIRECT_FIELD_NAME))
        url_is_safe = is_safe_url(redirect_to, allowed_hosts=request.get_host(), require_https=request.is_secure())

        if url_is_safe:
            return redirect(redirect_to)

        return redirect(settings.LOGIN_REDIRECT_URL)


class SignUpView(GuestOnlyView, FormView):
    template_name = 'accounts/sign_up.html'
    form_class = SignUpForm

    def form_valid(self, form):
        request = self.request
        user = form.save(commit=False)

        if settings.DISABLE_USERNAME:
            # Set a temporary username
            user.username = get_random_string()
        else:
            user.username = form.cleaned_data['username']

        if settings.ENABLE_USER_ACTIVATION:
            user.is_active = False

        # Create a user record
        user.save()

        # Change the username to the "user_ID" form
        if settings.DISABLE_USERNAME:
            user.username = f'user_{user.id}'
            user.save()

        if settings.ENABLE_USER_ACTIVATION:
            code = get_random_string(20)

            act = Activation()
            act.code = code
            act.user = user
            act.save()

            send_activation_email(request, user.email, code)

            messages.success(
                request, _('You are signed up. To activate the account, follow the link sent to the mail.'))
        else:
            raw_password = form.cleaned_data['password1']

            user = authenticate(username=user.username, password=raw_password)
            login(request, user)

            messages.success(request, _('You are successfully signed up!'))

        return redirect('index')


class ActivateView(View):
    @staticmethod
    def get(request, code):
        act = get_object_or_404(Activation, code=code)

        # Activate profile
        user = act.user
        user.is_active = True
        user.save()

        # Remove the activation record
        act.delete()

        messages.success(request, _('You have successfully activated your account!'))

        return redirect('accounts:log_in')


class ResendActivationCodeView(GuestOnlyView, FormView):
    template_name = 'accounts/resend_activation_code.html'

    @staticmethod
    def get_form_class(**kwargs):
        if settings.DISABLE_USERNAME:
            return ResendActivationCodeViaEmailForm

        return ResendActivationCodeForm

    def form_valid(self, form):
        user = form.user_cache

        activation = user.activation_set.first()
        activation.delete()

        code = get_random_string(20)

        act = Activation()
        act.code = code
        act.user = user
        act.save()

        send_activation_email(self.request, user.email, code)

        messages.success(self.request, _('A new activation code has been sent to your email address.'))

        return redirect('accounts:resend_activation_code')


class RestorePasswordView(GuestOnlyView, FormView):
    template_name = 'accounts/restore_password.html'

    @staticmethod
    def get_form_class(**kwargs):
        if settings.RESTORE_PASSWORD_VIA_EMAIL_OR_USERNAME:
            return RestorePasswordViaEmailOrUsernameForm

        return RestorePasswordForm

    def form_valid(self, form):
        user = form.user_cache
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        if isinstance(uid, bytes):
            uid = uid.decode()

        send_reset_password_email(self.request, user.email, token, uid)

        return redirect('accounts:restore_password_done')


class ChangeProfileView(LoginRequiredMixin, FormView):
    template_name = 'accounts/profile/change_profile.html'
    form_class = ChangeProfileForm

    def get_initial(self):
        user = self.request.user
        initial = super().get_initial()
        initial['first_name'] = user.first_name
        initial['last_name'] = user.last_name
        return initial

    def form_valid(self, form):
        user = self.request.user
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.save()

        messages.success(self.request, _('Profile data has been successfully updated.'))

        return redirect('accounts:change_profile')


class ChangeEmailView(LoginRequiredMixin, FormView):
    template_name = 'accounts/profile/change_email.html'
    form_class = ChangeEmailForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial['email'] = self.request.user.email
        return initial

    def form_valid(self, form):
        user = self.request.user
        email = form.cleaned_data['email']

        if settings.ENABLE_ACTIVATION_AFTER_EMAIL_CHANGE:
            code = get_random_string(20)

            act = Activation()
            act.code = code
            act.user = user
            act.email = email
            act.save()

            send_activation_change_email(self.request, email, code)

            messages.success(self.request, _('To complete the change of email address, click on the link sent to it.'))
        else:
            user.email = email
            user.save()

            messages.success(self.request, _('Email successfully changed.'))

        return redirect('accounts:change_email')


class ChangeEmailActivateView(View):
    @staticmethod
    def get(request, code):
        act = get_object_or_404(Activation, code=code)

        # Change the email
        user = act.user
        user.email = act.email
        user.save()

        # Remove the activation record
        act.delete()

        messages.success(request, _('You have successfully changed your email!'))

        return redirect('accounts:change_email')


class RemindUsernameView(GuestOnlyView, FormView):
    template_name = 'accounts/remind_username.html'
    form_class = RemindUsernameForm

    def form_valid(self, form):
        user = form.user_cache
        send_forgotten_username_email(user.email, user.username)

        messages.success(self.request, _('Your username has been successfully sent to your email.'))

        return redirect('accounts:remind_username')


class ChangePasswordView(BasePasswordChangeView):
    template_name = 'accounts/profile/change_password.html'

    def form_valid(self, form):
        # Change the password
        user = form.save()

        # Re-authentication
        login(self.request, user)

        messages.success(self.request, _('Your password was changed.'))

        return redirect('accounts:change_password')


class RestorePasswordConfirmView(BasePasswordResetConfirmView):
    template_name = 'accounts/restore_password_confirm.html'

    def form_valid(self, form):
        # Change the password
        form.save()

        messages.success(self.request, _('Your password has been set. You may go ahead and log in now.'))

        return redirect('accounts:log_in')


class RestorePasswordDoneView(BasePasswordResetDoneView):
    template_name = 'accounts/restore_password_done.html'


class LogOutConfirmView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/log_out_confirm.html'


class LogOutView(LoginRequiredMixin, BaseLogoutView):
    template_name = 'accounts/log_out.html'
