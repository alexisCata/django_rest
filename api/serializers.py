from django.utils import timezone
from django.contrib.auth.models import Group
# from django.core.exceptions import ValidationError
# from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from core.models import User, Notification, Class, Subject, Schedule


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('name',)


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name',)


class TeacherSerializer(serializers.HyperlinkedModelSerializer):
    groups = GroupSerializer(many=True)

    class Meta:
        model = User
        fields = ('id',
                  'first_name',
                  'last_name',
                  'groups',
                  )


class ClassTeacherSubjectSerializer(serializers.HyperlinkedModelSerializer):
    # TODO Different serializers for students and teachers.
    teacher = TeacherSerializer()
    subject = SubjectSerializer()
    # teaches_in = ClassSerializer()

    class Meta:
        model = User
        fields = ('teacher',
                  'subject',
                  # 'teaches_in',
                  )


class ClassStudentSerializer(serializers.HyperlinkedModelSerializer):
    teachers_subjects = ClassTeacherSubjectSerializer(many=True, read_only=True)

    class Meta:
        model = Class
        fields = ('id',
                  'name',
                  'teachers_subjects',
                  )


class StudentSerializer(serializers.HyperlinkedModelSerializer):
    subjects = SubjectSerializer(many=True)
    attends = ClassStudentSerializer()

    class Meta:
        model = User
        fields = ('id',
                  'first_name',
                  'last_name',
                  'subjects',
                  'attends',
                  )


class ClassSerializer(serializers.HyperlinkedModelSerializer):
    students = StudentSerializer(many=True, read_only=True)
    teachers_subjects = ClassTeacherSubjectSerializer(many=True, read_only=True)

    class Meta:
        model = Class
        fields = ('id',
                  'name',
                  'students',
                  'teachers_subjects',
                  )


class UserSerializer(serializers.HyperlinkedModelSerializer):
    groups = GroupSerializer(many=True)
    subjects = SubjectSerializer(many=True)
    attends = ClassSerializer()
    children = StudentSerializer(many=True)

    class Meta:
        model = User
        fields = ('id',
                  'first_name',
                  'last_name',
                  'groups',
                  'subjects',
                  'attends',
                  'children',
                  )


class NotificationSerializer(serializers.HyperlinkedModelSerializer):
    owner = TeacherSerializer(read_only=True)
    target_student = StudentSerializer(read_only=True)
    target_class = ClassSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Notification
        fields = (
            'id',
            'owner',
            'title',
            'description',
            'timestamp',
            'date',
            'target_student',
            'target_class',
            'type',
            'custom_fields',
            'subject',
            'icon',
        )


class ScheduleClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ('id',
                  'name')


class ScheduleClassTeacherSubjectSerializer(serializers.HyperlinkedModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    teaches_in = ClassSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('teacher',
                  'subject',
                  'teaches_in',
                  )


class ScheduleSerializer(serializers.HyperlinkedModelSerializer):
    class_teacher_subject = ScheduleClassTeacherSubjectSerializer(read_only=True)

    class Meta:
        model = Schedule
        fields = (
            'day',
            'order',
            'time',
            'class_teacher_subject',
        )


