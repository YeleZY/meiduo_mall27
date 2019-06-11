from django.conf.urls import url, include
from contents import views
urlpatterns = [
    url(r'^$', views.IndexView.as_view()),
]
