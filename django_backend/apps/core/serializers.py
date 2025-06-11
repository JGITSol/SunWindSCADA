from rest_framework import serializers
from .models import WindTurbine, WeatherData, TurbineMeasurement, Scenario, GridComplianceCheck

class WindTurbineSerializer(serializers.ModelSerializer):
    class Meta:
        model = WindTurbine
        fields = '__all__'

class WeatherDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherData
        fields = '__all__'

class TurbineMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = TurbineMeasurement
        fields = '__all__'
        
class TurbineMeasurementDetailSerializer(serializers.ModelSerializer):
    turbine = WindTurbineSerializer(read_only=True)
    
    class Meta:
        model = TurbineMeasurement
        fields = '__all__'

class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = '__all__'

class GridComplianceCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = GridComplianceCheck
        fields = '__all__'
        
class GridComplianceCheckDetailSerializer(serializers.ModelSerializer):
    turbine = WindTurbineSerializer(read_only=True)
    
    class Meta:
        model = GridComplianceCheck
        fields = '__all__'
