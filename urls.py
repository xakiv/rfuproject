

from django.conf.urls.defaults import *
from router import mapping
import views

urlpatterns = patterns('',
    (r'^$', views.index),
    mapping(r'^document/(?P<document_id>[A-Za-z0-9]+)/$', 'single_document',
            views.single_document_get, views.single_document_post),
)


