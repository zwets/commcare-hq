from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

from dimagi.utils.web import get_ip

from corehq.apps.registration.utils import activate_new_user
from corehq.apps.sso.models import IdentityProvider, AuthenticatedEmailDomain
from corehq.apps.sso.utils.session_helpers import (
    get_sso_invitation_from_session,
    get_sso_user_first_name_from_session,
    get_sso_user_last_name_from_session,
)
from corehq.apps.sso.utils.user_helpers import get_email_domain_from_username
from corehq.apps.users.models import CouchUser
from corehq.const import (
    USER_CHANGE_VIA_SSO_INVITE,
    USER_CHANGE_VIA_SSO_NEW_USER,
)


class SsoBackend(ModelBackend):
    """
    Authenticates against an IdentityProvider and SAML2 session data.
    """

    def authenticate(self, request, username, idp_slug, is_handshake_successful):
        if not (request and username and idp_slug and is_handshake_successful):
            return None

        try:
            identity_provider = IdentityProvider.objects.get(slug=idp_slug)
        except IdentityProvider.DoesNotExist:
            # not sure how we would even get here, but just in case
            request.sso_login_error = f"Identity Provider {idp_slug} does not exist."
            return None

        if not identity_provider.is_active:
            request.sso_login_error = f"This Identity Provider {idp_slug} is not active."
            return None

        email_domain = get_email_domain_from_username(username)
        if not email_domain:
            # not a valid username
            request.sso_login_error = f"Username {username} is not valid."
            return None

        if not AuthenticatedEmailDomain.objects.filter(
            email_domain=email_domain, identity_provider=identity_provider
        ).exists():
            # if this user's email domain is not authorized by this identity
            # do not continue with authentication
            request.sso_login_error = (
                f"The Email Domain {email_domain} is not allowed to "
                f"authenticate with this Identity Provider ({idp_slug})."
            )
            return None

        invitation = get_sso_invitation_from_session(request)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = self._create_new_user(request, username, invitation)

        request.sso_login_error = None
        return user

    def _create_new_user(self, request, username, invitation):
        """
        This creates a new user in HQ based on information in the request.
        :param request: HttpRequest
        :param username: String (username)
        :param invitation: Invitation
        :return: User
        """
        created_via = (USER_CHANGE_VIA_SSO_INVITE if invitation
                       else USER_CHANGE_VIA_SSO_NEW_USER)
        created_by = (CouchUser.get_by_user_id(invitation.invited_by) if invitation
                      else None)
        domain = invitation.domain if invitation else None

        new_web_user = activate_new_user(
            username=username,
            password=User.objects.make_random_password(),
            created_by=created_by,
            created_via=created_via,
            first_name=get_sso_user_first_name_from_session(request),
            last_name=get_sso_user_last_name_from_session(request),
            domain=domain,
            ip=get_ip(request),
        )
        return new_web_user
