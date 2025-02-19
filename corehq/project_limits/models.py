import architect
from django.db import models
from field_audit import audit_fields

AVG = 'AVG'
MAX = 'MAX'

AGGREGATION_OPTIONS = [
    (AVG, 'Average'),
    (MAX, 'Maximum'),
]


class DynamicRateDefinition(models.Model):
    key = models.CharField(max_length=512, blank=False, null=False, unique=True, db_index=True)
    per_week = models.FloatField(default=None, blank=True, null=True)
    per_day = models.FloatField(default=None, blank=True, null=True)
    per_hour = models.FloatField(default=None, blank=True, null=True)
    per_minute = models.FloatField(default=None, blank=True, null=True)
    per_second = models.FloatField(default=None, blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._clear_caches()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self._clear_caches()

    def _clear_caches(self):
        from corehq.project_limits.rate_limiter import get_dynamic_rate_definition

        get_dynamic_rate_definition.clear(self.key, {})


class GaugeDefinition(models.Model):
    """
    An abstract model to be used to define configuration to limit gauge values.
    The model is used by GaugeLimiter class to decide weather to limit or not.
    """

    key = models.CharField(max_length=512, blank=False, null=False, unique=True, db_index=True)
    wait_for_seconds = models.IntegerField(null=False)
    acceptable_value = models.FloatField(default=None, blank=True, null=True)
    aggregator = models.CharField(max_length=10, null=True, blank=True, choices=AGGREGATION_OPTIONS)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._clear_caches()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self._clear_caches()

    def _clear_caches(self):
        pass


class PillowLagGaugeDefinition(GaugeDefinition):
    max_value = models.FloatField(default=None, blank=True, null=True)
    average_value = models.FloatField(default=None, blank=True, null=True)

    def _clear_caches(self):
        from corehq.project_limits.gauge import get_pillow_throttle_definition

        get_pillow_throttle_definition.clear(self.key)


@architect.install('partition', type='range', subtype='date', constraint='week', column='date')
class RateLimitedTwoFactorLog(models.Model):
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    username = models.CharField(max_length=255, null=False, db_index=True)
    ip_address = models.CharField(max_length=45, null=False, db_index=True)
    phone_number = models.CharField(max_length=127, null=False, db_index=True)
    # 'sms', 'call' don't expect this to change
    method = models.CharField(max_length=4, null=False)
    # largest input is 'unknown', 15 for headroom
    window = models.CharField(max_length=15, null=False)
    # largest input is 'number_rate_limited', 31 for headroom
    status = models.CharField(max_length=31, null=False)


@audit_fields("limit")
class SystemLimit(models.Model):
    key = models.CharField(max_length=255)
    limit = models.PositiveIntegerField()
    # the domain field is reserved for extreme cases since limits should apply globally in steady state
    domain = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        constraints = [models.UniqueConstraint(fields=['key', 'domain'], name='unique_key_per_domain_constraint')]

    def __str__(self):
        domain = f"[{self.domain}] " if self.domain else ""
        return f"{domain}{self.key}: {self.limit}"
