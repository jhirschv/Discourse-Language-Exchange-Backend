from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (MyTokenObtainPairSerializer, UserSerializer, MessageSerializer, ChatSessionSerializer)
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import (User, Message, ChatSession)
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .utils import get_chat_session, get_messages_for_session

# Create your views here.

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class UserRegistrationView(APIView):
    def post(self, request):
        serializer = User(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                tokens = get_tokens_for_user(user)
                return Response({"tokens": tokens, "message": "User created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    def delete(self, request):
        # Directly use request.user since it's always present for authenticated users
        user = request.user
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

class ChatSessionViewSet(viewsets.ModelViewSet):
    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer

    def destroy(self, request, *args, **pk):
        chat_session = self.get_object()
        messages = Message.objects.filter(chat_session=chat_session)
        messages.delete()  # Delete all messages associated with the chat session
        chat_session.delete()  # Delete the chat session
        return Response(status=status.HTTP_204_NO_CONTENT)

class ChatSessionMessageViewSet(viewsets.ViewSet):
    def retrieve_or_create_session_get_messages(self, request, other_user_id=None):
        chat_session = get_chat_session(request.user.id, other_user_id)
        if chat_session:
            messages = get_messages_for_session(chat_session)
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
        return Response({"message": "No chat session found"}, status=404)
    
class UserChatSessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        chat_sessions = ChatSession.objects.filter(participants=user).distinct()
        serializer = ChatSessionSerializer(chat_sessions, many=True, context={'request': request})
        return Response(serializer.data)

