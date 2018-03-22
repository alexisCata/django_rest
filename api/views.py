from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets, mixins
# from rest_framework.decorators import detail_route
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.database import get_chats, get_chat_history
from core.models import (Notification,
                         Class,
                         User,
                         Subject,
                         Schedule,
                         GROUP_ADMIN_ID,
                         GROUP_TEACHER_ID,
                         GROUP_STUDENT_ID,
                         GROUP_PARENT_ID,
                         )
from worker.tasks import push_notification
from .serializers import (NotificationSerializer,
                          ClassSerializer,
                          UserSerializer,
                          SubjectSerializer,
                          ScheduleSerializer)


class NotificationsService(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.CreateModelMixin,
                           viewsets.GenericViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('type',)
    permission_classes = (permissions.IsAuthenticated,)

    http_method_names = ('get', 'post')

    def perform_create(self, serializer):
        subject_param = self.request.data.get('subject_id', None)
        try:
            subject_id = int(subject_param) \
                if subject_param is not None \
                else None

        except ValueError:
            raise ValidationError(_('Bad subject id'))

        if subject_id is not None:
            subject = get_object_or_404(Subject, pk=subject_id)

        else:
            subject = None

        target_student_id = self.request.data.get('target_student_id', None)
        if target_student_id is not None:
            target_student = get_object_or_404(User, pk=target_student_id)

        else:
            target_student = None

        target_class_id = self.request.data.get('target_class_id', None)
        if target_class_id is not None:
            target_class = get_object_or_404(Class, pk=target_class_id)

        else:
            target_class = None

        if not target_class and not target_student:
            raise ValidationError(_('Notification may have directed to a '
                                    'student or a class.'))

        notification = serializer.save(owner=self.request.user,
                                       target_class=target_class,
                                       target_student=target_student,
                                       subject=subject)
        push_notification.delay(notification.id)

    def get_queryset(self):
        user = self.request.user

        student_id = self.request.query_params.get('student', None)
        subject_id = self.request.query_params.get('subject', None)

        from_date = self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)

        size = self.request.query_params.get('size', None)

        if user.groups.filter(name=GROUP_ADMIN_ID).exists():
            queryset = Notification.objects.all()

        elif user.groups.filter(name=GROUP_TEACHER_ID).exists():
            # - Owned notifications.
            queryset = Notification.objects.filter(Q(owner=user))

        elif user.groups.filter(name=GROUP_PARENT_ID).exists():
            # - Notification to children.
            # - Notification to children classes.
            classes = list(Class.objects.filter(
                Q(students__parents=user),
            ))

            queryset = Notification.objects.filter(
                Q(target_student__parents=user) | \
                Q(target_class__in=classes)
            ).distinct()

        elif user.groups.filter(name=GROUP_STUDENT_ID).exists():
            queryset = User.objects.none()

        if student_id is not None:
            student = User.objects.get(pk=int(student_id))

            queryset = queryset.filter(
                Q(target_student=student) | \
                Q(target_student=None, target_class=student.attends),
            )

        if subject_id is not None:
            subject = Subject.objects.get(pk=int(subject_id))

            queryset = queryset.filter(
                Q(subject=subject)
            )

        if from_date is not None:
            queryset = queryset.filter(date__gte=from_date)

        if to_date is not None:
            queryset = queryset.filter(date__lt=to_date)

        # XXX Order by timestamp instead?
        queryset = queryset.order_by('-date')

        if size is not None:
            queryset = queryset[:int(size)]

        self.queryset = queryset

        return self.queryset


