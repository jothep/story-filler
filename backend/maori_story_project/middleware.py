"""
Custom middleware for the project
"""
import re
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from urllib.parse import urlparse


class WildcardCsrfViewMiddleware(CsrfViewMiddleware):
    """
    Extended CSRF middleware that supports wildcard domains.

    Allows patterns like:
    - https://*.run.app
    - https://*.us-central1.run.app
    """

    def _origin_verified(self, request):
        """Override to support wildcard patterns"""
        # Get the origin from the request
        request_origin = request.META.get("HTTP_ORIGIN")

        if request_origin:
            # Check wildcard patterns
            wildcard_patterns = getattr(settings, 'CSRF_TRUSTED_ORIGIN_WILDCARDS', [])
            for pattern in wildcard_patterns:
                # Convert wildcard pattern to regex
                # e.g., "https://*.run.app" -> "^https://[^/]+\.run\.app$"
                regex_pattern = pattern.replace('.', r'\.').replace('*', r'[^/]+')
                if re.match(f'^{regex_pattern}$', request_origin):
                    return True

        # Fall back to default origin check
        return super()._origin_verified(request)

    def _check_referer(self, request):
        """Override to support wildcard patterns in referer check"""
        referer = request.META.get('HTTP_REFERER')

        if referer:
            referer_parsed = urlparse(referer)
            referer_origin = f"{referer_parsed.scheme}://{referer_parsed.netloc}"

            # Check wildcard patterns
            wildcard_patterns = getattr(settings, 'CSRF_TRUSTED_ORIGIN_WILDCARDS', [])
            for pattern in wildcard_patterns:
                # Convert wildcard pattern to regex
                regex_pattern = pattern.replace('.', r'\.').replace('*', r'[^/]+')
                if re.match(f'^{regex_pattern}$', referer_origin):
                    # Wildcard matched, allow request
                    return None

        # Fall back to default CSRF check
        return super()._check_referer(request)
