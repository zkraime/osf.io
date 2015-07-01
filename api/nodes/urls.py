from django.conf.urls import url

from api.nodes import views

urlpatterns = [
    # Examples:
    # url(r'^$', 'api.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', views.NodeList.as_view(), name='node-list'),
    url(r'^(?P<node_id>\w+)/$', views.NodeDetail.as_view(), name='node-detail'),
    url(r'^(?P<node_id>\w+)/contributors/$', views.NodeContributorsList.as_view(), name='node-contributors'),
    url(r'^(?P<node_id>\w+)/registrations/$', views.NodeRegistrationsList.as_view(), name='node-registrations'),
    url(r'^(?P<node_id>\w+)/children/$', views.NodeChildrenList.as_view(), name='node-children'),
    url(r'^(?P<node_id>\w+)/pointers/$', views.NodePointersList.as_view(), name='node-pointers'),
    url(r'^(?P<node_id>\w+)/files/$', views.NodeFilesList.as_view(), name='node-files'),
    url(r'^(?P<node_id>\w+)/pointers/(?P<pointer_id>\w+)', views.NodePointerDetail.as_view(), name='node-pointer-detail'),
]
