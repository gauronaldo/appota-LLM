"""Pure scoring functions; no model calls or filesystem writes."""

def same_content(actual, expected):
    return (actual['type'] == expected['type'] and actual['topic'].casefold() == expected['topic'].casefold()
            and expected['contains'].casefold() in actual['content'].casefold()
            and all(condition.casefold() in actual['content'].casefold()
                    for condition in expected.get('conditions', [])))


def score(result, expected):
    rows, gold = result['items'], expected['items']
    used, errors = set(), []
    if result.get('error'):
        errors.append('Pipeline không xử lý được input: ' + result['error']['message'])
    for g in gold:
        found = next((i for i, a in enumerate(rows) if i not in used and same_content(a, g)), None)
        if found is None:
            errors.append(f'Thiếu/sai {g["type"]}: {g["topic"]} / {g["contains"]}')
            continue
        used.add(found)
        a = rows[found]
        for field in ['status', 'owner', 'due']:
            if a[field] != g[field]:
                errors.append(f'{g["topic"]}: {field} kỳ vọng {g[field]!r}, thực tế {a[field]!r}')
        if g['evidence_turn'] not in {ev['turn_id'] for ev in a['evidence']}:
            errors.append(f'{g["topic"]}: thiếu evidence kết luận {g["evidence_turn"]}')
    for i, a in enumerate(rows):
        if i not in used:
            errors.append(f'Mục ngoài kỳ vọng: {a["type"]} / {a["topic"]} / {a["content"]}')
    if result['review_queue']:
        errors.append(f'{len(result["review_queue"])} mục không qua validator')
    timeline_turns = {ev['turn_id'] for a in rows for ev in a['history']}
    for turn in expected['history_turns']:
        if turn not in timeline_turns:
            errors.append(f'Thiếu diễn biến {turn}')
    actual_decisions = [a for a in rows if a['type'] == 'decision' and a['status'] == 'confirmed']
    gold_decisions = [g for g in gold if g['type'] == 'decision' and g['status'] == 'confirmed']
    decision_used, tp = set(), 0
    for a in actual_decisions:
        match = next((i for i, g in enumerate(gold_decisions) if i not in decision_used and same_content(a, g)), None)
        if match is not None:
            decision_used.add(match)
            tp += 1
    intermediate = set(expected['intermediate_turns'])
    promoted = set()
    for a in actual_decisions:
        if not any(same_content(a, g) for g in gold_decisions):
            promoted.update(intermediate & {ev['turn_id'] for ev in a['evidence']})
    invented = 0
    for a in rows:
        if a['type'] != 'action':
            continue
        matches = [g for g in gold if same_content(a, g)]
        for field in ['owner', 'due']:
            if a[field] is not None and not any(a[field] == g[field] for g in matches):
                invented += 1
    expectation = '; '.join(f'{g["type"]}/{g["topic"]}: {g["contains"]} ({g["status"]}, owner={g["owner"]}, due={g["due"]}, conditions={g.get("conditions", [])})' for g in gold)
    actual = ('Lỗi pipeline: ' + result['error']['message']) if result.get('error') else ('; '.join(f'{a["type"]}/{a["topic"]}: {a["content"]} ({a["status"]}, owner={a["owner"]}, due={a["due"]})' for a in rows) or 'Không có mục')
    return dict(id=expected['id'], title=expected['title'], group=expected.get('group'),
                input_format=expected.get('input_format'), dataset_version=expected.get('dataset_version'),
                passed=not errors, errors=errors,
                expectation=expectation, actual=actual, lesson=expected['lesson'],
                metrics=dict(decision_tp=tp, decision_fp=len(actual_decisions)-tp,
                             decision_fn=len(gold_decisions)-tp, intermediate_promoted=len(promoted),
                             intermediate_total=len(intermediate), invented_owner_due=invented))
