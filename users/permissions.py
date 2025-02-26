from rest_framework.permissions import BasePermission

class RoleBasedPermission(BasePermission):
    """Allows access to users based on their role."""
    allowed_roles = []

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in self.allowed_roles


class IsAdminUser(RoleBasedPermission):
    allowed_roles = ["admin"]

class IsCashierUser(RoleBasedPermission):
    allowed_roles = ["cashier"]

class IsOwnerUser(RoleBasedPermission):
    allowed_roles = ["owner"]
