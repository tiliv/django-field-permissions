class InstancePermissionBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = True

    def authenticate(self, username, password):
        """ Abstain from offering user authentication. """
        return None

    def has_perm(self, user_obj, perm, obj=None):
        """ Consults the target object for runtime instance permission. """

        # If the obj is None, we don't want to offer any affirmative opinion about the object.
        # The standard Django model permission system will handle this by returning True when it is
        # appropriate.
        if obj is None:
            return False

        # Model doesn't handle instance-level hook.
        if not hasattr(obj, 'has_perm'):
            return True

        return obj.has_perm(user_obj, perm)

    def get_all_permissions(self, user_obj, obj=None):
        """
        Returns a set of permission strings that the given ``user_obj`` has for ``obj``
        """
        # check if user_obj and object are supported
        support, user_obj = check_support(user_obj, obj)
        if not support:
            return set()

        check = ObjectPermissionChecker(user_obj)
        return check.get_perms(obj)
