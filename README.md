# django-field-permissions

Adds object-level permissions via a model instance method, and a mechanism for consulting static per-field ``auth.Permissions``.  Offers hooks for per-object per-field runtime permission checks that ignore static permission if you don't want to use them.

Built on Python 3.5 on Django 1.9 (definitely requires Django 1.8+ because of the use of the simplified field access API)

## How it works
_Runtime per-object checks, auth.Permission (or arbitrary callable) for fields._

We make you declare a ``has_perm(user, perm)`` on any model that requires object-level checks.  You can ignore this method if you don't care very much about object-level checks; the default one won't get in your way.

Static per-field permissions are defined via Django's [custom permissions](https://docs.djangoproject.com/es/1.9/topics/auth/customizing/#custom-permissions) system, patterned as ``can_change_{model}_{fieldname}``, which is the standard permission label just with a suffix of the field in question.  Only fields nominated in this way will be checked by the system, and all others allow edits by default.

You then assign these permissions the usual way (to ``auth.Group`` instances or specific users).  If ``user.has_perm('can_change_mymodel_myfield')`` returns True, then by default ``instance.has_field_perm(user, 'myfield')`` will return True as well.

Optionally, ``has_field_perm(user, fieldname)`` will look for model hooks named ``can_change_FOO(user)``.  Even if a user lacks the required ``auth.Permission``, you can return True from ``instance.can_change_myfield(user)``, allowing you to completely ignore the static ``auth.Permission`` system.

Finally, if you really freaky, you can declare instead a class-level dictionary ``field_permissions`` on your model which associates model field names to an arbitrary perm label or callable.  Fields given in this dictionary will not bother to consult any other mechanism described above, so be comprehensive.

## Installation

Grab a copy of the code from the repository:

```shell
pip install git+https://github.com/tiliv/django-field-permissions#egg=field_permissions
```

Add it to your ``settings.INSTALLED_APPS`` and tell Django about our object-level permission auth backend:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'field_permissions',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # keep this bad boy
    'field_permissions.backends.InstancePermissionBackend',
]
```

## Usage

Add the provided mixin to any models that should be made aware of object-level or field-level permissions:

```python
# myapp/models.py
from django.db import models
from field_permissions.models import FieldPermissionModelMixin

class MyModel(FieldPermissionModelMixin, models.Model):
    # ...
```


#### Using ``auth.Permission`` for static permissions

Define some Django [custom permissions](https://docs.djangoproject.com/es/1.9/topics/auth/customizing/#custom-permissions) on your model for any fields that you want to opt into the permission system:

```python
# models.py
from django.db import models
from django.conf import settings
from field_permissions.models import FieldPermissionModelMixin
class Post(FieldPermissionModelMixin, models.Model):
    """ A user forum post. """
    name = models.CharField(max_length=50)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    class Meta:
        permissions = (
            ('can_change_post_name', "Can change post name"),
            ('can_change_post_content', "Can change post content"),
        )
```

Make sure you get those permissions created in your database:

```python
./manage.py makemigrations myapp
./manage.py migrate myapp
```

Now assign them to users or groups that require the permission.

At this point, you can use ``mypost.has_field_perm(user, 'name')`` to see if the user has the baseline static permission for the named field.  (You could of course use the standard mechanism to ask for this permission: ``user.has_perm('myapp.can_change_post_name')``.  Nothing about this is object-level, but by overriding the method on your model you can change that to suit your needs.)

#### Object-level hooks

You can choose whether or not you want to use static ``auth.Permission`` assignments alongside the object-level hooks named ``can_change_FOO(user)``.  (This naming scheme was chosen for its similarity to the Django admin app's permission hooks.)

By default, the hooks do nothing, but by overriding them and returning True or False, you can allow the object to choose at runtime what is allowed for the given user, regardless of their assigned permission.

Extending our ``Post`` example model from earlier, we can provide these hooks for fields represented in ``Meta.permissions`` list:

```python
class Post(FieldPermissionModelMixin, models.Model):
    """ A user forum post. """
    name = models.CharField(max_length=50)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    class Meta:
        permissions = (
            ('can_change_post_name', "Can change post name"),
            ('can_change_post_content', "Can change post content"),
        )

    def can_change_name(self, user):
        return self.user == user or user.is_staff

    def can_change_content(self, user):
        return self.user == user or user.is_staff
