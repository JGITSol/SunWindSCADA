from django.urls import path
from rest_framework.routers import DefaultRouter

from . import api
from .views import (GridComplianceCheckViewSet, ScenarioViewSet,
                    TurbineMeasurementViewSet, WeatherDataViewSet,
                    WindTurbineViewSet)

router = DefaultRouter()
router.register(r"turbines", WindTurbineViewSet)
router.register(r"weather", WeatherDataViewSet)
router.register(r"measurements", TurbineMeasurementViewSet)
router.register(r"scenarios", ScenarioViewSet)
router.register(r"compliance", GridComplianceCheckViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = router.urls

# Add the new hello_world endpoint
urlpatterns.append(
    path('hello/', api.hello_world, name='hello_world')
)
