(function () {
  'use strict';
  var KIND = { question: '의뢰사 확인 질문', change: '매뉴얼 수정 제안' };
  var DECISION = { adopt: '채택', reject: '채택 안 함', hold: '보류', answer: '답변함' };
  var NEED = {
    always: ['항상 권장', 'need-always'], needed: ['필요 (질문 답 기준)', 'need-yes'],
    not_needed: ['불필요 (질문 답 기준)', 'need-no'], pending: ['질문 답 대기', 'need-pending']
  };
  var state = { items: [], selected: null, saving: false };
  var $ = function (id) { return document.getElementById(id); };

  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) return;
      if (k === 'text') n.textContent = v;
      else if (k === 'class') n.className = v;
      else if (k.slice(0, 2) === 'on') n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v === true ? '' : v);
    });
    (kids || []).forEach(function (c) { if (c) n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return n;
  }
  function tag(text, cls) { return el('span', { class: 'tag ' + (cls || ''), text: text }); }
  function say(msg, cls) {
    var s = $('status'); s.className = 'status ' + (cls || ''); s.textContent = msg || '';
    if (cls === 'ok') setTimeout(function () { if (s.textContent === msg) s.textContent = ''; }, 4000);
  }
  function decided(it) { return it.decision && it.decision.verdict !== 'hold'; }
  function byId(id) { return state.items.find(function (i) { return i.id === id; }); }
  function answerLabel(q) {
    var d = q.decision;
    if (!d || d.verdict !== 'answer') return '';
    var o = q.options.find(function (x) { return x.id === d.resolution; });
    return o ? o.label : '';
  }

  function apply(data) {
    state.items = data.items || [];
    $('source-name').textContent = data.source_name ? '대상 매뉴얼: ' + data.source_name : '';
    var w = $('warning'); w.hidden = !data.warning; w.textContent = data.warning || '';
  }

  function load() {
    $('list').replaceChildren(el('li', { class: 'loading', text: '불러오는 중…' }));
    return fetch('/api/review', { headers: { Accept: 'application/json' } }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    }).then(function (d) { apply(d); render(); }).catch(function (e) {
      $('list').replaceChildren();
      $('detail').replaceChildren(el('div', { class: 'errbox', role: 'alert' }, [
        el('p', { text: '데이터를 불러오지 못했습니다: ' + e.message }),
        el('button', { class: 'btn', type: 'button', text: '다시 시도', onclick: load })
      ]));
    });
  }

  function filtered() {
    var k = $('f-kind').value, s = $('f-state').value, q = $('f-q').value.trim().toLowerCase();
    return state.items.filter(function (it) {
      if (k && it.kind !== k) return false;
      if (s === 'open' && decided(it)) return false;
      if (s === 'done' && !decided(it)) return false;
      if (s === 'conflict' && !it.conflict) return false;
      if (q && JSON.stringify(it).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
  }

  function renderSummary() {
    var qs = state.items.filter(function (i) { return i.kind === 'question'; });
    var cs = state.items.filter(function (i) { return i.kind === 'change'; });
    var cnt = function (arr, f) { return arr.filter(f).length; };
    var stats = [
      ['질문 답변', cnt(qs, decided) + ' / ' + qs.length],
      ['제안 결정', cnt(cs, decided) + ' / ' + cs.length],
      ['필요한 제안', cnt(cs, function (c) { return c.need === 'needed' || c.need === 'always'; })],
      ['채택', cnt(cs, function (c) { return c.decision && c.decision.verdict === 'adopt'; })],
      ['모순', cnt(cs, function (c) { return c.conflict; })]
    ];
    $('summary').replaceChildren.apply($('summary'), stats.map(function (s) {
      return el('div', { class: 'stat' + (s[0] === '모순' && s[1] ? ' bad' : '') }, [el('b', { text: String(s[1]) }), el('span', { text: s[0] })]);
    }));
  }

  function renderList() {
    var rows = filtered();
    $('count').textContent = '표시 ' + rows.length + ' / 전체 ' + state.items.length + '건';
    var ul = $('list');
    if (!rows.length) { ul.replaceChildren(el('li', { class: 'empty', text: '조건에 맞는 항목이 없습니다.' })); return rows; }
    ul.replaceChildren.apply(ul, rows.map(function (it) {
      var meta = [tag(KIND[it.kind], it.kind)];
      if (it.kind === 'change') { meta.push(tag(it.priority)); meta.push(tag(NEED[it.need][0], NEED[it.need][1])); }
      meta.push(it.decision ? tag(DECISION[it.decision.verdict], it.decision.verdict)
        : it.previous_decision ? tag('문구 변경 · 재결정 필요', 'conflict') : tag(it.rev ? '새 항목' : '미결정', 'none'));
      if (it.kind === 'question' && answerLabel(it)) meta.push(el('span', { text: '→ ' + answerLabel(it) }));
      if (it.conflict) meta.push(tag('모순', 'conflict'));
      return el('li', null, [el('button', {
        type: 'button', class: 'item' + (decided(it) ? ' done' : '') + (it.conflict ? ' bad' : ''), role: 'option',
        'aria-selected': it.key === state.selected ? 'true' : 'false', 'data-key': it.key,
        onclick: function () { select(it.key, true); }
      }, [el('div', { class: 't', text: it.id + '. ' + it.title }), el('div', { class: 'm' }, meta)])]);
    }));
    return rows;
  }

  function block(title, text, cls) {
    return el('section', { class: 'block ' + (cls || '') }, [el('h3', { text: title }), el('div', { class: 'fulltext', text: text })]);
  }

  function linkTo(id) {
    var t = byId(id);
    return el('button', { type: 'button', class: 'btn ghost', text: id + (t ? ' ' + t.title : ''), onclick: function () {
      $('f-kind').value = ''; $('f-state').value = ''; $('f-q').value = ''; select(t.key, true);
    } });
  }

  function questionDetail(it, kids) {
    kids.push(block('왜 필요한 질문인가요?', it.why));
    kids.push(el('h3', { text: '답을 고르세요' }));
    var d = it.decision || {};
    var fs = el('fieldset', { class: 'resolution' }, [el('legend', { text: '답변 (하나 선택)' })]);
    it.options.forEach(function (o) {
      var id = 'r-opt-' + o.id;
      fs.appendChild(el('label', { class: 'choice-option' + (it.recommended === o.id ? ' recommended' : ''), for: id }, [
        el('input', { type: 'radio', name: 'answer', id: id, value: o.id, checked: d.verdict === 'answer' && d.resolution === o.id }),
        el('span', null, [el('strong', null, [o.label, it.recommended === o.id ? tag('추천', 'recommended') : null]),
          el('small', { text: '이 답을 고르면: ' + o.effect })])
      ]));
    });
    var holdId = 'r-opt-hold';
    fs.appendChild(el('label', { class: 'choice-option', for: holdId }, [
      el('input', { type: 'radio', name: 'answer', id: holdId, value: '', checked: d.verdict === 'hold' }),
      el('span', null, [el('strong', { text: '아직 모름 (보류)' }), el('small', { text: '의뢰사 확인 후 다시 답합니다. 관련 제안은 ‘질문 답 대기’로 남습니다.' })])
    ]));
    if (it.affects.length) {
      kids.push(el('p', { class: 'saved', text: '이 답에 따라 필요 여부가 바뀌는 제안:' }));
      kids.push(el('div', { class: 'related' }, it.affects.map(linkTo)));
    }
    if (it.legacy && it.legacy.length) {
      kids.push(el('div', { class: 'legacy' }, [el('strong', { text: '이전 검토 화면에서 남긴 답 (참고, 자동 반영하지 않음)' })].concat(it.legacy.map(function (l) {
        return el('p', { text: '· ' + l.label + (l.note ? ' — 메모: ' + l.note : '') + (l.reviewer ? ' (' + l.reviewer + ')' : '') });
      }))));
    }
    kids.push(form(it, fs, function (f) {
      var c = f.querySelector('input[name=answer]:checked');
      if (!c) return null;
      return c.value ? { verdict: 'answer', resolution: c.value } : { verdict: 'hold', resolution: '' };
    }, '답을 고르세요. 모르면 ‘아직 모름’을 고르세요.'));
  }

  function changeDetail(it, kids) {
    var need = NEED[it.need];
    kids.push(el('div', { class: 'need ' + need[1] }, [
      el('strong', { text: need[0] }),
      el('p', { text: '적용 조건: ' + it.requires_text })
    ]));
    var qids = [];
    (it.requires || []).forEach(function (alt) { Object.keys(alt).forEach(function (q) { if (qids.indexOf(q) < 0) qids.push(q); }); });
    if (qids.length) {
      kids.push(el('div', { class: 'related' }, qids.map(function (q) {
        var t = byId(q), b = linkTo(q);
        b.textContent = q + ': ' + (answerLabel(t) || (t.decision ? '보류' : '미답변'));
        return b;
      })));
    }
    if (it.conflict) kids.push(el('p', { class: 'conflict-msg', role: 'alert', text: '⚠ ' + it.conflict }));
    var cur = it.current_text || it.current.map(function (c) {
      return c.sheet + ' ' + c.row + '행  ' + c.field + ' | ' + c.type + ' | 필수 ' + (c.required || '(빈칸)') + '\n' + c.description;
    }).join('\n\n');
    kids.push(el('div', { class: 'cols' }, [block('현재 매뉴얼 (원본 그대로)', cur, 'src'), block('제안', it.proposed, 'prop')]));
    kids.push(block('왜 바꾸나요?', it.reason));
    if (it.example) kids.push(block('예시', it.example));
    var d = it.decision || {};
    var fs = el('fieldset', { class: 'resolution' }, [el('legend', { text: '이 제안을 매뉴얼 수정안에 넣을까요?' })]);
    [['adopt', '채택 — 수정 제안서에 포함'], ['reject', '채택 안 함 — 현재 매뉴얼 유지'], ['hold', '보류 — 나중에 결정']].forEach(function (v) {
      var id = 'r-' + v[0];
      fs.appendChild(el('label', { class: 'choice-option', for: id }, [
        el('input', { type: 'radio', name: 'verdict', id: id, value: v[0], checked: d.verdict === v[0] }),
        el('span', null, [el('strong', { text: v[1] })])
      ]));
    });
    kids.push(form(it, fs, function (f) {
      var c = f.querySelector('input[name=verdict]:checked');
      return c ? { verdict: c.value, resolution: '' } : null;
    }, '채택 여부를 고르세요.'));
  }

  function form(it, fieldset, read, missing) {
    var d = it.decision || {};
    var note = el('textarea', { id: 'r-note', rows: '3' }); note.value = d.note || '';
    var rev = el('input', { type: 'text', id: 'r-rev', autocomplete: 'name' });
    rev.value = d.reviewer || localStorage.getItem('reviewer') || '';
    var btn = el('button', { type: 'submit', class: 'btn', id: 'r-save', text: '저장' });
    var f = el('form', { id: 'review-form' }, [fieldset,
      el('label', { class: 'f', for: 'r-note' }, ['메모 (선택: 수정 의견, 보류 이유, 의뢰사 회신 등)', note]),
      el('label', { class: 'f', for: 'r-rev' }, ['검토자 이름 (선택)', rev]),
      el('div', null, [btn, ' ', el('span', { class: 'saved', text: d.updated_at ? '마지막 저장: ' + d.updated_at + (d.reviewer ? ' · ' + d.reviewer : '') : '아직 저장하지 않았습니다.' })])
    ]);
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var v = read(f);
      if (!v) { say(missing, 'err'); return; }
      save(it, btn, { key: it.key, verdict: v.verdict, resolution: v.resolution, note: note.value, reviewer: rev.value.trim() });
    });
    return f;
  }

  function renderDetail() {
    var d = $('detail');
    var it = state.items.find(function (i) { return i.key === state.selected; });
    if (!it) { d.replaceChildren(el('p', { class: 'empty', text: '왼쪽 목록에서 항목을 선택하세요.' })); return; }
    var kids = [
      el('h2', { text: it.id + '. ' + it.title }),
      el('div', { class: 'badges' }, [tag(KIND[it.kind], it.kind), it.kind === 'change' ? tag(it.priority) : null,
        it.kind === 'change' ? tag(it.sheet) : null])
    ];
    if (!it.decision && it.previous_decision) {
      var p = it.previous_decision, prev = p.verdict === 'answer'
        ? (it.options.find(function (o) { return o.id === p.resolution; }) || {}).label : DECISION[p.verdict];
      kids.push(el('p', { class: 'conflict-msg', role: 'alert', text: '재검토 후 문구가 바뀌어 다시 결정해야 합니다. 이전 결정: ' + prev + (p.note ? ' — 메모: ' + p.note : '') }));
    } else if (!it.decision && it.rev) {
      kids.push(el('p', { class: 'need need-yes', text: '재검토에서 새로 추가된 항목입니다.' }));
    }
    if (it.kind === 'question') questionDetail(it, kids); else changeDetail(it, kids);
    d.replaceChildren.apply(d, kids);
  }

  function save(it, btn, body) {
    if (state.saving) return;
    var order = filtered(), pos = order.findIndex(function (r) { return r.key === it.key; });
    var after = order.slice(pos + 1).concat(order.slice(0, pos)).map(function (r) { return r.key; });
    state.saving = true; btn.disabled = true; btn.textContent = '저장 중…';
    fetch('/api/decisions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          if (!r.ok) throw new Error(j.error || ('HTTP ' + r.status));
          return j;
        });
      }).then(function (data) {
        state.saving = false;
        if (body.reviewer) localStorage.setItem('reviewer', body.reviewer); else localStorage.removeItem('reviewer');
        apply(data);
        var saved = state.items.find(function (i) { return i.key === it.key; });
        var next = after.map(function (k) { return state.items.find(function (i) { return i.key === k; }); })
          .find(function (i) { return i && !decided(i); });
        var msg = '저장했습니다.' + (saved.conflict ? ' ⚠ ' + saved.conflict : '');
        if (saved.conflict || !next) { render(); select(it.key, false); }
        else { render(); select(next.key, true); msg += ' 다음 미결정 항목으로 이동했습니다.'; }
        say(msg, saved.conflict ? 'err' : 'ok');
      }).catch(function (e) {
        state.saving = false; btn.disabled = false; btn.textContent = '저장';
        say('저장 실패: ' + e.message, 'err');
      });
  }

  function select(key, focus) {
    state.selected = key; renderList(); renderDetail();
    var b = document.querySelector('.item[data-key="' + CSS.escape(key) + '"]');
    if (b) b.scrollIntoView({ block: 'nearest' });
    if (focus) $('detail').focus({ preventScroll: false });
  }

  function render() {
    renderSummary();
    var rows = renderList();
    if (!rows.some(function (r) { return r.key === state.selected; })) state.selected = rows.length ? rows[0].key : null;
    renderList(); renderDetail();
  }

  ['f-kind', 'f-state'].forEach(function (id) { $(id).addEventListener('change', render); });
  $('f-q').addEventListener('input', render);
  load();
})();
