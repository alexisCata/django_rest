from rest_framework import permissions


class IsOwnerOrTargetReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        # if request.method in permissions.SAFE_METHODS:
        #     return True

        if obj.owner == request.user:
            return True

        # Write permissions are only allowed to the owner of the snippet.
        if request.method in permissions.SAFE_METHODS:
            if obj.target_student is not None:
                return obj.target_student == request.user

            elif obj.target_class is not None:
                return obj.target_class.students.filter(id=request.user.id).\
                        exists()

        return False
