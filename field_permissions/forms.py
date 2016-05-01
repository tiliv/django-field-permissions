from django import forms

class FieldPermissionFormMixin:
    """
    ModelForm logic for removing fields when a user is found not to have change permissions.
    """
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')

        super(FieldPermissionFormMixin, self).__init__(*args, **kwargs)

        model = self.Meta.model
        model_field_names = [f.name for f in model._meta.get_fields()]  # this might be too broad
        for name in model_field_names:
            if name in self.fields and not self.instance.has_field_perm(user, field=name):
                self.remove_unauthorized_field(name)

    def remove_unauthorized_field(self, name):
        del self.fields[name]


class FieldPermissionForm(FieldPermissionFormMixin, forms.ModelForm):
    pass
