from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from .serializers import (
    RegisterSerializer,
    check,
    LoginSerializer,
    UserSerializer,
)
from .models import UserAccount
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import (
    smart_str,
    smart_bytes,
)
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import authenticate
from django.contrib.auth import login, logout
from django.urls import reverse
from .utils import Util, part1, part2, part3, part4, part5
from rest_framework.authtoken.models import Token
from django.shortcuts import redirect
from django.http import Http404
from udyam_backend.settings import BASE_URL_FRONTEND


class LoginView(generics.GenericAPIView):
    """
    Implement login functionality, taking email and password
    as input, and returning the Token.
    """

    serializer_class = LoginSerializer

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        if email is None or password is None:
            return Response(
                {"error": "Please provide both email and password"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif len(UserAccount.objects.filter(email=email)) == 0:
            return Response(
                {"error": "Your email is not registered with us."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user1 = UserAccount.objects.get(email=email)
        if user1.is_active is False:
            return Response(
                {"error": "You have not activated your account after registration. Please check your mail."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = authenticate(username=email, password=password)
        if not user:
            return Response(
                {"error": "Please check your credentials...cannot login!"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})


class FormData(generics.GenericAPIView):

    def post(self, request):
        email = request.data.get("email")
        user = UserAccount.objects.filter(email = email) ;

        if not user :
            return Response(
                {"error": "Please check your credentials...cannot login!"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        
        was_active = user.is_active 
        if was_active :
            return Response(
                {"message": "User already registered"},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        college_name = request.data.get("college_name")
        referral_code = request.data.get("refferal_code")
        year = request.data.get("year")


        user.college_name = college_name 
        user.year = year

        if referral_code and was_active is False:
            ref_user = UserAccount.objects.get(user_referral_code=user.referral_code)
            if  not ref_user:
                return Response(
                {"error": "unknown referral code"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            else :
                ref_user.referral_count += 1
                ref_user.save()
        
        user.is_active = True
        user.save() 
        login(request, user)

        return Response(
            {"message" : "Your Account Has Been Succesfully Created"},
            status=status.HTTP_201_CREATED
        )



class LogoutView(generics.GenericAPIView):

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = LoginSerializer

    def get(self, request):
        logout(request)

        return Response(status=status.HTTP_200_OK)



class UserUpdateView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = UserAccount.objects.all()
    serializer_class = UserSerializer

    def get(self, request):
        try:
            user = request.user
            content = {
                "name": user.name,
                "email": user.email,
                "college_name": user.college_name,
                "year": user.year,
                "referral_code": user.user_referral_code,
            }
            return Response(content, status=status.HTTP_200_OK)
        except serializers.get_error_detail:
            return Response(
                {"error": "An error occurred!"}, status=status.HTTP_403_FORBIDDEN
            )

    def post(self, request):
        user = UserAccount.objects.filter(email=request.user.email)
        if user is not None:
            if "name" in request.data:
                user.update(name=request.data["name"])
            if "year" in request.data:
                user.update(
                    year=request.data["year"],
                )
            if "college_name" in request.data:
                user.update(
                    college_name=request.data["college_name"],
                )
            return Response(
                {"message": "Updated successfully!"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "An error occurred!"}, status=status.HTTP_403_FORBIDDEN
            )


class RegisterView(generics.GenericAPIView):
    queryset = UserAccount.objects.all()
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = check(request.data)
            if user is None:
                user = serializer.save()
                create_auth_token(user=user)
                uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
                token = PasswordResetTokenGenerator().make_token(user)
                current_site = get_current_site(request=request).domain
                relativeLink = reverse(
                    "activate-account", kwargs={"uidb64": uidb64, "token": token}
                )
                absurl = "http://" + current_site + relativeLink
                email_body = (
                    part1
                    + user.name
                    + part2
                    + """Thanks for registering on Udyam. Here is the discord link of udyam: https://discord.gg/gNrEW8vp4G <br>
                    To complete your udyam sign up, we just need to verify your email address.<br>
                    Click the link below to verify:"""
                    + part3
                    + absurl
                    + part4
                    + "Verify Email"
                    + part5
                )
                data = {
                    "email_body": email_body,
                    "to_mail": [user.email],
                    "email_subject": "Activate Your Udyam Account",
                }
                Util.send_email(data)
                return Response(
                    {"success": "Verification link has been sent by email!"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "User with same credentials already exists!"},
                    status=status.HTTP_226_IM_USED,
                )
        else:
            # print(serializer.errors)
            error = {}
            for err in serializer.errors:
                error[err] = serializer.errors[err][0]
            return Response(error, status=status.HTTP_409_CONFLICT)


# def ActivateAccount(request, uidb64, token):
#     id = smart_str(urlsafe_base64_decode(uidb64))
#     user = UserAccount.objects.get(id=id)
#     if not PasswordResetTokenGenerator().check_token(user, token):
#         raise Http404
#     url = BASE_URL_FRONTEND + "/loginregister"
#     was_active = user.is_active
#     user.is_active = True
#     user.save()
#     if user.referral_code and was_active is False:
#         user = UserAccount.objects.get(user_referral_code=user.referral_code)
#         if user is not None:
#             user.referral_count += 1
#             user.save()
#     return redirect(url)
