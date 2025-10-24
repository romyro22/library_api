from django.urls import path, include
from adrf.routers import DefaultRouter
from .views import AuthorViewSet, BookViewSet


router = DefaultRouter()

router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'books', BookViewSet, basename='book')


app_name = 'books'

urlpatterns = [
    path('', include(router.urls)),
]
