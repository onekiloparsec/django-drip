import sys

from django.db.models import ForeignKey, ManyToManyField, OneToOneField
from django.db.models.fields.related import ForeignObjectRel
from django.apps import apps

# taking a nod from python-requests and skipping six
_ver = sys.version_info
is_py2 = (_ver[0] == 2)
is_py3 = (_ver[0] == 3)

basestring = (str, bytes)
unicode = str


def get_fields(Model,
               parent_field="",
               model_stack=None,
               stack_limit=2,
               excludes=['permissions', 'comment', 'content_type']):
    """
    Given a Model, return a list of lists of strings with important stuff:
    ...
    ['test_user__user__customuser', 'customuser', 'User', 'ForeignObjectRel']
    ['test_user__unique_id', 'unique_id', 'TestUser', 'CharField']
    ['test_user__confirmed', 'confirmed', 'TestUser', 'BooleanField']
    ...

     """
    out_fields = []

    if model_stack is None:
        model_stack = []

    # github.com/omab/python-social-auth/commit/d8637cec02422374e4102231488481170dc51057
    if isinstance(Model, basestring):
        app_label, model_name = Model.split('.')
        Model = apps.get_model(app_label, model_name)

    all_related_objects = [
        f for f in Model._meta.get_fields()
        if (f.one_to_many or f.one_to_one) and f.auto_created and not f.concrete
    ]

    fields = Model._meta.fields + Model._meta.many_to_many + tuple(all_related_objects)
    model_stack.append(Model)

    # do a variety of checks to ensure recursion isnt being redundant

    stop_recursion = False
    if len(model_stack) > stack_limit:
        # rudimentary CustomUser->User->CustomUser->User detection
        if model_stack[-3] == model_stack[-1]:
            stop_recursion = True

        # stack depth shouldn't exceed x
        if len(model_stack) > 5:
            stop_recursion = True

        # we've hit a point where we are repeating models
        if len(set(model_stack)) != len(model_stack):
            stop_recursion = True

    if stop_recursion:
        return []  # give empty list for "extend"

    for field in fields:
        field_name = field.name

        if isinstance(field, ForeignObjectRel):
            field_name = field.field.related_query_name()

        if parent_field:
            full_field = "__".join([parent_field, field_name])
        else:
            full_field = field_name

        if len([True for exclude in excludes if (exclude in full_field)]):
            continue

        # add to the list
        out_fields.append([full_field, field_name, Model, field.__class__])

        if (not stop_recursion and
                (isinstance(field, ForeignKey) or isinstance(field, OneToOneField) or
                 isinstance(field, ForeignObjectRel) or isinstance(field, ManyToManyField))):

            if isinstance(field, ForeignObjectRel):
                RelModel = field.model
            else:
                RelModel = field.related_model

            out_fields.extend(get_fields(RelModel, full_field, list(model_stack)))

    return out_fields


def give_model_field(full_field, Model):
    """
    Given a field_name and Model:

    "test_user__unique_id", <AchievedGoal>

    Returns "test_user__unique_id", "id", <Model>, <ModelField>
    """
    field_data = get_fields(Model, '', [])

    for full_key, name, _Model, _ModelField in field_data:
        if full_key == full_field:
            return full_key, name, _Model, _ModelField

    raise Exception('Field key `{0}` not found on `{1}`.'.format(full_field, Model.__name__))


def get_simple_fields(Model, **kwargs):
    return [[f[0], f[3].__name__] for f in get_fields(Model, **kwargs)]
