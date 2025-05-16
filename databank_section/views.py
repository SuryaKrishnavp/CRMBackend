from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from auth_section.permissions import IsSalesManagerUser,IsCustomAdminUser
from auth_section.models import Sales_manager_reg
from leads_section.models import Leads,LeadCategory
from rest_framework.response import Response
from .serializers import DatabankSerializer,DataBankEditSerializer,DataBankGETSerializer,DataBankImageSerializer
from rest_framework import status
from .models import DataBank,DataBankImage
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from django.db.models import Q
from django.http import JsonResponse
from .filters import DataBankFilter
from django.core.mail import send_mail
from django.conf import settings
from auth_section.models import Ground_level_managers_reg
from rest_framework.permissions import IsAuthenticated
from project_section.models import Project_db
from django.core.mail import EmailMessage
from django.conf import settings
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from leads_section.models import Leads
import os
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import pagesizes
from django.core.files.images import ImageFile
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Image
import requests
from PIL import Image as PILImage
from geopy.geocoders import Nominatim
from opencage.geocoder import OpenCageGeocode
from geopy.distance import geodesic
import re


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def get_lead_data(request, lead_id):
    user = request.user
    sales_manager = Sales_manager_reg.objects.filter(user=user.id).first()

    if not sales_manager:
        return Response({"error": "Sales Manager not found"}, status=status.HTTP_404_NOT_FOUND)


    # Get Lead
    lead = get_object_or_404(Leads, id=lead_id)

    # Prepare response
    lead_data = {
        "name": lead.name,
        "email": lead.email,
        "phonenumber": lead.phonenumber,
        "district": lead.district,
        "place": lead.place,
        "address":lead.address,
        "purpose": lead.purpose,
        "mode_of_purpose":lead.mode_of_purpose,
        "follower": lead.follower
    }
    return Response(lead_data, status=status.HTTP_200_OK)


        
    
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSalesManagerUser])
def store_data_into_db(request, lead_id):
    user = request.user
    sales_manager = Sales_manager_reg.objects.filter(user=user.id).first()

    if not sales_manager:
        return Response({"error": "Sales Manager not found"}, status=status.HTTP_404_NOT_FOUND)

    lead = get_object_or_404(Leads, id=lead_id)
    if lead.staff_id != sales_manager.id:
        return Response({"error": "Sales Manager mismatch"}, status=status.HTTP_403_FORBIDDEN)

    serializer = DatabankSerializer(data=request.data)

    if serializer.is_valid():
        validated_data = serializer.validated_data
        lead_category_value = validated_data.get("lead_category", None)
        databank_entry = DataBank.objects.create(
            lead=lead,
            follower=sales_manager,
            timestamp=timezone.now(),
            **serializer.validated_data
        )
        if lead_category_value:
            LeadCategory.objects.create(
                lead=lead,
                category=lead_category_value
            )
        return Response({"success": "Data stored successfully", "id": databank_entry.id}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['PATCH'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])  
