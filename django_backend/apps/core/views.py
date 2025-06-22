from datetime import timedelta

from django.utils import timezone
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (GridComplianceCheck, Scenario, TurbineMeasurement,
                     WeatherData, WindTurbine)
from .serializers import (GridComplianceCheckDetailSerializer,
                          GridComplianceCheckSerializer, ScenarioSerializer,
                          TurbineMeasurementDetailSerializer,
                          TurbineMeasurementSerializer, WeatherDataSerializer,
                          WindTurbineSerializer)


class WindTurbineViewSet(viewsets.ModelViewSet):
    """
    API endpoint for wind turbines.
    """

    queryset = WindTurbine.objects.all()
    serializer_class = WindTurbineSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "status"]
    ordering_fields = ["name", "nominal_power", "status"]

    @action(detail=True, methods=["get"])
    def measurements(self, request, pk=None):
        """Get recent measurements for a specific turbine"""
        turbine = self.get_object()
        since = request.query_params.get("since", "1h")

        # Parse time filter
        if since.endswith("h"):
            hours = int(since[:-1])
            since_time = timezone.now() - timedelta(hours=hours)
        elif since.endswith("d"):
            days = int(since[:-1])
            since_time = timezone.now() - timedelta(days=days)
        else:
            since_time = timezone.now() - timedelta(hours=1)

        measurements = TurbineMeasurement.objects.filter(
            turbine=turbine, timestamp__gte=since_time
        ).order_by("-timestamp")

        serializer = TurbineMeasurementSerializer(measurements, many=True)
        return Response(serializer.data)


class WeatherDataViewSet(viewsets.ModelViewSet):
    """
    API endpoint for weather data.
    """

    queryset = WeatherData.objects.all().order_by("-timestamp")
    serializer_class = WeatherDataSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["timestamp"]

    @action(detail=False, methods=["get"])
    def recent(self, request):
        """Get most recent weather data"""
        recent = WeatherData.objects.order_by("-timestamp").first()
        serializer = self.get_serializer(recent)
        return Response(serializer.data)


class TurbineMeasurementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for turbine measurements.
    """

    queryset = TurbineMeasurement.objects.all().order_by("-timestamp")
    serializer_class = TurbineMeasurementSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["turbine__name"]
    ordering_fields = ["timestamp", "power_output", "wind_speed"]

    def get_serializer_class(self):
        if self.action == "retrieve" or self.action == "list":
            return TurbineMeasurementDetailSerializer
        return TurbineMeasurementSerializer

    @action(detail=False, methods=["get"])
    def latest(self, request):
        """Get latest measurements for all turbines"""
        # Get distinct turbine IDs
        turbine_ids = TurbineMeasurement.objects.values_list(
            "turbine", flat=True
        ).distinct()

        # For each turbine, get the latest measurement
        latest_measurements = []
        for turbine_id in turbine_ids:
            measurement = (
                TurbineMeasurement.objects.filter(turbine_id=turbine_id)
                .order_by("-timestamp")
                .first()
            )

            if measurement:
                latest_measurements.append(measurement)

        serializer = TurbineMeasurementDetailSerializer(latest_measurements, many=True)
        return Response(serializer.data)


class ScenarioViewSet(viewsets.ModelViewSet):
    """
    API endpoint for simulation scenarios.
    """

    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "scenario_type"]
    ordering_fields = ["name", "active"]

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate a scenario and deactivate all others"""
        scenario = self.get_object()

        # Deactivate all other scenarios
        Scenario.objects.all().update(active=False)

        # Activate this scenario
        scenario.active = True
        scenario.save()

        return Response({"status": "Scenario activated"})


class GridComplianceCheckViewSet(viewsets.ModelViewSet):
    """
    API endpoint for grid compliance checks.
    """

    queryset = GridComplianceCheck.objects.all().order_by("-timestamp")
    serializer_class = GridComplianceCheckSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["turbine__name", "check_type", "compliant"]
    ordering_fields = ["timestamp", "check_type", "compliant"]

    def get_serializer_class(self):
        if self.action == "retrieve" or self.action == "list":
            return GridComplianceCheckDetailSerializer
        return GridComplianceCheckSerializer