```

Note that this works specifically because these fields are represented in ``Meta.permissions``.  If you don't want to use the auth permission system at all, you can do so by offering the model a different system for nominating fields for the underlying ``has_field_perm()`` method to automatically discover:

```python
class Post(FieldPermissionModelMixin, models.Model):
    """ A user forum post. """
    name = models.CharField(max_length=50)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    def can_change_name(self, user, **kwargs):
        return self.user == user or user.is_staff

    def can_change_content(self, user, **kwargs):
        return self.user == user or user.is_staff

    field_permissions = {
        'name': can_change_name,
        'content': can_change_content,
    }
```

In this example, the callbacks must accept an additional ``field`` keyword argument.  If you're using separate callbacks for every field, that argument is redundant, so the example replaced it with ``**kwargs``.

If you were instead factoring out the copy-pasted check, you might use this instead:

```python
def is_owner_or_staff(obj, user, field):
    return obj.user == user or user.is_staff

class Post(FieldPermissionModelMixin, models.Model):
    field_permissions = {
        'name': is_owner_or_staff,
        'content': is_owner_or_staff,
    }

    # ...
```

You shouldn't be modifying the class-level dictionary at runtime.  It's not thread-safe.

Finally, you could supply an arbitrary perm label in the dictionary, although this is going back to just a static permission system:

```python
class Post(FieldPermissionModelMixin, models.Model):
    field_permissions = {
        'name': 'myapp.can_do_thing_one',
        'content': 'myapp.can_do_thing_two',
    }

    # ...
```


#### Field permissions in forms and serializers

Field permissions are not something that Django, its forms, or its many API packages know about, on account of us making them up.  The ``has_field_perm()`` and various ``can_change_FOO()`` hooks let you opt into the system, but nothing will consult those hooks unless you make them do so.

Subclass the appropriate mixin to have unauthorized fields dealt with:

```python
# forms.py
from django import forms
from field_permissions.forms import FieldPermissionsFormMixin
from .models import Post

class PostForm(FieldPermissionsFormMixin, forms.ModelForm):
    class Meta:
        model = Post
        fields = ('name', 'content')

# serializers.py
from rest_framework import serializers
from field_permissions.api.rest_framework import FieldPermissionSerializerMixin
from .models import Post

class PostSerializer(FieldPermissionSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('name', 'content')

```

The form requires a ``user`` keyword argument in its ``__init__()`` method, so arrange to send it one in your view (probably via ``get_form_kwargs()`` if you're using a class-based view).

It's not clear with vanilla Django forms what it means to have a "read only" field, so the default behavior of the forms mixin is to simply remove fields that the user doesn't have permission to edit.  If you would like something else to happen instead, override your form's ``remove_unauthorized_field(fieldname)`` method and do whatever is required (changing the widget, etc).

#### Advanced customization

The ``field_permissions.models.FieldPermissionModelMixin`` makes a couple of assumptions about how permissions are named.  The relevant settings are stored on the mixin itself so that they may be customized per-model (or even per-instance, if you the freaky type).

The following is how the mixin controls which permission codenames it wants to discover in your model's custom ``Meta.permissions`` list.

```python
class FieldPermissionModelMixin:
    # Custom permission codename expected in Meta.permissions
    FIELD_PERM_CODENAME = 'can_change_{model}_{name}'

    # Per-field hook name for runtime checks
    FIELD_PERMISSION_GETTER = 'can_change_{name}'

    # The permission granted to any user when asking about a field
    # not found in the model's Meta.permissions or field_permissions dict.
    # Setting this to False would mean that any field not named in the
    # permission configuration is assumed off limits for any user.
    FIELD_PERMISSION_MISSING_DEFAULT = True

    # ...
```
