from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Course, Lesson


class CourseLessonPermissionsTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        # Пользователи
        self.user1 = User.objects.create_user(email='user1@test.local', password='pass12345', first_name='U1')
        self.user2 = User.objects.create_user(email='user2@test.local', password='pass12345', first_name='U2')
        self.moder = User.objects.create_user(email='moder@test.local', password='pass12345', first_name='Mod')
        # Группа модераторов
        moderators = Group.objects.get_or_create(name='moderators')[0]
        self.moder.groups.add(moderators)

        # Базовые данные
        self.course_user1 = Course.objects.create(title='C-U1', owner=self.user1)
        self.course_user2 = Course.objects.create(title='C-U2', owner=self.user2)
        self.lesson_user1 = Lesson.objects.create(course=self.course_user1, title='L-U1', owner=self.user1)
        self.lesson_user2 = Lesson.objects.create(course=self.course_user2, title='L-U2', owner=self.user2)

        # URLs
        self.course_list_url = reverse('course-list')
        self.lesson_list_url = reverse('lesson-list-create')

    # --- Общие требования аутентификации ---
    def test_auth_required_for_courses_and_lessons(self):
        self.assertEqual(self.client.get(self.course_list_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(self.lesson_list_url).status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Немодератор ---
    def test_regular_user_course_crud_and_scoping(self):
        self.client.force_authenticate(self.user1)
        # list — только свои
        resp_list = self.client.get(self.course_list_url)
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        ids = [c['id'] for c in resp_list.data['results']]
        self.assertIn(self.course_user1.id, ids)
        self.assertNotIn(self.course_user2.id, ids)

        # create — разрешено
        create_resp = self.client.post(self.course_list_url, data={"title": "New User1"}, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_resp.data['owner'], self.user1.id)
        new_course_id = create_resp.data['id']

        # update — только свои; чужой — 403
        own_detail = reverse('course-detail', args=[new_course_id])
        other_detail = reverse('course-detail', args=[self.course_user2.id])
        self.assertEqual(self.client.patch(own_detail, data={"description": "d"}, format='json').status_code,
                         status.HTTP_200_OK)
        self.assertEqual(self.client.patch(other_detail, data={"description": "x"}, format='json').status_code,
                         status.HTTP_403_FORBIDDEN)

        # delete — только свои
        self.assertEqual(self.client.delete(own_detail).status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.delete(other_detail).status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_lessons_crud_and_scoping(self):
        self.client.force_authenticate(self.user1)
        # list — только свои
        list_resp = self.client.get(self.lesson_list_url)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        ids = [l['id'] for l in list_resp.data['results']]
        self.assertIn(self.lesson_user1.id, ids)
        self.assertNotIn(self.lesson_user2.id, ids)

        # create — разрешено
        create_resp = self.client.post(self.lesson_list_url,
                                       data={"course": self.course_user1.id, "title": "L-new"},
                                       format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_resp.data['owner'], self.user1.id)
        detail_own = reverse('lesson-detail', args=[create_resp.data['id']])
        detail_other = reverse('lesson-detail', args=[self.lesson_user2.id])

        # update — владелец или модератор; здесь владелец
        self.assertEqual(self.client.patch(detail_own, data={"title": "upd"}, format='json').status_code,
                         status.HTTP_200_OK)
        # чужой — 403
        self.assertEqual(self.client.patch(detail_other, data={"title": "x"}, format='json').status_code,
                         status.HTTP_403_FORBIDDEN)

        # delete — только владелец
        self.assertEqual(self.client.delete(detail_own).status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.delete(detail_other).status_code, status.HTTP_403_FORBIDDEN)

    # --- Модератор ---
    def test_moderator_courses_permissions(self):
        self.client.force_authenticate(self.moder)

        # list — видит все
        resp_list = self.client.get(self.course_list_url)
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        ids = {c['id'] for c in resp_list.data['results']}
        self.assertTrue({self.course_user1.id, self.course_user2.id}.issubset(ids))

        # create — запрещено
        self.assertEqual(self.client.post(self.course_list_url, data={"title": "No"}).status_code,
                         status.HTTP_403_FORBIDDEN)

        # update — разрешено для любых
        any_detail = reverse('course-detail', args=[self.course_user1.id])
        self.assertEqual(self.client.patch(any_detail, data={"description": "m"}, format='json').status_code,
                         status.HTTP_200_OK)

        # delete — запрещено
        self.assertEqual(self.client.delete(any_detail).status_code, status.HTTP_403_FORBIDDEN)

    def test_moderator_lessons_permissions(self):
        self.client.force_authenticate(self.moder)
        # list — видит все
        resp_list = self.client.get(self.lesson_list_url)
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        ids = {l['id'] for l in resp_list.data['results']}
        self.assertTrue({self.lesson_user1.id, self.lesson_user2.id}.issubset(ids))

        # create — запрещено
        self.assertEqual(self.client.post(self.lesson_list_url,
                                          data={"course": self.course_user1.id, "title": "No"}).status_code,
                         status.HTTP_403_FORBIDDEN)

        # update — можно любые
        detail_other = reverse('lesson-detail', args=[self.lesson_user2.id])
        self.assertEqual(self.client.patch(detail_other, data={"title": "M-upd"}, format='json').status_code,
                         status.HTTP_200_OK)

        # delete — нельзя
        self.assertEqual(self.client.delete(detail_other).status_code, status.HTTP_403_FORBIDDEN)
