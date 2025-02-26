from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _

from corehq import toggles
from corehq.apps.domain.decorators import login_required
from corehq.apps.domain.views.base import BaseDomainView
from corehq.apps.hqwebapp.decorators import use_bootstrap5
from corehq.apps.hqwebapp.tables.pagination import SelectablePaginatedTableView
from corehq.apps.integration.kyc.forms import KycConfigureForm
from corehq.apps.integration.kyc.models import KycConfig
from corehq.apps.integration.kyc.services import (
    get_user_data_for_api,
    verify_users,
)
from corehq.apps.integration.kyc.tables import KycVerifyTable
from corehq.util.htmx_action import HqHtmxActionMixin, hq_hx_action
from corehq.util.metrics import metrics_gauge


@method_decorator(use_bootstrap5, name='dispatch')
@method_decorator(toggles.KYC_VERIFICATION.required_decorator(), name='dispatch')
class KycConfigurationView(HqHtmxActionMixin, BaseDomainView):
    section_name = _("Data")
    urlname = 'kyc_configuration'
    template_name = 'kyc/kyc_config_base.html'
    page_title = _('KYC Configuration')

    form_class = KycConfigureForm
    form_template_partial_name = 'kyc/partials/kyc_config_form_partial.html'

    @property
    def page_url(self):
        return reverse(self.urlname, args=[self.domain])

    @property
    def section_url(self):
        return reverse(self.urlname, args=(self.domain,))

    @property
    def page_context(self):
        return {
            'kyc_config_form': self.config_form,
        }

    @property
    def config(self):
        try:
            # Currently a domain can only save one config so we shouldn't
            # expect more than one per domain
            return KycConfig.objects.get(domain=self.domain)
        except KycConfig.DoesNotExist:
            return KycConfig(domain=self.domain)

    @property
    def config_form(self):
        if self.request.method == 'POST':
            return self.form_class(self.request.POST, instance=self.config)
        return self.form_class(instance=self.config)

    def post(self, request, *args, **kwargs):
        form = self.config_form
        show_success = False
        if form.is_valid():
            form.save(commit=True)
            show_success = True

        context = {
            'kyc_config_form': form,
            'show_success': show_success,
        }
        return self.render_htmx_partial_response(request, self.form_template_partial_name, context)


@method_decorator(login_required, name='dispatch')
@method_decorator(toggles.KYC_VERIFICATION.required_decorator(), name='dispatch')
class KycVerificationTableView(HqHtmxActionMixin, SelectablePaginatedTableView):
    urlname = 'kyc_verify_table'
    table_class = KycVerifyTable

    def get_queryset(self):
        kyc_config = KycConfig.objects.get(domain=self.request.domain)
        row_objs = kyc_config.get_kyc_users()
        return [self._parse_row(row_obj, kyc_config) for row_obj in row_objs]

    def _parse_row(self, row_obj, config):
        user_data = get_user_data_for_api(row_obj, config)
        row_data = {
            'id': row_obj.user_id,
            'has_invalid_data': False,
        }
        user_fields = [
            'first_name',
            'last_name',
            'phone_number',
            'email',
            'national_id_number',
            'street_address',
            'city',
            'post_code',
            'country',
        ]
        for field in user_fields:
            if field not in user_data:
                row_data['has_invalid_data'] = True
                continue
            row_data[field] = user_data[field]
        return row_data

    @hq_hx_action('post')
    def verify_rows(self, request, *args, **kwargs):
        kyc_config = KycConfig.objects.get(domain=self.request.domain)
        if request.POST.get('verify_all'):
            kyc_users = kyc_config.get_kyc_users()
        else:
            selected_ids = request.POST.getlist('selected_ids')
            kyc_users = kyc_config.get_kyc_users_by_ids(selected_ids)
        results = verify_users(kyc_users, kyc_config)
        verify_success = all(results.values())
        success_count = sum(1 for result in results.values() if result)
        fail_count = len(results) - success_count
        context = {
            'verify_success': verify_success,
            'success_count': success_count,
            'fail_count': fail_count,
        }
        self._report_verification_status_metric(success_count, fail_count)
        return self.render_htmx_partial_response(request, 'kyc/partials/kyc_verify_alert.html', context)

    def _report_verification_status_metric(self, success_count, failure_count):
        metrics_gauge(
            'commcare.integration.kyc.verification.success.count',
            success_count,
            tags={'domain': self.request.domain}
        )
        metrics_gauge(
            'commcare.integration.kyc.verification.failure.count',
            failure_count,
            tags={'domain': self.request.domain}
        )


@method_decorator(use_bootstrap5, name='dispatch')
@method_decorator(toggles.KYC_VERIFICATION.required_decorator(), name='dispatch')
class KycVerificationReportView(BaseDomainView):
    urlname = 'kyc_verify'
    template_name = 'kyc/kyc_verify_report.html'
    section_name = _('Data')
    page_title = _('KYC Report')

    @property
    def page_url(self):
        return reverse(self.urlname, args=[self.domain])

    @property
    def section_url(self):
        return reverse(self.urlname, args=(self.domain,))

    def get(self, request, *args, **kwargs):
        self._report_users_count_metric()
        return super().get(request, *args, **kwargs)

    def _report_users_count_metric(self):
        try:
            kyc_config = KycConfig.objects.get(domain=self.domain)
        except KycConfig.DoesNotExist:
            pass
        else:
            total_users = len(kyc_config.get_kyc_users())
            metrics_gauge(
                'commcare.integration.kyc.total_users.count',
                total_users,
                tags={'domain': self.domain}
            )
