from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model, authenticate
from rest_framework.permissions import AllowAny
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.timezone import now
from accounts.serializers import UserSerializer
from django.conf import settings
from django.core.mail import send_mail

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email")
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        address = request.data.get("address")

        if not username or not password or not email:
            return Response({"error": "Username, password, and email are required."}, status=401)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists."}, status=400)
        
        if User.objects.filter(email=email).exists():
            return Response({"error": "email already exists."}, status=400)

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            address = address
        )
        
        user.is_active = False
        user.save()

        # Create email activation link
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = request.build_absolute_uri(
            reverse('activate', kwargs={'uidb64': uid, 'token': token})
        )

        # Send verification email
        subject = "Activate your account"
        message = f"Hi {user.first_name},\n\nPlease click the link below to activate your account:\n{activation_link}\n\nThank you!"
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]

        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        except Exception as e:
            return Response({"error": "Failed to send email.", "details": str(e)}, status=500)

        return Response({
            "message": "Registration successful! Please check your email to activate your account."
        }, status=201)
    
# Process verification link (activate account)
class ActivateAccountView(APIView):
    permission_classes = []

    def get(self, request, uidb64, token):
        try:
            # Convert the encoded uid back to user pk
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({'message': 'Account successfully activated'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'The verification link is invalid or has expired'}, status=status.HTTP_400_BAD_REQUEST)


# Resend verification link
class ResendActivationEmailView(APIView):
    permission_classes = []  # Allow unauthenticated users to call

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Please enter email"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)

            if user.is_active:
                return Response({
                    "message": "This account has already been activated. No need to resend verification link."
                }, status=401)

            # Generate a new verification link
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = request.build_absolute_uri(
                f"/accounts/activate/{uid}/{token}/"
            )

            # Send the email
            subject = "Resend Activation Link"
            message = f"Hi {user.first_name},\n\nPlease click the link below to activate your account:\n{activation_link}\n\nThank you!"
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [user.email]

            send_mail(subject, message, from_email, recipient_list, fail_silently=False)

            return Response({
                "message": "A new activation email has been sent. Please check your inbox."
            }, status=200)

        except User.DoesNotExist:
            # To avoid information leakage, do not reveal if email exists
            return Response({
                "message": "A new activation email has been sent. Please check your inbox."
            }, status=200)
        
# login API
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if user is not None:
            # update last_login
            user.last_login = now()
            user.save(update_fields=['last_login'])

            # 建create token
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "message": "Login successfully!",
            }, status=200)

        return Response({"error": "Invalid credentials"}, status=400)

# logout API（delete token）
class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({"message": "Logged out successfully."}, status=200)

# User info
class AccountDetailView(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
# Edit Account

class AccountUpdateView(APIView):
    authentication_classes = [TokenAuthentication]

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Account updated successfully", "user": serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Account partially updated successfully", "user": serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Delete Account

class AccountDeleteView(APIView):
    authentication_classes = [TokenAuthentication]

    def delete(self, request):
        request.user.delete()
        return Response({"message": "Account deleted"}, status=204)