def update_databank(request, databank_id):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanger = Sales_manager_reg.objects.filter(user = staff.id).first()

    try:
        databank = DataBank.objects.get(id=databank_id)
    except DataBank.DoesNotExist:
        return Response({"error": "DataBank entry not found"}, status=404)

    # Check if the logged-in staff is the follower of this databank entry
    if databank.follower_id != salesmanger.id:
        return Response({'message': 'Data editable only by the assigned follower'}, status=403)

    # Partially update only provided fields
    serializer = DataBankEditSerializer(databank, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        lead_category_value = request.data.get('lead_category')
        if lead_category_value:
            try:
                lead = databank.lead  # Assuming DataBank has FK to Leads
            except AttributeError:
                return Response({"error": "DataBank is not linked to a Lead"}, status=400)

            # Update existing LeadCategory category only (no timestamp change)
            lead_category_instance = LeadCategory.objects.filter(lead=lead).first()
            if lead_category_instance:
                lead_category_instance.category = lead_category_value
                lead_category_instance.save(update_fields=['category'])
        return Response(serializer.data, status=200)
    
    return Response(serializer.errors, status=400)





@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def view_databank_data(request):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()

    data = DataBank.objects.filter(follower_id=salesmanager.id)
    
    serializer = DataBankEditSerializer(data, many=True)
    return Response(serializer.data, status=200)




@api_view(['DELETE'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])  
def delete_databank(request, databank_id):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    try:
        databank = DataBank.objects.get(id=databank_id)
    except DataBank.DoesNotExist:
        return Response({"error": "DataBank entry not found"}, status=404)

    if databank.follower_id != salesmanager.id:
        return Response({"error": "Only the assigned follower can delete this entry"}, status=403)

    databank.delete()
    return Response({"message": "DataBank entry deleted successfully"}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def autocomplete_databank(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({"suggestions": []})

    matches = DataBank.objects.filter(
        Q(name__icontains=query) |
        Q(district__icontains=query) |
        Q(place__icontains=query)
    ).values_list('name', 'district', 'place')

    suggestions = set()
    for name, district, place in matches:
        if name and query.lower() in name.lower():
            suggestions.add(name)
        if district and query.lower() in district.lower():
            suggestions.add(district)
        if place and query.lower() in place.lower():
            suggestions.add(place)

    return JsonResponse({"suggestions": list(suggestions)})



@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def databank_suggestions(request):
    query = request.GET.get("q", "").strip()
    suggestions = set()

    if not query:
        return Response({"suggestions": []})

    matching_items = DataBank.objects.filter(
        Q(name__icontains=query) |
        Q(district__icontains=query) |
        Q(place__icontains=query)
    ).values_list("name", "district", "place")

    for name, district, place in matching_items:
        if name and query.lower() in name.lower():
            suggestions.add(name)
        if district and query.lower() in district.lower():
            suggestions.add(district)
        if place and query.lower() in place.lower():
            suggestions.add(place)

    return Response({"suggestions": list(suggestions)[:10]})  # limit to top 10


from leads_section.serializers import LeadsViewSerializer
from project_section.serializers import ProjectSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def search_databank(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({"error": "Query parameter is required"}, status=400)

    # 1️⃣ Search in Databank
    databank_results = DataBank.objects.filter(
        Q(name__icontains=query) |
        Q(email__icontains=query) |
        Q(phonenumber__icontains=query) |
        Q(district__icontains=query) |
        Q(place__icontains=query) |
        Q(purpose__icontains=query) |
        Q(mode_of_property__icontains=query) |
        Q(demand_price__icontains=query) |
        Q(location_proposal_district__icontains=query) |
        Q(location_proposal_place__icontains=query) |
        Q(area_in_sqft__icontains=query) |
        Q(building_roof__icontains=query) |
        Q(number_of_floors__icontains=query) |
        Q(building_bhk__icontains=query) |
        Q(projects__project_name__icontains=query) |
        Q(projects__importance__icontains=query)
    )

    if databank_results.exists():
        return JsonResponse({
            "source": "databank",
            "results": DataBankGETSerializer(databank_results, many=True).data
        })

    # 2️⃣ If no Databank results, search in Leads
    lead_results = Leads.objects.filter(
        Q(name__icontains=query) |
        Q(email__icontains=query) |
        Q(phonenumber__icontains=query) |
        Q(district__icontains=query) |
        Q(place__icontains=query) |
        Q(purpose__icontains=query) |
        Q(mode_of_purpose__icontains=query) |
        Q(message__icontains=query) |
        Q(status__icontains=query) |
        Q(stage__icontains=query) |
        Q(follower__icontains=query)
    )

    if lead_results.exists():
        return JsonResponse({
            "source": "leads",
            "results": LeadsViewSerializer(lead_results, many=True).data
        })

    # 3️⃣ If no Leads results, search in Projects
    project_results = Project_db.objects.filter(
        Q(project_name__icontains=query) |
        Q(importance__icontains=query) |
        Q(description__icontains=query)
    )

    if project_results.exists():
        return JsonResponse({
            "source": "projects",
            "results": ProjectSerializer(project_results, many=True).data
        })

    # 4️⃣ If no matches found in any, return empty response
    return JsonResponse({"source": "none", "results": []})








@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSalesManagerUser])
def autocomplete_databank_salesmanager(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({"suggestions": []})

    staff = request.user
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    if not salesmanager:
        return JsonResponse({"error": "Not a valid sales manager"}, status=403)

    # Filter DataBank records where any field contains the query string (name, district, place)
    matches = DataBank.objects.filter(
        Q(name__icontains=query) | 
        Q(district__icontains=query) | 
        Q(place__icontains=query),
        follower=salesmanager
    ).values_list('name', 'district', 'place')

    suggestions = set()

    for name, district, place in matches:
        # Add only the parts that contain the query string
        if name and query.lower() in name.lower():
            suggestions.add(name)
        if district and query.lower() in district.lower():
            suggestions.add(district)
        if place and query.lower() in place.lower():
            suggestions.add(place)

    return JsonResponse({"suggestions": list(suggestions)})





@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def salesmanager_search_databank(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({"error": "Query parameter is required"}, status=400)
    staff = request.user

    # Check if the user is a sales manager
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    if not salesmanager:
        return Response({"error": "Not a valid sales manager"}, status=status.HTTP_403_FORBIDDEN)

    # 1️⃣ Search in Databank
    databank_results = DataBank.objects.filter(
        (Q(name__icontains=query) |
        Q(email__icontains=query) |
        Q(phonenumber__icontains=query) |
        Q(district__icontains=query) |
        Q(place__icontains=query) |
        Q(purpose__icontains=query) |
        Q(mode_of_property__icontains=query) |
        Q(demand_price__icontains=query) |
        Q(location_proposal_district__icontains=query) |
        Q(location_proposal_place__icontains=query) |
        Q(area_in_sqft__icontains=query) |
        Q(building_roof__icontains=query) |
        Q(number_of_floors__icontains=query) |
        Q(building_bhk__icontains=query) |
        Q(projects__project_name__icontains=query) |
        Q(projects__importance__icontains=query))&
        Q(follower=salesmanager)
    )

    if databank_results.exists():
        return JsonResponse({
            "source": "databank",
            "results": DataBankGETSerializer(databank_results, many=True).data
        })

    # 2️⃣ If no Databank results, search in Leads
    lead_results = Leads.objects.filter(
        (Q(name__icontains=query) |
        Q(email__icontains=query) |
        Q(phonenumber__icontains=query) |
        Q(district__icontains=query) |
        Q(place__icontains=query) |
        Q(purpose__icontains=query) |
        Q(mode_of_purpose__icontains=query) |
        Q(message__icontains=query) |
        Q(status__icontains=query) |
        Q(stage__icontains=query) |
        Q(follower__icontains=query))&
        Q(staff_id=salesmanager.id)
    )

    if lead_results.exists():
        return JsonResponse({
            "source": "leads",
            "results": LeadsViewSerializer(lead_results, many=True).data
        })

    # 3️⃣ If no Leads results, search in Projects
    project_results = Project_db.objects.filter(
        (Q(project_name__icontains=query) |
        Q(importance__icontains=query) |
        Q(description__icontains=query)) &
        Q(data_bank__follower=salesmanager)
    )

    if project_results.exists():
        return JsonResponse({
            "source": "projects",
            "results": ProjectSerializer(project_results, many=True).data
        })

    # 4️⃣ If no matches found in any, return empty response
    return JsonResponse({"source": "none", "results": []})








OPENCAGE_API_KEY = 'c445fce3f1b14cba8c08daafb182d5f3'  # Replace with your actual API key
geocoder = OpenCageGeocode(OPENCAGE_API_KEY)

def get_coordinates(place_name):
    try:
        query = f"{place_name}, Kerala, India"
        results = geocoder.geocode(query)
        if results and len(results):
            lat = results[0]['geometry']['lat']
            lng = results[0]['geometry']['lng']
            return (lat, lng)
        else:
            pass
    except Exception as e:
        pass
    return None





def extract_coordinates(link):
    if not link:
        return None
    try:
        # Split the string by comma to get latitude and longitude
        lat, lon = map(float, link.split(','))
        return lat, lon
    except ValueError:
        return None

OPENCAGE_API_KEY = 'c445fce3f1b14cba8c08daafb182d5f3'  # Replace with your real API key
geocoder = OpenCageGeocode(OPENCAGE_API_KEY)
# Function to geocode a place using Geopy (Nominatim)
def geocode_location(place_name):
    try:
        query = f"{place_name}, Kerala, India"
        results = geocoder.geocode(query)
        if results and len(results):
            lat = results[0]['geometry']['lat']
            lng = results[0]['geometry']['lng']
            return (lat, lng)
        else:
            pass
    except Exception as e:
        pass
    return None

@api_view(['GET'])
@permission_classes([AllowAny])
def filter_data_banks(request):
    queryset = DataBank.objects.all()
    filters = DataBankFilter(request.GET, queryset=queryset).qs

    district = request.GET.get('district')
    place = request.GET.get('location')
    distance_km = request.GET.get('distance_km')

    if distance_km and (place or district):
        try:
            distance_km = float(distance_km)

            # Try geocoding the place first, fallback to district
            base_coords = None
            if place:
                base_coords = geocode_location(place)
            if not base_coords and district:
                base_coords = geocode_location(district)
            if not base_coords:
                return Response({"error": "Could not geocode the provided place or district."}, status=status.HTTP_400_BAD_REQUEST)

            filtered_ids = []
            for obj in filters:
                coords = extract_coordinates(obj.location_link)
                if coords:
                    dist = geodesic(base_coords, coords).km
                    if dist <= distance_km:
                        filtered_ids.append(obj.id)

            filters = filters.filter(id__in=filtered_ids)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    serializer = DataBankGETSerializer(filters, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)








@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_matching_pdf(request, property_id):
    try:
        new_property = get_object_or_404(DataBank, id=property_id)

        opposite_purpose_map = {
            "For Selling a Property": "For Buying a Property",
            "For Buying a Property": "For Selling a Property",
            "For Rental or Lease": "Looking to Rent or Lease a Property",
            "Looking to Rent or Lease Property": "For Rental or Lease",
        }
        opposite_purpose = opposite_purpose_map.get(new_property.purpose, None)

        potential_matches = DataBank.objects.filter(
            purpose=opposite_purpose,
            mode_of_property=new_property.mode_of_property,
        )

        if not potential_matches.exists():
            potential_matches = DataBank.objects.filter(
                purpose=opposite_purpose,
                mode_of_property__in=["other", new_property.mode_of_property],
            )

        new_coords = get_coordinates(
            new_property.location_proposal_place if new_property.purpose in ["For Buying a Property", "Looking to Rent or Lease Property"]
            else new_property.place
        )

        ranked_matches = []
        for match in potential_matches:
            score = 0

            if match.mode_of_property == new_property.mode_of_property:
                score += 4

            # District and Place match
            if new_property.purpose in ["For Buying a Property", "Looking to Rent or Lease Property"]:
                if match.district == new_property.location_proposal_district:
                    score += 3
                if match.place and new_property.location_proposal_place and match.place.lower() == new_property.location_proposal_place.lower():
                    score += 2
                match_coords = get_coordinates(match.place)
            else:
                if match.location_proposal_district == new_property.district:
                    score += 3
                if match.location_proposal_place and new_property.place and match.location_proposal_place.lower() == new_property.place.lower():
                    score += 2
                match_coords = get_coordinates(match.location_proposal_place)

            # Geo Distance Bonus (Closer = Higher Score)
            if new_coords and match_coords:
                try:
                    distance_km = geodesic(new_coords, match_coords).km
                    if distance_km <= 5:
                        score += 5
                    elif distance_km <= 10:
                        score += 3
                    elif distance_km <= 20:
                        score += 1
                except:
                    pass

            if match.demand_price and new_property.demand_price:
                if match.demand_price * 0.9 <= new_property.demand_price <= match.demand_price * 1.1:
                    score += 5

            if match.area_in_sqft == new_property.area_in_sqft:
                score += 2
            if match.building_bhk and new_property.building_bhk and match.building_bhk == new_property.building_bhk:
                score += 2
            if match.number_of_floors and new_property.number_of_floors and match.number_of_floors == new_property.number_of_floors:
                score += 1

            if match.building_roof == new_property.building_roof:
                score += 1

            if score > 0:
                ranked_matches.append((score, match))

        ranked_matches.sort(reverse=True, key=lambda x: x[0])

        if not ranked_matches:
            ground_staff_emails = Ground_level_managers_reg.objects.values_list("email", flat=True)
            if ground_staff_emails:
                subject = "⚠️ No Matches Found for New Property"
                message = (
                    f"A new property (ID: {new_property.id}, Purpose: {new_property.purpose}, Type: {new_property.mode_of_property}) "
                    f"has been added, but no matching properties were found."
                )
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, list(ground_staff_emails), fail_silently=True)

            return Response(
                {"message": "⚠️ No matching properties found! Email notification sent to Ground-Level Staff."},
                status=status.HTTP_200_OK,
            )

        # === PDF Generation ===
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=50, bottomMargin=50, leftMargin=40, rightMargin=40)
        styles = getSampleStyleSheet()
        content = []

        # --- Header with Logo and Background ---
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'devicon.jpg')  # <-- Update this to the correct path of your logo
        logo = RLImage(logo_path, width=80, height=80)  # Resize as needed

        header_main_style = ParagraphStyle(
            name='HeaderMain',
            fontSize=16,
            textColor=colors.white,
            alignment=TA_CENTER,
        )

        header_sub_style = ParagraphStyle(
            name='HeaderSub',
            fontSize=8,
            textColor=colors.white,
            alignment=TA_CENTER,
        )

        header_data = [[
            logo,
            Paragraph("<b>DEVELOK DEVELOPERS</b><br/>Thrissur, Kerala<br/> 9846845777 | 9645129777<br/> info@devlokdevelopers.com |  www.devlokdevelopers.com", header_sub_style)
        ]]

        header_table = Table(header_data, colWidths=[60, 450])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#0564BC")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        content.append(header_table)
        content.append(Spacer(1, 12))

        # Custom styles for the content
        normal_style = ParagraphStyle(name='Normal', fontSize=10, leading=14)
        footer_style = ParagraphStyle(name='Footer', fontSize=8, textColor=colors.grey, alignment=TA_CENTER)

        # Intro text
        intro = (
            "We are excited to present a curated list of properties that closely match your preferences. "
            "Here are our top picks based on your recent property entry:"
        )
        content.append(Paragraph(intro, normal_style))
        content.append(Spacer(1, 20))

        # Matching Properties section
        for score, prop in ranked_matches[:5]:
            details = f"""
            <b>District:</b> {prop.district} &nbsp;&nbsp; <b>Place:</b> {prop.place}<br/>
            <b>Purpose:</b> {prop.purpose} &nbsp;&nbsp; <b>Type:</b> {prop.mode_of_property}<br/>
            <b>Price:</b> {prop.demand_price} &nbsp;&nbsp; <b>Area:</b> {prop.area_in_sqft} sqft<br/>
            <b>BHK:</b> {prop.building_bhk or 'N/A'} &nbsp;&nbsp; <b>Floors:</b> {prop.number_of_floors or 'N/A'}<br/>
            <b>Roof Type:</b> {prop.building_roof or 'N/A'}<br/>
            <b>Additional Notes:</b> {prop.additional_note or 'None'}
            """
            content.append(Paragraph(details, normal_style))
            content.append(Spacer(1, 6))            

            content.append(Spacer(1, 12))
            content.append(Table([[" " * 150]], style=[("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.grey)]))
            content.append(Spacer(1, 12))

        content.append(Spacer(1, 10))
        content.append(Paragraph("Generated by <b>DEVELOK DEVELOPERS Matching Engine</b>", footer_style))

        # Watermark function
        def add_watermark(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica-Bold', 60)
            canvas.setFillColorRGB(0.9, 0.9, 0.9, alpha=0.2)
            canvas.translate(300, 400)
            canvas.rotate(45)
            canvas.drawCentredString(0, 0, "DEVELOK DEVELOPERS")
            canvas.restoreState()

        # Build the document with watermark on every page
        doc.build(content, onFirstPage=add_watermark, onLaterPages=add_watermark)

        buffer.seek(0)


        # === Email with PDF attachment ===
        subject = f"Matching Properties PDF for Property ID {property_id}"
        body = "Hello,\n\nPlease find the attached PDF with top matching properties."
        to_email = new_property.email

        if not to_email:
            return Response({"error": "Client email not found."}, status=400)

        email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [to_email])
        email.attach(f"matching_properties_{property_id}.pdf", buffer.read(), "application/pdf")
        email.send(fail_silently=False)

        return Response({"message": "Matching properties PDF sent to client successfully."})

    except Exception as e:
        return Response({"error": str(e)}, status=500)










@api_view(['GET'])
@permission_classes([AllowAny])
def match_property(request, property_id):
    try:
        new_property = get_object_or_404(DataBank, id=property_id)

        opposite_purpose_map = {
            "For Selling a Property": "For Buying a Property",
            "For Buying a Property": "For Selling a Property",
            "For Rental or Lease": "Looking to Rent or Lease a Property",
            "Looking to Rent or Lease Property": "For Rental or Lease",
        }
        opposite_purpose = opposite_purpose_map.get(new_property.purpose, None)

        potential_matches = DataBank.objects.filter(
            purpose=opposite_purpose,
            mode_of_property=new_property.mode_of_property,
        )

        if not potential_matches.exists():
            potential_matches = DataBank.objects.filter(
                purpose=opposite_purpose,
                mode_of_property__in=["other", new_property.mode_of_property],
            )

        new_coords = get_coordinates(
            new_property.location_proposal_place if new_property.purpose in ["For Buying a Property", "Looking to Rent or Lease Property"]
            else new_property.place
        )

        ranked_matches = []
        for match in potential_matches:
            score = 0

            if match.mode_of_property == new_property.mode_of_property:
                score += 4

            # District and Place match
            if new_property.purpose in ["For Buying a Property", "Looking to Rent or Lease Property"]:
                if match.district == new_property.location_proposal_district:
                    score += 3
                if match.place and new_property.location_proposal_place and match.place.lower() == new_property.location_proposal_place.lower():
                    score += 2
                match_coords = get_coordinates(match.place)
            else:
                if match.location_proposal_district == new_property.district:
                    score += 3
                if match.location_proposal_place and new_property.place and match.location_proposal_place.lower() == new_property.place.lower():
                    score += 2
                match_coords = get_coordinates(match.location_proposal_place)

            # Geo Distance Bonus (Closer = Higher Score)
            if new_coords and match_coords:
                try:
                    distance_km = geodesic(new_coords, match_coords).km
                    if distance_km <= 5:
                        score += 5
                    elif distance_km <= 10:
                        score += 3
                    elif distance_km <= 20:
                        score += 1
                except:
                    pass

            if match.demand_price and new_property.demand_price:
                if match.demand_price * 0.9 <= new_property.demand_price <= match.demand_price * 1.1:
                    score += 5

            if match.area_in_sqft == new_property.area_in_sqft:
                score += 2
            if match.building_bhk and new_property.building_bhk and match.building_bhk == new_property.building_bhk:
                score += 2
            if match.number_of_floors and new_property.number_of_floors and match.number_of_floors == new_property.number_of_floors:
                score += 1

            if match.building_roof == new_property.building_roof:
                score += 1

            if score > 0:
                ranked_matches.append((score, match))

        ranked_matches.sort(reverse=True, key=lambda x: x[0])

        if ranked_matches:
            serialized_matches = [
                {"score": score, "data": DataBankGETSerializer(match).data}
                for score, match in ranked_matches
            ]
            return Response(
                {"total_matches": len(ranked_matches), "matches": serialized_matches},
                status=200
            )

        ground_staff_emails = Ground_level_managers_reg.objects.values_list("email", flat=True)
        if ground_staff_emails:
            subject = "⚠️ No Matches Found for New Property"
            message = (
                f"A new property has been added but no matching properties were found.\n\n"
                f"--- Property Details ---\n"
                f"ID: {new_property.id}\n"
                f"Name: {new_property.name}\n"
                f"Phone: {new_property.phonenumber}\n"
                f"Email: {new_property.email}\n"
                f"Purpose: {new_property.purpose}\n"
                f"Type: {new_property.mode_of_property}\n"
                f"District: {new_property.district}\n"
                f"Place: {new_property.place}\n"
                f"Address: {new_property.address}\n"
                f"Demand Price: {new_property.demand_price}\n"
                f"Proposal District: {new_property.location_proposal_district}\n"
                f"Proposal Place: {new_property.location_proposal_place}\n"
                f"Area: {new_property.area_in_sqft}\n"
                f"BHK: {new_property.building_bhk}\n"
                f"Floors: {new_property.number_of_floors}\n"
                f"Roof Type: {new_property.building_roof}\n"
                f"Location Link: {new_property.location_link}\n"
                f"Additional Note: {new_property.additional_note}\n"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                list(ground_staff_emails),
                fail_silently=True
            )

        return Response(
            {"message": "⚠️ No matching properties found! Email notification sent to Ground-Level Staff."},
            status=200
        )

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
    
    

@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def lead_into_databank(request,lead_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    databank = DataBank.objects.filter(lead_id=lead_id)
    serializer = DataBankGETSerializer(databank,many=True).data
    return Response(serializer,status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def databank_graph(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    total_datas = DataBank.objects.all().count()
    for_buy = DataBank.objects.filter(purpose='For Buying a Property').count()
    for_sell = DataBank.objects.filter(purpose='For Selling a Property').count()
    for_rent = DataBank.objects.filter(purpose='For Rental or Lease').count()
    rental_seeker = DataBank.objects.filter(purpose='Looking to Rent or Lease Property').count()

    response_data = {
        "total_collections": total_datas,
        "sell": for_sell,
        "buy": for_buy,
        "for_rental": for_rent,
        "rental_seeker": rental_seeker
    }
    return Response(response_data, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def Buy_databank(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    buy_list = DataBank.objects.filter(purpose = "For Buying a Property")
    serializer = DataBankGETSerializer(buy_list,many=True).data
    return Response(serializer,status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def Sell_databank(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    buy_list = DataBank.objects.filter(purpose = "For Selling a Property")
    serializer = DataBankGETSerializer(buy_list,many=True).data
    return Response(serializer,status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def ForRent_databank(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    buy_list = DataBank.objects.filter(purpose = "For Rental or Lease")
    serializer = DataBankGETSerializer(buy_list,many=True).data
    return Response(serializer,status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def RentSeeker_databank(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    buy_list = DataBank.objects.filter(purpose = "Looking to Rent or Lease Property")
    serializer = DataBankGETSerializer(buy_list,many=True).data
    return Response(serializer,status=200)




@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def SalesM_Buy_databank(request):
    staff = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    buy_list = DataBank.objects.filter(purpose = "For Buying a Property",follower=salesmanager)
    serializer = DataBankGETSerializer(buy_list,many=True).data
    return Response(serializer,status=200)



@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def SalesM_Sell_databank(request):
    staff = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    sell_list = DataBank.objects.filter(purpose = "For Selling a Property",follower=salesmanager)
    serializer = DataBankGETSerializer(sell_list,many=True).data
    return Response(serializer,status=200)




@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def SalesM_ForRent_databank(request):
    staff = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    rental_list = DataBank.objects.filter(purpose = "For Rental or Lease",follower=salesmanager)
    serializer = DataBankGETSerializer(rental_list,many=True).data
    return Response(serializer,status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def SalesM_RentSeeker_databank(request):
    staff = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    seeker_list = DataBank.objects.filter(purpose = "Looking to Rent or Lease Property",follower=salesmanager)
    serializer = DataBankGETSerializer(seeker_list,many=True).data
    return Response(serializer,status=200)




@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def single_databank(request,databank_id):
    staff = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    databank = DataBank.objects.filter(id=databank_id,follower=salesmanager)
    serializer = DataBankGETSerializer(databank,many=True).data
    return Response(serializer,status=status.HTTP_200_OK)




@api_view(['POST'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def add_image_databank(request,databank_id):
    staff = request.user

    # Check if the user is a sales manager
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    if not salesmanager:
        return Response({"error": "Not a valid sales manager"}, status=status.HTTP_403_FORBIDDEN)

    # Retrieve the databank entry
    try:
        databank = DataBank.objects.get(id=databank_id, follower=salesmanager)
    except DataBank.DoesNotExist:
        return Response({"error": "Databank not available or unauthorized access"}, status=status.HTTP_404_NOT_FOUND)

    # Check if images are present in the request
    images = request.FILES.getlist('photos')  # `getlist` handles multiple images
    if not images:
        return Response({"error": "No images provided"}, status=status.HTTP_400_BAD_REQUEST)

    # Save images
    image_instances = []
    for image in images:
        img_instance = DataBankImage(databank=databank, image=image)
        img_instance.save()
        image_instances.append(img_instance)

    serializer = DataBankImageSerializer(image_instances, many=True)
    return Response(serializer.data, status=status.HTTP_201_CREATED)




@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def view_images_databank(request, databank_id):
    staff = request.user

    # Check if the user is a sales manager
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    if not salesmanager:
        return Response({"error": "Not a valid sales manager"}, status=status.HTTP_403_FORBIDDEN)

    # Retrieve the databank entry
    try:
        databank = DataBank.objects.get(id=databank_id, follower=salesmanager)
    except DataBank.DoesNotExist:
        return Response({"error": "Databank not available or unauthorized access"}, status=status.HTTP_404_NOT_FOUND)

    # Fetch all images for the given databank
    images = DataBankImage.objects.filter(databank=databank)
    if not images.exists():
        return Response({"message": "No images available for this databank"}, status=status.HTTP_404_NOT_FOUND)

    # Serialize and return image data
    serializer = DataBankImageSerializer(images, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)




@api_view(['DELETE'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def delete_image(request, databank_id, image_id):
    staff = request.user

    # Check if the user is a sales manager
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    if not salesmanager:
        return Response({"error": "Not a valid sales manager"}, status=status.HTTP_403_FORBIDDEN)

    # Check if the databank exists and belongs to the sales manager
    try:
        databank = DataBank.objects.get(id=databank_id, follower=salesmanager)
    except DataBank.DoesNotExist:
        return Response({"error": "Databank not available or unauthorized access"}, status=status.HTTP_404_NOT_FOUND)

    # Retrieve the image
    image = get_object_or_404(DataBankImage, id=image_id, databank=databank)

    # Delete the image
    image.delete()
    
    return Response({"message": "Image deleted successfully"}, status=status.HTTP_200_OK)











@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def lead_into_databank_salesmanager(request,lead_id):
    staff = request.user

    # Check if the user is a sales manager
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    if not salesmanager:
        return Response({"error": "Not a valid sales manager"}, status=status.HTTP_403_FORBIDDEN)
    databank = DataBank.objects.filter(lead_id=lead_id)
    serializer = DataBankGETSerializer(databank,many=True).data
    return Response(serializer,status=status.HTTP_200_OK)








@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def salesmanager_databank_graph(request):
    staff = request.user

    # Check if the user is a sales manager
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    if not salesmanager:
        return Response({"error": "Not a valid sales manager"}, status=status.HTTP_403_FORBIDDEN)
    total_datas = DataBank.objects.filter(follower=salesmanager).count()
    for_buy = DataBank.objects.filter(follower=salesmanager, purpose='For Buying a Property').count()
    for_sell = DataBank.objects.filter(follower=salesmanager, purpose='For Selling a Property').count()
    for_rent = DataBank.objects.filter(follower=salesmanager, purpose='For Rental or Lease').count()
    rental_seeker = DataBank.objects.filter(follower=salesmanager, purpose='Looking to Rent or Lease Property').count()

    response_data = {
        "total_collections": total_datas,
        "sell": for_sell,
        "buy": for_buy,
        "for_rental": for_rent,
        "rental_seeker": rental_seeker
    }
    return Response(response_data, status=200)




@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def admin_single_databank(request,databank_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    
    databank = DataBank.objects.filter(id=databank_id)
    serializer = DataBankGETSerializer(databank,many=True).data
    return Response(serializer,status=status.HTTP_200_OK)





@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def admin_view_images_databank(request, databank_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    # Retrieve the databank entry
    try:
        databank = DataBank.objects.get(id=databank_id)
    except DataBank.DoesNotExist:
        return Response({"error": "Databank not available or unauthorized access"}, status=status.HTTP_404_NOT_FOUND)

    # Fetch all images for the given databank
    images = DataBankImage.objects.filter(databank=databank)
    if not images.exists():
        return Response({"message": "No images available for this databank"}, status=status.HTTP_404_NOT_FOUND)

    # Serialize and return image data
    serializer = DataBankImageSerializer(images, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)




@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def lead_into_databank_admin(request, lead_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    # Use select_related for optimized fetching of related fields (follower, etc.)
    databank = DataBank.objects.filter(lead_id=lead_id).select_related('follower').only('id', 'follower__username', 'timestamp', 'name', 'email', 'phonenumber', 'district', 'place', 'address', 'purpose', 'mode_of_property', 'demand_price', 'location_proposal_district', 'location_proposal_place', 'area_in_sqft', 'building_roof', 'number_of_floors', 'building_bhk', 'additional_note', 'lead_category', 'location_link', 'image_folder')
    
    # If you have related projects, use prefetch_related (for many-to-many relationships)
    # Example: prefetch_related('projects') if you have a many-to-many relationship with projects
    # databank = databank.prefetch_related(Prefetch('projects')).only('id', 'projects__project_name')

    # Serialize the data
    serializer = DataBankGETSerializer(databank, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)








@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def Databank_List_admin(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    databank = DataBank.objects.filter(lead__stage__in=['Not Opened','Data Saved'])
    serializer = DataBankGETSerializer(databank,many=True).data
    return Response(serializer,status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def Databank(request):
    admin = request.user

    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    # Databank list
    databank_list = DataBank.objects.all()
    serializer = DataBankGETSerializer(databank_list, many=True)

    # Analytics data
    total_datas = databank_list.count()
    for_buy = databank_list.filter(purpose='For Buying a Property').count()
    for_sell = databank_list.filter(purpose='For Selling a Property').count()
    for_rent = databank_list.filter(purpose='For Rental or Lease').count()
    rental_seeker = databank_list.filter(purpose='Looking to Rent or Lease Property').count()

    analytics = {
        "total_collections": total_datas,
        "buy": for_buy,
        "sell": for_sell,
        "for_rental": for_rent,
        "rental_seeker": rental_seeker,
    }

    return Response({
        "databank": serializer.data,
        "analytics": analytics
    }, status=200)
