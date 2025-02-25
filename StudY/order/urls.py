from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from .views import *
from rest_framework import routers

router = routers.SimpleRouter()

order_actions = OrderExecutorActionsViewSet.as_view({
    'post': 'accept_order'
})

order_reject = OrderExecutorActionsViewSet.as_view({
    'post': 'reject_order'
})

order_edit = OrderExecutorActionsViewSet.as_view({
    'patch': 'edit_order'
})

order_confirm = OrderCustomerActionsViewSet.as_view({
    'post': 'confirm_order'
})

router.register(r'views-discipline', OrderDisciplinesViewSet, basename='views-discipline')
router.register(r'views-executors', ExecutorDisciplineViewSet, basename='views-executor'),
router.register(r'executor-disciplines', ExecutorSelfDisciplineViewSet, basename='executor-discipline'),
router.register(r'list-orders', ExecutorCustomerOrderViewSet, basename='executor-orders')


urlpatterns = [
                  path('', include(router.urls)),
                  path('create-executor-disciplines/', ExecutorDisciplineCreateView.as_view(),
                       name='create-executor-disciplines'),
                  path('create-personal-order/', OrderPersonalCreateView.as_view(), name='create-order'),

                  path('orders/<int:order_id>/accept/', order_actions, name='accept_order'),
                  path('orders/<int:order_id>/reject/', order_reject, name='reject_order'),
                  path('orders/<int:order_id>/edit/', order_edit, name='edit_order'),
                  path('orders/<int:order_id>/confirm/', order_confirm, name='confirm_order'),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
