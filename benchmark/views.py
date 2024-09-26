from functools import wraps
import io
import time

import pandas as pd
from django.conf import settings
from django.core.cache import caches
from django.core.cache.backends.dummy import DummyCache
from django.http import HttpResponse


SETUP_FUNCTIONS = {}
TEST_FUNCTIONS = {}


def register_setup(func):
    SETUP_FUNCTIONS[func.__name__] = func
    return func

def register_test(func):
    @wraps(func)
    def timed_func(cache):
        n = 100
        start = time.monotonic()
        for _ in range(n):
            func(cache)
        return (time.monotonic() - start) / n

    TEST_FUNCTIONS[func.__name__] = timed_func

    return func


@register_test
def get_miss(cache):
    cache.get('empty-value')


@register_setup
def get_short_string(cache):
    cache.set('short-string', 'hello')


@register_test
def get_short_string(cache):
    cache.get('short_string')


@register_setup
def get_long_string(cache):
    cache.set('long-string', 'hello' * 1000)


@register_test
def get_long_string(cache):
    cache.get('long_string')


@register_test
def set_short_string(cache):
    cache.set('test-short-string', 'something')


@register_test
def set_long_string(cache):
    cache.set('test-long-string', 'something' * 1000)


@register_test
def delete_string(cache):
    cache.set('key-to-delete', 'something')
    cache.delete('key-to-delete')


def plot_mem_svg(plot):
    with io.StringIO() as f:
        figure = plot.get_figure()
        figure.savefig(f, format='svg', bbox_inches='tight')
        return f.getvalue()


def run_benchmark(request):
    results = []
    for test_name, test_func in TEST_FUNCTIONS.items():
        test_results = {'test': test_name}
        results.append(test_results)
        for cache_key in settings.CACHES:
            cache = caches[cache_key]
            if isinstance(cache, DummyCache):
                continue
            if test_name in SETUP_FUNCTIONS:
                SETUP_FUNCTIONS[test_name](cache)
            test_results[cache_key] = test_func(cache)
    df = pd.DataFrame(results).set_index('test')
    return HttpResponse(f"""
        {df.T.style.background_gradient(axis='rows').to_html()}
        {plot_mem_svg(df.plot.barh(legend='reverse', figsize=(12, 6)))}
    """)
