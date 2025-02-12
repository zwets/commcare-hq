import time
from functools import wraps
from operator import eq

from attrs import asdict, define, field

from dimagi.utils.logging import notify_error, notify_exception

from corehq.util.metrics import metrics_histogram


@define
class Experiment:
    """Experiment decorator factory for comparing old and new code paths.

    :param campaign: Experiment campaign name for a group of experiments.
        Should be defined as a constant in `corehq/apps/experiments/__init__.py`.
    :param old_args: A dict of keyword arguments to invoke the old code path.
    :param new_args: A dict of keyword arguments to invoke the new code path.
    :param time_buckets: A tuple of histogram buckets for the old code
        path timer.
    :param percent_buckets: A tuple of histogram buckets for the new
        code path time as a percentage of the old code path time. For
        example, if the old code path takes 1 second and the new code
        path takes 2 seconds, the percentage is 2 / 1 or 200%.
    """
    campaign = field()
    old_args = field(factory=dict)
    new_args = field(factory=dict)
    is_equal = field(default=eq)
    time_buckets = field(default=(0.01, 0.1, 1, 10, 100))
    percent_buckets = field(default=(50, 95, 105, 200))
    path = field(default="")

    def __call__(self, func=None, /, **kw):
        experiment = type(self)(**(asdict(self) | kw))
        if func is None:
            return experiment
        experiment.path = f"{func.__module__}.{func.__qualname__}"
        return experiment.decorate(func)

    @property
    def tags(self):
        return {"campaign": self.campaign, "path": self.path}

    def decorate(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            old_error = new_error = None
            start = time.time()
            try:
                old_result = func(*args, **kwargs, **self.old_args)
            except Exception as err:
                old_error = err
            mid = time.time()
            try:
                new_result = func(*args, **kwargs, **self.new_args)
            except Exception as err:
                if old_error is None:
                    notify_exception(None, "new code path failed in experiment",
                                    details=self.tags)
                    new_error = True  # error reference not needed
                else:
                    new_error = err

            end = time.time()
            old_time = mid - start
            new_time = end - mid
            diff_pct = (new_time / old_time * 100) if old_time else over_the_top
            metrics_histogram(
                "commcare.experiment.time", old_time, tags=self.tags,
                bucket_tag='duration', buckets=self.time_buckets, bucket_unit='s',
            )
            metrics_histogram(
                "commcare.experiment.diff", diff_pct, tags=self.tags,
                bucket_tag='duration', buckets=self.percent_buckets, bucket_unit='%',
            )

            if old_error is not None:
                if new_error is None:
                    new_repr = repr(new_result)
                elif type(new_error) is type(old_error) and new_error.args == old_error.args:
                    raise old_error
                else:
                    new_repr = f"raised {describe(type(new_error), new_error.args, {})}"
                old_repr = describe(type(old_error), old_error.args, {})
                notify_error(
                    f"{describe(func, args, kwargs)}: raised {old_repr} != {new_repr}",
                    details=self.tags,
                )
                raise old_error
            if new_error is None and not self.is_equal(old_result, new_result):
                notify_error(
                    f"{describe(func, args, kwargs)}: {old_result!r} != {new_result!r}",
                    details=self.tags,
                )
            return old_result

        over_the_top = self.percent_buckets[-1] + 1
        wrapper.experiment = self
        return wrapper


def describe(func, args, kwargs, vlen=20):
    def rep(v):
        rval = repr(v)
        return (rval[:vlen] + "...") if len(rval) > vlen else rval
    argv = [rep(a) for a in args] + [f"{k}={rep(v)}" for k, v in kwargs.items()]
    return f"{func.__name__}({', '.join(argv)})"
