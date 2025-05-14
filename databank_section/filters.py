import django_filters
from .models import DataBank

class DataBankFilter(django_filters.FilterSet):
    district = django_filters.CharFilter(lookup_expr='icontains')
    place = django_filters.CharFilter(lookup_expr='icontains')
    purpose = django_filters.CharFilter(lookup_expr='icontains')
    mode_of_property = django_filters.CharFilter(lookup_expr='icontains')
    demand_price_min = django_filters.NumberFilter(field_name="demand_price", lookup_expr='gte')
    demand_price_max = django_filters.NumberFilter(field_name="demand_price", lookup_expr='lte')
    location_proposal_district = django_filters.CharFilter(lookup_expr='icontains')
    location_proposal_place = django_filters.CharFilter(lookup_expr='icontains')
    follower = django_filters.CharFilter(field_name="follower__username", lookup_expr='icontains')  # Search by follower's name
    timestamp = django_filters.DateFromToRangeFilter()  # Allows filtering by date range
    area_in_sqft_min = django_filters.NumberFilter(field_name="area_in_sqft", lookup_expr='gte')
    area_in_sqft_max = django_filters.NumberFilter(field_name="area_in_sqft", lookup_expr='lte')
    lead_category = django_filters.CharFilter(lookup_expr='icontains')
    building_roof = django_filters.CharFilter(lookup_expr='icontains')
    number_of_floors_min = django_filters.NumberFilter(field_name="number_of_floors", lookup_expr='gte')
    number_of_floors_max = django_filters.NumberFilter(field_name="number_of_floors", lookup_expr='lte')

    building_bhk = django_filters.NumberFilter(field_name="building_bhk")
   

    class Meta:
        model = DataBank
        fields = [
            'district', 'purpose', 'mode_of_property', 'demand_price', 
            'location_proposal_district', 'location_proposal_place', 'follower', 'timestamp',
            'area_in_sqft_min', 'area_in_sqft_max', 'building_roof',
            'number_of_floors_min', 'number_of_floors_max', 'building_bhk', 
        ]