class ClassesService(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer

    permission_classes = (permissions.IsAuthenticated,)

    # @detail_route(methods=['get'])
    # def students(self, request, pk=None):
    #     c = Class.objects.get(pk=pk)

    #     return Response(StudentSerializer(c.students.all(), many=True).data,
    #                     status=status.HTTP_200_OK,
    #                     )


class UsersService(mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def retrieve(self, request, pk=None):
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = UserSerializer(user)

        return Response(serializer.data)

    def get_queryset(self):
        no_students = self.request.query_params.get('no_students', False)

        user = self.request.user
        if user.groups.filter(name=GROUP_ADMIN_ID).exists():
            if not no_students:
                queryset = User.objects.filter(
                    ~Q(id=user.id),
                )

            else:
                queryset = User.objects.filter(
                    ~Q(id=user.id),
                    ~Q(groups__name=GROUP_STUDENT_ID),
                )

        elif user.groups.filter(name=GROUP_TEACHER_ID).exists():
            # - All teachers
            # - Fathers of the students of the classes that their children
            #   attend.
            # - Students.
            classes = list(Class.objects.filter(
                Q(teachers_subjects__teacher=user)
            ))

            parents = User.objects.filter(
                Q(groups__name=GROUP_PARENT_ID),
                Q(children__attends__in=classes),
            )

            teachers = User.objects.filter(
                ~Q(id=user.id),
                Q(groups__name=GROUP_TEACHER_ID),
            )

            if not no_students:
                students = User.objects.filter(
                    Q(groups__name=GROUP_STUDENT_ID),
                    Q(attends__in=classes),
                )

            else:
                students = User.objects.none()

            queryset = (parents | teachers | students).distinct()

        elif user.groups.filter(name=GROUP_PARENT_ID).exists():
            # - Teachers of the classes that their children attend.
            # - Fathers of the students of the classes that their children
            #   attend.
            # - Children
            classes = list(Class.objects.filter(
                Q(students__parents=user)
            ))

            parents = User.objects.filter(
                ~Q(id=user.id),
                Q(groups__name=GROUP_PARENT_ID),
                Q(children__attends__in=classes),
            )

            teachers = User.objects.filter(
                Q(groups__name=GROUP_TEACHER_ID),
                Q(classes_subjects__teaches_in__in=classes),
            )

            if not no_students:
                students = User.objects.filter(
                    Q(groups__name=GROUP_STUDENT_ID),
                    Q(parents=user),
                )

            else:
                students = User.objects.none()

            queryset = (parents | teachers | students).distinct()

        elif user.groups.filter(name=GROUP_STUDENT_ID).exists():
            queryset = User.objects.none()

        return queryset


class ScheduleService(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer

    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user

        queryset = Schedule.objects.filter(class_teacher_subject__teacher=user)

        return queryset


class AuthUser(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class GetUserParents(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, user_id, *args, **kwargs):
        user = User.objects.get(id=int(user_id))
        serializer = UserSerializer(user.parents.all(), many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class SubjectsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user

        class_id = self.request.query_params.get('class', None)

        if user.groups.filter(name=GROUP_ADMIN_ID).exists():
            queryset = Subject.objects.all()

        elif user.groups.filter(name=GROUP_TEACHER_ID).exists():
            queryset = Subject.objects.filter(
                classes_teachers__teacher=user).distinct()  # distinct needed?

        # elif user.groups.filter(name=GROUP_PARENT_ID).exists():

        else:
            queryset = Subject.objects.none()

        if class_id is not None:
            subjects = list(Subject.objects.filter(
                Q(classes_teachers__teaches_in__id=int(class_id)),
            ).values_list('id', flat=True))

            queryset = queryset.filter(id__in=subjects)

        return Response(
            SubjectSerializer(queryset, many=True).data,
            status=status.HTTP_200_OK
        )


class ChatsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user

        return Response(
            get_chats(user.id),
            status=status.HTTP_200_OK
        )


class ChatsHistoryView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, user_id, *args, **kwargs):
        user = request.user

        size = int(request.query_params.get('size', 50))
        from_message = request.query_params.get('from', None)

        return Response(
            get_chat_history(user.id, int(user_id),
                             size=size, from_message=from_message,
                             mark_as_read=True),
            status=status.HTTP_200_OK
        )
