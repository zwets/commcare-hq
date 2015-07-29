from collections import defaultdict
from itertools import islice
import traceback

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

from celery.utils.mail import ErrorMail
from django.core import mail
from django.utils.log import AdminEmailHandler
from django.views.debug import get_exception_reporter_filter
from django.template.loader import render_to_string


def clean_exception(exception):
    """
    Takes an Exception instance and strips potentially sensitive information
    """
    from django.conf import settings
    if settings.DEBUG:
        return exception

    # couchdbkit doesn't provide a better way for us to catch this exception
    if (
        isinstance(exception, AssertionError) and
        exception.message.startswith('received an invalid response of type')
    ):
        message = ("It looks like couch returned an invalid response to "
                   "couchdbkit.  This could contain sensitive information, "
                   "so it's being redacted.")
        return exception.__class__(message)

    return exception


class HqAdminEmailHandler(AdminEmailHandler):
    """
    Custom AdminEmailHandler to include additional details which can be supplied as follows:

    logger.error(message,
        extra={
            'details': {'domain': 'demo', 'user': 'user1'}
        }
    )
    """
    def get_context(self, record):
        request = None
        try:
            request = record.request
            filter = get_exception_reporter_filter(request)
            request_repr = filter.get_request_repr(request)
        except Exception:
            request_repr = "Request repr() unavailable."

        tb_list = []
        code = None
        if record.exc_info:
            etype, _value, tb = record.exc_info
            value = clean_exception(_value)
            tb_list = ['Traceback (most recent call first):\n']
            formatted_exception = traceback.format_exception_only(etype, value)
            tb_list.extend(formatted_exception)
            extracted_tb = reversed(traceback.extract_tb(tb))
            code = self.get_code(extracted_tb)
            tb_list.extend(traceback.format_list(extracted_tb))
            stack_trace = '\n'.join(tb_list)
            subject = '%s: %s' % (record.levelname,
                                  formatted_exception[0].strip() if formatted_exception else record.getMessage())
        else:
            stack_trace = 'No stack trace available'
            subject = '%s: %s' % (
                record.levelname,
                record.getMessage()
            )
        context = defaultdict(lambda: '')
        context.update({
            'subject': self.format_subject(subject),
            'message': record.getMessage(),
            'details': getattr(record, 'details', None),
            'tb_list': tb_list,
            'request_repr': request_repr,
            'stack_trace': stack_trace,
            'code': code,
        })
        if request:
            context.update({
                'get': request.GET,
                'post': request.POST,
                'method': request.method,
                'url': request.build_absolute_uri(),
            })
        return context

    def emit(self, record):
        context = self.get_context(record)

        message = "\n\n".join(filter(None, [
            context['message'],
            self.format_details(context['details']),
            context['stack_trace'],
            context['request_repr'],
        ]))
        html_message = render_to_string('hqadmin/email/error_email.html', context)
        mail.mail_admins(context['subject'], message, fail_silently=True,
                         html_message=html_message)

    def format_details(self, details):
        if details:
            formatted = '\n'.join('{item[0]}: {item[1]}'.format(item=item) for item in details.items())
            return 'Details:\n{}'.format(formatted)

    def get_code(self, extracted_tb):
        trace = next((trace for trace in extracted_tb if 'site-packages' not in trace[0]), None)
        if not trace:
            return None

        filename = trace[0]
        lineno = trace[1]
        offset = 10
        with open(filename) as f:
            code_context = list(islice(f, lineno - offset, lineno + offset))

        return highlight(''.join(code_context),
            PythonLexer(),
            HtmlFormatter(
                noclasses=True,
                linenos='table',
                hl_lines=[offset, offset],
                linenostart=(lineno - offset + 1),
        )
        )


class NotifyExceptionEmailer(HqAdminEmailHandler):
    def get_context(self, record):
        context = super(NotifyExceptionEmailer, self).get_context(record)
        context['subject'] = record.getMessage()
        return context


class SensitiveErrorMail(ErrorMail):
    """
    Extends Celery's ErrorMail class to prevents task args and kwargs from being printed in error emails.
    """
    replacement = '(excluded due to sensitive nature)'

    def format_body(self, context):
        context['args'] = self.replacement
        context['kwargs'] = self.replacement
        return self.body.strip() % context
