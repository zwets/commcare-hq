from django.conf.urls import url

from corehq.apps.integration.views import (
    BiometricIntegrationView,
    dialer_view,
    DialerSettingsView,
    gaen_otp_view,
    GaenOtpServerSettingsView,
    HmacCalloutSettingsView,
)
from corehq.apps.reports.views import TableauServerView

settings_patterns = [
    url(r'^biometric/$', BiometricIntegrationView.as_view(),
        name=BiometricIntegrationView.urlname),
    url(r'^dialer/$', DialerSettingsView.as_view(), name=DialerSettingsView.urlname),
    url(r'^signed_callout/$', HmacCalloutSettingsView.as_view(), name=HmacCalloutSettingsView.urlname),
    url(r'^gaen_otp_server/$', GaenOtpServerSettingsView.as_view(), name=GaenOtpServerSettingsView.urlname),
    url(r'^tableau_server/$', TableauServerView.as_view(), name=TableauServerView.urlname),
]

urlpatterns = [
    url(r'dialer/$', dialer_view, name="dialer_view"),
    url(r'gaen_otp/$', gaen_otp_view, name="gaen_otp_view"),
]
