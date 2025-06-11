from rest_framework.routers import DefaultRouter
from .views import (
    WindTurbineViewSet, 
    WeatherDataViewSet, 
    TurbineMeasurementViewSet, 
    ScenarioViewSet,
    GridComplianceCheckViewSet
)

router = DefaultRouter()
router.register(r'turbines', WindTurbineViewSet)
router.register(r'weather', WeatherDataViewSet)
router.register(r'measurements', TurbineMeasurementViewSet)
router.register(r'scenarios', ScenarioViewSet)
router.register(r'compliance', GridComplianceCheckViewSet)

urlpatterns = router.urls
