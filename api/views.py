from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout

class LoginView(APIView):
    permission_classes = [AllowAny]  # 登入不需先驗證

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)  # 利用 Django session 登入
            return Response({"message": "登入成功"})
        else:
            return Response({"error": "帳號或密碼錯誤"}, status=400)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # 登出需要先登入才可用

    def post(self, request):
        logout(request)  # 清除 session
        return Response({"message": "登出成功"})
