from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta

from lms.models import Course, Lesson
from .models import Payment


class UsersProfilesAndPaymentsTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        # Users
        self.u1 = User.objects.create_user(email='u1@test.local', password='pass12345', first_name='U1', last_name='L1')
        self.u2 = User.objects.create_user(email='u2@test.local', password='pass12345', first_name='U2', last_name='L2')
        self.moder = User.objects.create_user(email='mod@test.local', password='pass12345', first_name='Mod')

        # Moderators group
        moderators = Group.objects.get_or_create(name='moderators')[0]
        self.moder.groups.add(moderators)

        # Courses/Lessons for payments
        self.c1 = Course.objects.create(title='Course1', owner=self.u1)
        self.c2 = Course.objects.create(title='Course2', owner=self.u2)
        self.l1 = Lesson.objects.create(course=self.c1, title='L1', owner=self.u1)
        self.l2 = Lesson.objects.create(course=self.c2, title='L2', owner=self.u2)

        # Payments: 2 for u1, 1 for u2
        self.p_u1_1 = Payment.objects.create(user=self.u1, course=self.c1, amount=1000, method=Payment.Method.CASH)
        self.p_u1_2 = Payment.objects.create(user=self.u1, lesson=self.l1, amount=500, method=Payment.Method.TRANSFER)
        self.p_u2_1 = Payment.objects.create(user=self.u2, course=self.c2, amount=2000, method=Payment.Method.CASH)

        # URLs
        self.user_list_url = reverse('user-list')
        self.user1_detail_url = reverse('user-detail', args=[self.u1.id])
        self.user2_detail_url = reverse('user-detail', args=[self.u2.id])
        self.payments_url = reverse('payment-list')

    def test_profile_read_rules_and_update_permissions(self):
        # Auth as u1
        self.client.force_authenticate(self.u1)

        # View other profile: should hide last_name and payments
        resp_other = self.client.get(self.user2_detail_url)
        self.assertEqual(resp_other.status_code, status.HTTP_200_OK)
        self.assertNotIn('last_name', resp_other.data)
        self.assertIn('payments', resp_other.data)
        self.assertEqual(resp_other.data['payments'], [])

        # View own profile: payments visible and non-empty
        resp_self = self.client.get(self.user1_detail_url)
        self.assertEqual(resp_self.status_code, status.HTTP_200_OK)
        self.assertIn('last_name', resp_self.data)
        self.assertTrue(isinstance(resp_self.data.get('payments'), list))
        self.assertGreaterEqual(len(resp_self.data['payments']), 2)

        # Update own profile allowed
        upd_self = self.client.patch(self.user1_detail_url, data={'first_name': 'U1-upd'}, format='json')
        self.assertEqual(upd_self.status_code, status.HTTP_200_OK)
        self.assertEqual(upd_self.data['first_name'], 'U1-upd')

        # Update other profile forbidden
        upd_other = self.client.patch(self.user2_detail_url, data={'first_name': 'X'}, format='json')
        self.assertEqual(upd_other.status_code, status.HTTP_403_FORBIDDEN)

    def test_payments_visibility_regular_vs_moderator(self):
        # As regular u1 — only own payments
        self.client.force_authenticate(self.u1)
        resp_u1 = self.client.get(self.payments_url)
        self.assertEqual(resp_u1.status_code, status.HTTP_200_OK)
        ids_u1 = {p['id'] for p in resp_u1.data['results']}
        self.assertTrue({self.p_u1_1.id, self.p_u1_2.id}.issubset(ids_u1))
        self.assertNotIn(self.p_u2_1.id, ids_u1)

        # As moderator — sees all
        self.client.force_authenticate(self.moder)
        resp_m = self.client.get(self.payments_url)
        self.assertEqual(resp_m.status_code, status.HTTP_200_OK)
        ids_m = {p['id'] for p in resp_m.data['results']}
        self.assertTrue({self.p_u1_1.id, self.p_u1_2.id, self.p_u2_1.id}.issubset(ids_m))


class StripePaymentTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email='stripe@test.local', password='pass12345')
        self.course = Course.objects.create(title='Stripe Course', owner=self.user)
        self.create_url = reverse('payment-create')

    def auth(self):
        self.client.force_authenticate(self.user)

    @patch('users.stripe_service.create_checkout_session')
    @patch('users.stripe_service.create_price')
    @patch('users.stripe_service.create_product')
    def test_create_payment_success(self, m_product, m_price, m_session):
        self.auth()
        m_product.return_value = {'id': 'prod_test_123'}
        m_price.return_value = {'id': 'price_test_456'}
        m_session.return_value = {'id': 'cs_test_789', 'url': 'https://checkout.stripe.com/pay/test', 'status': 'open'}

        resp = self.client.post(self.create_url, data={
            'course_id': self.course.id,
            'amount': '1999.00'
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('stripe_checkout_url', resp.data)
        self.assertTrue(str(resp.data['stripe_checkout_url']).startswith('http'))

        # Payment object persisted with Stripe fields
        p = Payment.objects.get(id=resp.data['id'])
        self.assertEqual(p.method, Payment.Method.STRIPE)
        self.assertEqual(p.stripe_product_id, 'prod_test_123')
        self.assertEqual(p.stripe_price_id, 'price_test_456')
        self.assertEqual(p.stripe_session_id, 'cs_test_789')
        self.assertEqual(p.stripe_status, 'open')

    def test_create_payment_amount_must_be_positive(self):
        self.auth()
        resp = self.client.post(self.create_url, data={
            'course_id': self.course.id,
            'amount': '0'
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('users.stripe_service.retrieve_session')
    def test_payment_status_updates(self, m_retrieve):
        self.auth()
        # Prepare a payment with existing session id
        p = Payment.objects.create(
            user=self.user,
            course=self.course,
            amount=100,
            method=Payment.Method.STRIPE,
            stripe_session_id='cs_test_abc',
            stripe_status='open',
        )
        url = reverse('payment-status', args=[p.id])
        m_retrieve.return_value = {'id': 'cs_test_abc', 'status': 'complete'}

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        p.refresh_from_db()
        self.assertEqual(p.stripe_status, 'complete')


class UserDeactivationTaskTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        # Users to test deactivation logic
        now = timezone.now()
        self.active_recent = User.objects.create_user(email='recent@test.local', password='pass12345')
        self.active_recent.last_login = now - timedelta(days=5)
        self.active_recent.save(update_fields=['last_login'])

        self.active_old = User.objects.create_user(email='old@test.local', password='pass12345')
        self.active_old.last_login = now - timedelta(days=60)
        self.active_old.save(update_fields=['last_login'])

        self.active_never = User.objects.create_user(email='never@test.local', password='pass12345')
        # last_login remains None

        self.inactive_old = User.objects.create_user(email='inactive@test.local', password='pass12345', is_active=False)
        self.inactive_old.last_login = now - timedelta(days=90)
        self.inactive_old.save(update_fields=['last_login'])

    def test_deactivate_inactive_users_task(self):
        from .tasks import deactivate_inactive_users
        updated_count = deactivate_inactive_users()
        # Should deactivate: active_old and active_never (2 users)
        self.assertEqual(updated_count, 2)

        # Refresh from DB
        for u in [self.active_recent, self.active_old, self.active_never, self.inactive_old]:
            u.refresh_from_db()

        self.assertTrue(self.active_recent.is_active)
        self.assertFalse(self.active_old.is_active)
        self.assertFalse(self.active_never.is_active)
        # Already inactive remains inactive
        self.assertFalse(self.inactive_old.is_active)
