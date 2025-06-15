from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, time
from ai.serializers import EventPreferenceSerializer
from api.models import Event,EventEditor,TaskAssignment,VenueSuggestion,Registration,EmailLog,SocialPost
from django.contrib.auth import get_user_model
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from ai.google_form_views import load_credentials, create_google_form
from ai.services.services import (
    generate_event_from_gemini,generate_task_assignment_from_gemini,
    generate_venue_suggestion_from_gemini,generate_registration_form_from_gemini,
    generate_invitation_from_gemini,generate_social_post_gemini
)


User = get_user_model()


# Permission Tools
def has_role(user, event_id, roles):
    return EventEditor.objects.filter(event_id=event_id, user=user, role__in=roles).exists()

class GenerateEventAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EventPreferenceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            ai_response = generate_event_from_gemini(data)

            # 解析日期字串並轉成當天 00:00 跟 23:59:59
            date_str = data.get("date")
            event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time = datetime.combine(event_date, time(00, 00, 00))  # 00:00:00
            end_time = datetime.combine(event_date, time(23, 59, 59))  # 23:59:59

            event = Event.objects.create(
                name=ai_response["name"][0],  # 取第一個建議的名稱
                description=ai_response["description"],
                slogan=ai_response["slogan"][0],
                target_audience=data.get("target_audience"),
                expected_attendees=ai_response["expected_attendees"],
                start_time=start_time,
                end_time=end_time,
                type=data.get("type"),
                budget=data.get("budget"),
                status="draft",
                created_by=request.user
            )
            EventEditor.objects.create(
                event=event,
                user=request.user,
                role='owner'
            )

             # 把 event.id 加入回傳資料
            response_data = ai_response.copy()
            response_data["event_id"] = event.id

            # 回傳全部 AI 建議（前端選擇後再呼叫另存API）
            return Response(response_data , status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": f"Failed to generate or save event: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TaskAssignmentGenerationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        # 權限檢查
        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        # 取得 Event 資料
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        # 組合成 event_data 給 Gemini 用
        event_data = {
            "event": {
                "event_id": event.id,
                "event_name": event.name,
                "start_time": event.start_time.isoformat() if event.start_time else None,
                "end_time": event.end_time.isoformat() if event.end_time else None,
                "expected_attendees": event.expected_attendees,
                "type": event.type,
            }
        
        }

        try:
            # 丟給 Gemini 產生任務
            result = generate_task_assignment_from_gemini(event_data)

            # 儲存到資料庫
            task_data_list = result.get("task_summary_by_role", [])
            TaskAssignment.objects.filter(event=event).delete()  # 清除原本的（可選）
            for task in task_data_list:
                TaskAssignment.objects.create(
                    event=event,
                    role=task.get("role"),
                    description=task.get("description", ""),
                    count=task.get("count", 0),
                    start_time=task.get("start_time"),
                    end_time=task.get("end_time"),
                )

            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class VenueSuggestionGenerationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def geocode_place_name(self, place_name: str):
        try:
            geolocator = Nominatim(user_agent="EventIQBot/1.0 (zxcv2442442002@gmail.com)")
            location = geolocator.geocode(place_name, timeout=10)
            if location:
                address = location.address
                lat = location.latitude
                lon = location.longitude
                map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                return address, map_url
            else:
                return None, None
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            return None, None

    def post(self, request, event_id):
        # 權限檢查
        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        # 從資料庫抓 event
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get("name", "")
        radius_km = request.data.get("radius_km", "")

        # 不用geocode地址座標給 Gemini，因為你要只用名稱產生建議（也可改掉這部分）
        input_data = {
            "event": {
                "event_id": event.id,
                "name": event.name,
                "type": event.type,
                "expected_attendees": event.expected_attendees,
                "start_time": event.start_time.isoformat() if event.start_time else None,
                "end_time": event.end_time.isoformat() if event.end_time else None,
                "budget": event.budget,
                "target_audience": event.target_audience,
            },
            "venue_suggestion": {
                "radius_km": radius_km,
                "name": name,
                # 不送 latitude, longitude，讓 Gemini 只用名字產生場地名稱建議
            }
        }

        try:
            result = generate_venue_suggestion_from_gemini(input_data)
            suggestions = result.get("venue_suggestions", [])

            updated_suggestions = []

            for idx, venue in enumerate(suggestions):
                # 用 geopy 查場地名稱的正確地址與地圖連結
                address, map_url = self.geocode_place_name(venue.get("name"))

                # 更新場地資訊回傳給前端
                venue["address"] = address if address else venue.get("address", "")
                venue["map_url"] = map_url if map_url else venue.get("map_url")

                updated_suggestions.append(venue)

                # 只存第一筆到資料庫
                if idx == 0:
                    # 清空舊資料（可選）
                    VenueSuggestion.objects.filter(event=event).delete()

                    VenueSuggestion.objects.create(
                        event=event,
                        name=venue.get("name"),
                        address=venue["address"],
                        capacity=venue.get("capacity"),
                        transportation_score=venue.get("transportation_score"),
                        map_url=venue["map_url"],
                        is_outdoor=venue.get("is_outdoor"),
                    )

            # 更新回傳的結果
            result["venue_suggestions"] = updated_suggestions

            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RegistrationFormGenerationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        # 權限檢查
        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        # 取得 Event 資料
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            venue = VenueSuggestion.objects.get(event_id=event_id)
        except VenueSuggestion.DoesNotExist:
            return Response({"error": "VenueSuggestion not found"}, status=status.HTTP_404_NOT_FOUND)

        # 組合成 event_data 給 Gemini 用
        event_data = {
            "event": {
                "event_id": event.id,
                "event_name": event.name,
                "start_time": event.start_time.isoformat() if event.start_time else None,
                "end_time": event.end_time.isoformat() if event.end_time else None,
                "expected_attendees": event.expected_attendees,
                "type": event.type,
                "slogan" :event.slogan,
                "targeted_audiences" :event.target_audience,
            },
            "venue":{
                "name": venue.name,
                "address" : venue.address,
            }
        
        }

        try:
            # 1. 產生報名表 JSON 資料
            result = generate_registration_form_from_gemini(event_data)

            # 2. 從 result 取得表單標題與欄位
            form_title = result.get("form_title", f"Registration for {event.name}")
            form_fields = result.get("form_fields", [])
            form_description = result.get("event_intro", f"Registration for {event.description}")

            if not form_fields:
                return Response({"error": "form_fields is required"}, status=status.HTTP_400_BAD_REQUEST)

            # 3. 取得 Google API 憑證
            creds = load_credentials()
            if not creds:
                return Response({"error": "Google OAuth credentials missing"}, status=status.HTTP_401_UNAUTHORIZED)

            # 4. 用 create_google_form 產生 Google 表單
            registration_url, edit_url = create_google_form(creds, form_title, form_fields,form_description)

            # 5. 把連結存到資料庫
            registration, created = Registration.objects.get_or_create(event=event)
            registration.registration_url = registration_url
            registration.edit_url = edit_url
            registration.save()

            # 6. 回傳結果給前端
            return Response({
                "registration_url": registration_url,
                "edit_url": edit_url,
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InvitationGenerationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            venue = VenueSuggestion.objects.get(event_id=event_id)
        except VenueSuggestion.DoesNotExist:
            return Response({"error": "VenueSuggestion not found"}, status=status.HTTP_404_NOT_FOUND)
    
        try:
            registeration = Registration.objects.get(event_id=event_id)
        except Registration.DoesNotExist:
            return Response({"error": "Registration not found"}, status=status.HTTP_404_NOT_FOUND)
        
        receiver_name = request.data.get("receiver_name", "")
        recipient_email = request.data.get("recipient_email", "")
        words_limit = request.data.get("words_limit", "")
        tone = request.data.get("tone", "")
        language = request.data.get("language", "")

        event_data = {
            "event": {
                "event_id": event.id,
                "event_name": event.name,
                "event_description": event.description,
                "event_slogan": event.slogan,
                "type": event.type,
                "start_time": event.start_time.isoformat() if event.start_time else None,
                "end_time": event.end_time.isoformat() if event.end_time else None,
            },
            "venue": {
                "name": venue.name,
                "address": venue.address,  
            },
            "registeration": {
                "registeration_url": registeration.registration_url,
            },
            "invitation": {
                "receiver_name": receiver_name,
                "words_limit": words_limit,  
                "tone": tone,
                "language": language,  
            }
        }

        try:
            result = generate_invitation_from_gemini(event_data)

            invitation_list = result.get("invitation_list", [])
            for invitation in invitation_list:
                EmailLog.objects.create(
                    event=event,
                    recipient_email=recipient_email,
                    recipient_name=receiver_name,
                    subject=invitation.get("invitation_letter_subject", ""),
                    body=invitation.get("invitation_letter_body", ""),
                )

            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SocialPostGenerationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            venue = VenueSuggestion.objects.get(event_id=event_id)
        except VenueSuggestion.DoesNotExist:
            return Response({"error": "VenueSuggestion not found"}, status=status.HTTP_404_NOT_FOUND)
    
        try:
            registeration = Registration.objects.get(event_id=event_id)
        except Registration.DoesNotExist:
            return Response({"error": "Registration not found"}, status=status.HTTP_404_NOT_FOUND)
        
        platform = request.data.get("platform", "")
        tone = request.data.get("tone", "")
        hook_type = request.data.get("hook_type", "")
        words_limit = request.data.get("words_limit", "")
        include_emoji = request.data.get("include_emoji", "")
        emoji_level = request.data.get("emoji_level", "")
        power_words = request.data.get("power_words", "")
        hsashtag_seeds = request.data.get("hsashtag_seeds", "")
        language = request.data.get("language", "")

        event_data = {
            "event": {
                "event_id": event.id,
                "event_name": event.name,
                "event_description": event.description,
                "event_slogan": event.slogan,
                "event_target_audience": event.target_audience,
                "type": event.type,
                "start_time": event.start_time.isoformat() if event.start_time else None,
                "end_time": event.end_time.isoformat() if event.end_time else None,
            },
            "venue": {
                "name": venue.name,
                "address": venue.address,  
            },
            "registeration": {
                "registeration_url": registeration.registration_url,
            },
            "social_post": {
                "platform": platform,
                "words_limit": words_limit,  
                "tone": tone,
                "hook_type": hook_type,  
                "include_emoji": include_emoji,  
                "emoji_level": emoji_level,  
                "power_words": power_words,  
                "hsashtag_seeds": hsashtag_seeds,  
                "language": language, 
            }
        }

        try:
            result = generate_social_post_gemini(event_data)

            post_list = result.get("post_list", [])
            for post in post_list:
                SocialPost.objects.create(
                    event=event,
                    platform=platform,
                    tone=tone,
                    language=language,
                    content=post.get("content", ""),
                )

            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
