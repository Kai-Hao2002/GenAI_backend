import base64
import os
from uuid import uuid4
import qrcode
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, time
from ai.serializers import EventPreferenceSerializer,InvitationRequestSerializer
from api.models import Event,EventEditor,TaskAssignment,VenueSuggestion,Registration,EmailLog,SocialPost,VisualAsset
from django.contrib.auth import get_user_model
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from django.utils.timezone import localtime,make_aware
from django.shortcuts import get_object_or_404
import traceback

from ai.services.services import (
    generate_event_from_gemini,generate_task_assignment_from_gemini,
    generate_venue_suggestion_from_gemini,generate_registration_form_from_gemini,
    generate_invitation_from_gemini,generate_social_post_gemini,generate_poster_text_gemini,
    generate_poster_image_openai
)


User = get_user_model()


# Permission Tools
def has_role(user, event_id, roles):
    return EventEditor.objects.filter(event_id=event_id, user=user, role__in=roles).exists()

# Create Event
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

            # Parse the date string and preset it to 00:00 and 23:59:59 on the current day
            date_str = data.get("date")
            event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time = make_aware(datetime.combine(event_date, time(0, 0, 0)))
            end_time = make_aware(datetime.combine(event_date, time(23, 59, 59)))

            event = Event.objects.create(
                name=ai_response["name"][0],  # default the first list of name
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

             
            response_data = ai_response.copy()
            response_data["event_id"] = event.id

            
            return Response(response_data , status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": f"Failed to generate or save event: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Create TaskAssighnment
class TaskAssignmentGenerationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):

        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

 
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)


        event_data = {
            "event": {
                "event_name": event.name,
                "start_time": event.start_time.isoformat() if event.start_time else None,
                "end_time": event.end_time.isoformat() if event.end_time else None,
                "expected_attendees": event.expected_attendees,
                "type": event.type,
            }
        
        }

        try:
            result = generate_task_assignment_from_gemini(event_data)

            
            TaskAssignment.objects.filter(event=event).delete()  

            task_data_list = result.get("task_summary_by_role", [])
            updated_task_data_list = []

            for task in task_data_list:
                saved = TaskAssignment.objects.create(
                    event=event,
                    role=task.get("role"),
                    description=task.get("description", ""),
                    count=task.get("count", 0),
                    start_time=task.get("start_time"),
                    end_time=task.get("end_time"),
                )
                
                task["id"] = saved.id
                task["event_id"] = event.id
                updated_task_data_list.append(task)

            result["task_summary_by_role"] = updated_task_data_list
            

            return Response(result, status=status.HTTP_200_OK)


        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# Create VenueSuggestion
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

        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get("name", "")
        radius_km = request.data.get("radius_km", "")

        
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
               
            }
        }

        try:
            result = generate_venue_suggestion_from_gemini(input_data)
            suggestions = result.get("venue_suggestions", [])

            updated_suggestions = []

            for idx, venue in enumerate(suggestions):
               
                address, map_url = self.geocode_place_name(venue.get("name"))

                
                venue["address"] = address if address else venue.get("address", "")
                venue["map_url"] = map_url if map_url else venue.get("map_url")

                

              
                if idx == 0:
                 
                    VenueSuggestion.objects.filter(event=event).delete()

                    saved = VenueSuggestion.objects.create(
                        event=event,
                        name=venue.get("name"),
                        address=venue["address"],
                        capacity=venue.get("capacity"),
                        transportation_score=venue.get("transportation_score"),
                        map_url=venue["map_url"],
                        is_outdoor=venue.get("is_outdoor"),
                    )

    
 
                venue["id"] = saved.id  
                venue["event_id"] = event.id

                updated_suggestions.append(venue)

            result["venue_suggestions"] = updated_suggestions
            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Create RegistrationFormField
class RegistrationFormGenerationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        try:
            event = Event.objects.get(id=event_id)
            venue = VenueSuggestion.objects.get(event_id=event_id)
        except (Event.DoesNotExist, VenueSuggestion.DoesNotExist):
            return Response({"error": "Event or Venue not found"}, status=status.HTTP_404_NOT_FOUND)

        event_data = {
            "event": {
                "event_id": event.id,
                "event_name": event.name,
                "start_time": event.start_time.isoformat() if event.start_time else None,
                "end_time": event.end_time.isoformat() if event.end_time else None,
                "expected_attendees": event.expected_attendees,
                "type": event.type,
                "slogan": event.slogan,
                "targeted_audiences": event.target_audience,
            },
            "venue": {
                "name": venue.name,
                "address": venue.address,
            }
        }

        try:
            result = generate_registration_form_from_gemini(event_data)

            
            Registration.objects.filter(event=event).delete()

            registration_list = result.get("registration-list", [])
            updated_list = []

            for registration in registration_list:
                saved = Registration.objects.create(
                    event=event,
                    event_intro=registration.get("event_intro", ""),
                    form_title=registration.get("form_title", ""),
                    form_fields=registration.get("form_fields", ""),
                )

                
                registration["id"] = saved.id
                registration["event_id"] = event.id
                updated_list.append(registration)

            result["registration-list"] = updated_list
            return Response(result, status=status.HTTP_200_OK)


        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InvitationGenerationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
       
        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        
        event = get_object_or_404(Event, id=event_id)
        venue = get_object_or_404(VenueSuggestion, event_id=event_id)
        registration = get_object_or_404(Registration, event_id=event_id)

        
        serializer = InvitationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data

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
            "registration": {
                "registration_url": registration.registration_url,
            },
            "invitation": {
                "receiver_name": data["receiver_name"],
                "words_limit": data["words_limit"],
                "tone": data["tone"],
                "language": data["language"],
            }
        }

        try:
            result = generate_invitation_from_gemini(event_data)

            invitation_list = result.get("invitation_list", [])
            if not invitation_list:
                return Response({"error": "No invitation content returned from Gemini."}, status=500)

            updated_list = []
            for invitation in invitation_list:
                saved = EmailLog.objects.create(
                    event=event,
                    recipient_email=data["recipient_email"],
                    recipient_name=data["receiver_name"],
                    subject=invitation.get("invitation_letter_subject", ""),
                    body=invitation.get("invitation_letter_body", ""),
                )
                invitation["id"] = saved.id
                invitation["event_id"] = event.id
                updated_list.append(invitation)

            result["invitation_list"] = updated_list
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            print("🛑 Internal error generating invitation:")
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Create posts on the Social media 
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
            registration = Registration.objects.get(event_id=event_id)
        except Registration.DoesNotExist:
            return Response({"error": "Registration not found"}, status=status.HTTP_404_NOT_FOUND)
        
        platform = request.data.get("platform", "")
        tone = request.data.get("tone", "")
        hook_type = request.data.get("hook_type", "")
        words_limit = request.data.get("words_limit", "")
        include_emoji = request.data.get("include_emoji", "")
        emoji_level = request.data.get("emoji_level", "")
        power_words = request.data.get("power_words", "")
        hashtag_seeds = request.data.get("hashtag_seeds", "")
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
            "registration": {
                "registration_url": registration.registration_url,
            },
            "social_post": {
                "platform": platform,
                "words_limit": words_limit,  
                "tone": tone,
                "hook_type": hook_type,  
                "include_emoji": include_emoji,  
                "emoji_level": emoji_level,  
                "power_words": power_words,  
                "hashtag_seeds": hashtag_seeds,  
                "language": language, 
            }
        }

        try:
            result = generate_social_post_gemini(event_data)
            SocialPost.objects.filter(event=event).delete()

            post_list = result.get("post_list", [])
            updated_post_list = []

            for post in post_list:
                saved = SocialPost.objects.create(
                    event=event,
                    platform=platform,
                    tone=tone,
                    language=language,
                    content=post.get("content", ""),
                )
                
                post["id"] = saved.id
                post["event_id"] = event.id
                updated_post_list.append(post)

            result["post_list"] = updated_post_list

            return Response(result, status=status.HTTP_200_OK)



        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Create poster
class PosterGenerationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        try:
            event = Event.objects.get(id=event_id)
            venue = VenueSuggestion.objects.get(event_id=event_id)
        except (Event.DoesNotExist, VenueSuggestion.DoesNotExist):
            return Response({"error": "Event or venue not found"}, status=status.HTTP_404_NOT_FOUND)

        
        tone = request.data.get("tone", "")
        color_scheme = request.data.get("color_scheme", "")
        layout_style = request.data.get("layout_style", "")
        font_style = request.data.get("font_style", "")
        language = request.data.get("language", "")

        
        event_data = {
            "event": {
                "event_id": event.id,
                "event_name": event.name,
                "event_description": event.description,
                "event_slogan": event.slogan,
                "event_target_audience": event.target_audience,
                "event_type": event.type,
                "start_time": localtime(event.start_time).strftime('%Y-%m-%d %H:%M'),
                "end_time": localtime(event.end_time).strftime('%Y-%m-%d %H:%M'),
            },
            "venue": {
                "name": venue.name,
                "address": venue.address,
            },
            "poster": {
                "language": language,
                "tone": tone,
                "color_scheme": color_scheme,
                "layout_style": layout_style,
                "font_style": font_style,
            }
        }

        try:
        
            poster_text = generate_poster_text_gemini(event_data)
            headline = poster_text["headline"]
            subheadline = poster_text["subheadline"]

           
            event_data["poster_text"] = {
                "headline": headline,
                "subheadline": subheadline
            }

         
            image_base64 = generate_poster_image_openai(event_data)

    
            img_bytes = base64.b64decode(image_base64)
            folder = os.path.join(settings.MEDIA_ROOT, "generated_posters")
            os.makedirs(folder, exist_ok=True)
            filename = f"{uuid4().hex}.png"
            filepath = os.path.join(folder, filename)

            with open(filepath, "wb") as f:
                f.write(img_bytes)

            media_url = f"{settings.MEDIA_URL}generated_posters/{filename}"

            VisualAsset.objects.filter(event=event).delete()
            visual_asset = VisualAsset.objects.create(
                event=event,
                image_url=media_url,
                headline=headline,
                subheadline=subheadline,
                tone=tone,
                color_scheme=color_scheme,
                font_style=font_style,
                layout_style=layout_style,
            )

            return Response({
                "image_url": media_url,
                "filename": filename,
                "local_path": filepath,
                "headline": headline,
                "subheadline": subheadline,
                "visual_asset_id": visual_asset.id
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
