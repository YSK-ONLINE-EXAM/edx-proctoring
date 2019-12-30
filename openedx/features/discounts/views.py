"""
The Discount API Views should return information about discounts that apply to the user and course.

"""
# -*- coding: utf-8 -*-


from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import CourseKey
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.cors_csrf.decorators import ensure_csrf_cookie_cross_domain
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from openedx.core.lib.api.permissions import ApiKeyHeaderPermissionIsAuthenticated
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin

from .applicability import can_receive_discount, discount_percentage


class CourseUserDiscount(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Request discount information for a user and course

    **Example Requests**

        GET /api/discounts/v1/course/{course_key_string}

    **Response Values**

        Body consists of the following fields:
            discount_applicable:
                whether the user can receive a discount for this course
            jwt:
                the jwt with user information and discount information

    **Parameters:**

        course_key_string:
            The course key for which the discount should be applied

    **Returns**

        * 200 on success with above fields.
        * 401 if there is no user signed in.

        Example response:
        {
            "discount_applicable": false,
            "jwt": xxxxxxxx.xxxxxxxx.xxxxxxx
        }
    """
    authentication_classes = (JwtAuthentication, OAuth2AuthenticationAllowInactiveUser,
                              SessionAuthenticationAllowInactiveUser,)
    permission_classes = (ApiKeyHeaderPermissionIsAuthenticated,)

    # Since the course about page on the marketing site uses this API to auto-enroll users,
    # we need to support cross-domain CSRF.
    @method_decorator(ensure_csrf_cookie_cross_domain)
    def get(self, request, course_key_string):
        """
        Return the discount percent, if the user has appropriate permissions.
        """
        course_key = CourseKey.from_string(course_key_string)
        course = CourseOverview.get_from_id(course_key)
        discount_applicable = can_receive_discount(user=request.user, course=course)
        discount_percent = discount_percentage(course)
        payload = {'discount_applicable': discount_applicable, 'discount_percent': discount_percent}
        return Response({
            'discount_applicable': discount_applicable,
            'jwt': create_jwt_for_user(request.user, additional_claims=payload)})


class CourseUserDiscountWithUserParam(DeveloperErrorViewMixin, APIView):
    """
    DO NOT USE

    This should not be used for anything other than getting the course/user discount information from
    ecommerce after payment in order to build an order. We plan to build orders before payment in this
    ticket: REV-692, at which point, this endpoint will no longer be necessary and should be removed.

    **Use Cases**

        Request discount information for a user and course

    **Example Requests**

        GET /api/discounts/v1/user/{user_id}/course/{course_key_string}

    **Response Values**

        Body consists of the following fields:
            discount_applicable:
                whether the user can receive a discount for this course
            jwt:
                the jwt with user information and discount information

    **Parameters:**

        course_key_string:
            The course key for which the discount should be applied
        user_id
            The user id for which the discount should be applied

    **Returns**

        * 200 on success with above fields.

        Example response:
        {
            "discount_applicable": false,
            "jwt": xxxxxxxx.xxxxxxxx.xxxxxxx
        }
    """
    authentication_classes = (JwtAuthentication, OAuth2AuthenticationAllowInactiveUser,
                              SessionAuthenticationAllowInactiveUser,)
    permission_classes = (ApiKeyHeaderPermissionIsAuthenticated, IsAdminUser)

    # Since the course about page on the marketing site uses this API to auto-enroll users,
    # we need to support cross-domain CSRF.
    @method_decorator(ensure_csrf_cookie_cross_domain)
    def get(self, request, course_key_string, user_id):
        """
        Return the discount percent, if the user has appropriate permissions.
        """
        course_key = CourseKey.from_string(course_key_string)
        course = CourseOverview.get_from_id(course_key)
        user = User.objects.get(id=user_id)
        discount_applicable = can_receive_discount(user=user, course=course)
        discount_percent = discount_percentage(course)
        payload = {'discount_applicable': discount_applicable, 'discount_percent': discount_percent}
        return Response({
            'discount_applicable': discount_applicable,
            'jwt': create_jwt_for_user(request.user, additional_claims=payload)})
