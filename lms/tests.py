from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Course, Lesson


class CourseLessonAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(email='admin@test.local', password='adminpass')
        self.course_list_url = reverse('course-list')  # /api/courses/

    def test_courses_list_anonymous_ok(self):
        Course.objects.create(title='C1')
        resp = self.client.get(self.course_list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)

    def test_courses_create_anonymous_allowed(self):
        payload = {"title": "New Course"}
        resp = self.client.post(self.course_list_url, data=payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_courses_crud_as_admin(self):
        # create
        self.client.force_authenticate(self.admin)
        create_resp = self.client.post(self.course_list_url, data={"title": "C-Admin", "description": "desc"})
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        course_id = create_resp.data['id']
        detail_url = reverse('course-detail', args=[course_id])

        # update (patch)
        patch_resp = self.client.patch(detail_url, data={"description": "updated"}, format='json')
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_resp.data['description'], 'updated')

        # delete
        del_resp = self.client.delete(detail_url)
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_lessons_crud_anonymous_allowed(self):
        course = Course.objects.create(title='Base')
        lesson_list_url = reverse('lesson-list-create')  # /api/lessons/

        # anonymous create allowed (по условиям ДЗ безопасность не включаем)
        create_l = self.client.post(lesson_list_url, data={"course": course.id, "title": "L1"}, format='json')
        self.assertEqual(create_l.status_code, status.HTTP_201_CREATED)
        lesson_id = create_l.data['id']
        lesson_detail_url = reverse('lesson-detail', args=[lesson_id])

        # list ok
        list_resp = self.client.get(lesson_list_url)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)

        # update ok (анонимно)
        patch_resp = self.client.patch(lesson_detail_url, data={"title": "L1-upd"}, format='json')
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_resp.data['title'], 'L1-upd')

        # delete ok (анонимно)
        del_resp = self.client.delete(lesson_detail_url)
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
