#!/bin/bash
# Keep the historical entry point, but never start the unsafe restore procedure.
printf '%s\n' \
    'ERROR: Legacy volume restore is disabled.' \
    'The previous implementation could delete existing data before validating a backup.' \
    'A safe replacement restore workflow is not available yet.' \
    'No containers, volumes, or cloud resources were changed.' >&2
exit 1
