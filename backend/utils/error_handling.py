"""
Error Handling Utilities
Standardized error responses and custom exceptions
"""

import json
from typing import Dict, Any, List, Optional


class ImageValidationError(Exception):
    """Raised when image validation fails"""
    pass


class DetectionFailedError(Exception):
    """Raised when room detection finds no rooms"""
    pass


def error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: Optional[str] = None,
    suggestions: Optional[List[str]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build standardized error response

    Args:
        status_code: HTTP status code
        error_code: Machine-readable error code
        message: Human-readable error message
        details: Optional additional details
        suggestions: Optional list of suggestions for user
        request_id: Optional request ID for tracking

    Returns:
        API Gateway response dictionary
    """

    body = {
        'status': 'error',
        'error_code': error_code,
        'message': message
    }

    if details:
        body['details'] = details

    if suggestions:
        body['suggestions'] = suggestions

    if request_id:
        body['request_id'] = request_id

    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }
