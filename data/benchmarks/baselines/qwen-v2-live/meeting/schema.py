"""Same strict schemas used in the API and local validation."""
TYPES = ['decision', 'action', 'issue', 'request_feedback', 'unresolved']
STATUSES = ['confirmed', 'needs_confirmation', 'unresolved', 'insufficient_information']
KINDS = ['proposal', 'support', 'objection', 'change', 'defer', 'finalize',
         'assign', 'issue', 'request_feedback', 'other']


def obj(properties):
    return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)


STR = {'type': 'string'}
NULL_STR = {'type': ['string', 'null']}
EVIDENCE = obj(dict(turn_id=STR, quote=STR))
EVENT = obj(dict(turn_id=STR, kind=dict(type='string', enum=KINDS), quote=STR))
TOPIC = obj(dict(topic=STR, events=dict(type='array', items=EVENT)))
STAGE_ONE = obj(dict(topics=dict(type='array', items=TOPIC)))
ITEM = obj(dict(id=STR, topic=STR, type=dict(type='string', enum=TYPES),
                status=dict(type='string', enum=STATUSES), content=STR, owner=NULL_STR,
                due=NULL_STR, evidence=dict(type='array', items=EVIDENCE), reason=STR,
                history=dict(type='array', items=EVENT)))
STAGE_TWO = obj(dict(items=dict(type='array', items=ITEM)))
VERDICT = dict(type='string', enum=['pass', 'fail', 'uncertain'])
CHECK_FIELDS = ['supported', 'topic_correct', 'current', 'conditions_preserved', 'assignment_supported']
SEMANTIC_CHECK = obj(dict(item_id=STR, **{key: VERDICT for key in CHECK_FIELDS},
                          reason=STR, evidence=dict(type='array', items=EVIDENCE)))
SEMANTIC = obj(dict(checks=dict(type='array', items=SEMANTIC_CHECK)))
# Models select references; application code copies the source quote exactly.
# Public output retains the original evidence schema.
REFERENCE = obj(dict(turn_id=STR))
MODEL_EVENT = obj(dict(turn_id=STR, kind=dict(type='string', enum=KINDS)))
MODEL_STAGE_ONE = obj(dict(topics=dict(type='array', items=obj(dict(
    topic=STR, events=dict(type='array', items=MODEL_EVENT))))))
MODEL_ITEM = obj({**ITEM['properties'], 'evidence':dict(type='array',items=REFERENCE),
                  'history':dict(type='array',items=MODEL_EVENT)})
MODEL_STAGE_TWO = obj(dict(items=dict(type='array',items=MODEL_ITEM)))
MODEL_SEMANTIC = obj(dict(checks=dict(type='array',items=obj({
    **SEMANTIC_CHECK['properties'], 'evidence':dict(type='array',items=REFERENCE)}))))


def schema_errors(value, schema, path='$'):
    """Validate our bounded schema subset without installing a third-party package."""
    errors = []
    kind = schema['type']
    if isinstance(kind, list):
        if value is None and 'null' in kind:
            return []
        kind = 'string'
    correct = {'object': isinstance(value, dict), 'array': isinstance(value, list),
               'string': isinstance(value, str)}.get(kind, False)
    if not correct:
        return [f'{path}: sai kiểu {kind}']
    if 'enum' in schema and value not in schema['enum']:
        errors.append(f'{path}: giá trị ngoài enum')
    if kind == 'object':
        for name in schema['required']:
            if name not in value:
                errors.append(f'{path}.{name}: thiếu trường')
        for name, val in value.items():
            if name not in schema['properties']:
                errors.append(f'{path}.{name}: trường không được hỗ trợ')
            else:
                errors.extend(schema_errors(val, schema['properties'][name], f'{path}.{name}'))
    if kind == 'array':
        for i, val in enumerate(value):
            errors.extend(schema_errors(val, schema['items'], f'{path}[{i}]'))
    return errors
