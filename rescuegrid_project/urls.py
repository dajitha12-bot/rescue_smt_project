from django.contrib import admin
from django.urls import path
from core import views as core_views
from core import dashboard_views
from core import api_views
from emergencies import views as emergency_views
from relief import views as relief_views
from gdacs_integration import views as gdacs_views
from analytics_app import views as analytics_views
from notifications_app import views as notif_views

urlpatterns = [
    # Django Admin
    path('django-admin/', admin.site.urls),

    # Authentication & Profile
    path('', core_views.dashboard_redirect, name='index'),
    path('login/', core_views.login_view, name='login'),
    path('register/', core_views.register_view, name='register'),
    path('logout/', core_views.logout_view, name='logout'),
    path('dashboard/', core_views.dashboard_redirect, name='dashboard_redirect'),
    path('profile/', core_views.user_profile, name='user_profile'),

    # Role Dashboards
    path('dashboard/admin/', dashboard_views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/user/', dashboard_views.user_dashboard, name='user_dashboard'),
    path('dashboard/donor/', relief_views.donor_dashboard, name='donor_dashboard'),

    # User & Hospital Flows
    path('emergencies/request/', emergency_views.request_help, name='request_help'),
    path('emergencies/my-requests/', emergency_views.my_requests, name='my_requests'),
    path('emergencies/track/<str:tracking_code>/', emergency_views.request_detail, name='request_detail'),
    path('emergencies/update-status/<str:tracking_code>/', emergency_views.update_request_status, name='update_request_status'),
    path('facilities/hospitals/', relief_views.user_hospitals, name='user_hospitals'),
    path('facilities/shelters/', relief_views.user_shelters, name='user_shelters'),
    path('map/user/', dashboard_views.user_map, name='user_map'),

    # Donor Flows
    path('donor/needs/', relief_views.donor_needs, name='donor_needs'),
    path('donor/donate/', relief_views.donor_donate, name='donor_donate'),
    path('donor/my-donations/', relief_views.donor_my_donations, name='donor_my_donations'),

    # Admin Operations Flow
    path('admin/emergencies/', dashboard_views.admin_emergencies, name='admin_emergencies'),
    path('admin/map/', dashboard_views.admin_map, name='admin_map'),
    path('admin/gdacs/', gdacs_views.gdacs_events_list, name='admin_gdacs'),
    path('admin/resources/', relief_views.admin_resources, name='admin_resources'),
    path('admin/donations/', relief_views.admin_donations, name='admin_donations'),
    path('admin/donations/update/<str:tracking_code>/', relief_views.admin_update_donation_status, name='admin_update_donation_status'),
    path('admin/facilities/', relief_views.admin_facilities, name='admin_facilities'),
    path('admin/responders/', relief_views.admin_responders, name='admin_responders'),
    path('admin/database-records/', dashboard_views.admin_database_records, name='admin_database_records'),

    # Analytics & Documented Algorithms
    path('analytics/', analytics_views.analytics_dashboard, name='analytics_dashboard'),

    # Notifications Flow
    path('notifications/', notif_views.notifications_list, name='notifications_list'),
    path('notifications/read/<int:notification_id>/', notif_views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', notif_views.mark_all_read, name='mark_all_read'),

    # APIs for Dynamic Maps & Sync
    path('api/gdacs/sync/', gdacs_views.trigger_gdacs_sync, name='api_gdacs_sync'),
    path('api/gdacs/geojson/', gdacs_views.api_gdacs_geojson, name='api_gdacs_geojson'),
    path('api/map/layers/', api_views.api_map_layers, name='api_map_layers'),
]
