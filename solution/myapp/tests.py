from myapp.models import ContactModel
from django.contrib.auth.models import User,Permission
import pytest
from pytest_drf import (
    ViewSetTest,
    Returns200,
    Returns201,
    Returns204,
    Returns403,
    UsesGetMethod,
    UsesDeleteMethod,
    UsesDetailEndpoint,
    UsesListEndpoint,
    UsesPatchMethod,
    UsesPostMethod,
)
from pytest_drf.util import pluralized, url_for
from pytest_lambda import lambda_fixture, static_fixture
from pytest_assert_utils import assert_model_attrs
from rest_framework.test import APIClient

def express1(contact):
    return {
        "id": contact.id,
        "name": contact.name,
        "email": contact.email,
    }

express = pluralized(express1)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


class TestsBase(ViewSetTest):
    list_url = lambda_fixture(lambda: url_for("contacts-list"))
    detail_url = lambda_fixture(
        lambda contact: url_for("contacts-detail", contact.pk)
    )
    contacts = lambda_fixture(
        lambda: [
            ContactModel.objects.create(name=e, email=e)
            for e in [
                "a@b.com",
                "a@c.com",
                "a@d.com",
            ]
        ],
        autouse=True,
    )
    @pytest.fixture
    def users(self):
        def create(**kwargs):
            pw = kwargs.pop('password')
            perm = kwargs.pop('permission',None)
            u = User.objects.create(**kwargs)
            u.set_password(pw)
            if perm:
                perm = Permission.objects.get(codename=perm)
                u.user_permissions.add(perm)
            u.save()

        args=[
            dict(username="admin", is_superuser=True,password='1'),
            dict(username="reader",password='1',permission=('view_contactmodel')),
            dict(username="writer",password='1',permission=('add_contactmodel')),
            dict(username="deleter",password='1',permission=('delete_contactmodel')),
        ]

        [create(**e ) for e in args]

    contact = lambda_fixture(
        lambda: ContactModel.objects.create(
            name="a@z.com", email="a@z.com"
        ),
        autouse=True,
    )

    @pytest.fixture
    def client(self, users):
        client = APIClient()
        client.login(username=self.username, password="1")
        return client

# test viewset
class TestContactViewSet(TestsBase):
    username = 'admin'

    class TestList(
        UsesGetMethod,
        UsesListEndpoint,
        Returns200,
    ):
        def test_it(self, json, contacts, contact):
            expected = [express1(contact)] + express(contacts)
            actual = json
            assert expected == actual

    class TestCreate(
        UsesPostMethod,
        UsesListEndpoint,
        Returns201,
    ):
        data = static_fixture(dict(name="a", email="b@c.com"))

        ids = lambda_fixture(
            lambda: set(
                ContactModel.objects.values_list("id", flat=True)
            )
        )

        def test(self, ids, json):
            expected = ids | {json["id"]}
            actual = set(
                ContactModel.objects.values_list("id", flat=True)
            )
            assert expected == actual

        def test_sets_attrs(self, data, json):
            actual = ContactModel.objects.get(pk=json["id"])

            expected = data
            assert_model_attrs(actual, expected)

        def test_returns_contact(self, json):
            contact = ContactModel.objects.get(pk=json["id"])

            expected = express1(contact)
            actual = json
            assert expected == actual

    class TestRetrieve(
        UsesGetMethod,
        UsesDetailEndpoint,
        Returns200,
    ):
        def test(self, contact, json):
            expected = express1(contact)
            actual = json
            assert expected == actual

    class TestUpdate(
        UsesPatchMethod,
        UsesDetailEndpoint,
        Returns200,
    ):
        data = static_fixture(dict(name="newname!", email="a@b.com"))

        def test_sets_attrs(self, data, contact):
            # We must tell Django to grab fresh data from the database, or we'll
            # see our stale initial data and think our endpoint is broken!
            contact.refresh_from_db()

            expected = data
            assert_model_attrs(contact, expected)

        def test_returns(self, contact, json):
            contact.refresh_from_db()

            expected = express1(contact)
            actual = json
            assert expected == actual

    class TestDestroy(
        UsesDeleteMethod,
        UsesDetailEndpoint,
        Returns204,
    ):
        ids = lambda_fixture(
            lambda contact: set(  # ensure our to-be-deleted ContactModel exists in our set
                ContactModel.objects.values_list("id", flat=True)
            )
        )

        def test(self, ids, contact):
            expected = ids - {contact.id}
            actual = set(
                ContactModel.objects.values_list("id", flat=True)
            )
            assert expected == actual

# test user access rights
class TestReader(TestsBase,UsesListEndpoint,Returns200):
    username='reader'
    class TestList(
        UsesGetMethod,
        UsesListEndpoint,
        Returns200,
    ):
        pass
    class TestCreate(
        UsesPostMethod,
        UsesListEndpoint,
        Returns403,
    ):
        pass
    class TestDestroy(
        UsesDeleteMethod,
        UsesDetailEndpoint,
        Returns403,
    ):
        pass

class TestWriter(TestsBase,UsesListEndpoint,Returns200):
    username='writer'
    class TestList(
        UsesGetMethod,
        UsesListEndpoint,
        Returns200,
    ):
        pass
    class TestCreate(
        UsesPostMethod,
        UsesListEndpoint,
        Returns201,
    ):
        data = static_fixture(dict(name="a", email="b@c.com"))

        ids = lambda_fixture(
            lambda: set(
                ContactModel.objects.values_list("id", flat=True)
            )
        )

        def test(self, ids, json):
            expected = ids | {json["id"]}
            actual = set(
                ContactModel.objects.values_list("id", flat=True)
            )
            assert expected == actual

    class TestDestroy(
        UsesDeleteMethod,
        UsesDetailEndpoint,
        Returns403,
    ):
        pass

class TestDeleter(TestsBase,UsesListEndpoint,Returns200):
    username='deleter'
    class TestList(
        UsesGetMethod,
        UsesListEndpoint,
        Returns200,
    ):
        pass
    class TestCreate(
        UsesPostMethod,
        UsesListEndpoint,
        Returns403,
    ):
        data = static_fixture(dict(name="a", email="b@c.com"))

    class TestDestroy(
        UsesDeleteMethod,
        UsesDetailEndpoint,
        Returns204,
    ):
        pass


"""
@pytest.fixture
def api_client(client):
    user = User.objects.create_user(username='haut_u', email='', password='1')
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    return client

@pytest.mark.django_db
def test_name_of_your_test(api_client):
    # Add your logic here
    url = reverse('img')
    response = api_client.get(url)
    print(registry.apps.get_app_configs()) # my app is printed

    print(response)
    r = dict(
        data = response.data,
        content = response.content,
    json = response.json())

    print('data',r)
    assert response.status_code == status.HTTP_200_OK
    # your asserts

def skip_test_api_jwt(self):
    resp = self.client.post(
        url,
        {"email": "", "password": "pass"},
        format="json",
    )
    self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertEqual(resp.status_code, status.HTTP_200_OK)
    self.assertTrue("token" in resp.data)

    self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
    client.credentials(HTTP_AUTHORIZATION="JWT " + token)
"""
