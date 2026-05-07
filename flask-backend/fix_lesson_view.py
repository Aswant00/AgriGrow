with open(r'c:\Users\aswan\Projects\AgriGrow\AgriGrow.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

clean = (
    'function LessonView({ lesson, mod, appState, onCompleteLesson, onBack, onNext }) {\n'
    '  const [ans, setAns] = useState(null);\n'
    '  const c = lesson.content;\n'
    '  const done = appState.completedLessons.includes(lesson.id);\n'
    '  const idx = mod.lessons.findIndex(l => l.id === lesson.id);\n'
    '\n'
    '  useEffect(() => { setAns(null); }, [lesson.id]);\n'
    '\n'
    '  const pick = async (i) => {\n'
    '    if (ans !== null) return;\n'
    '    setAns(i);\n'
    '    if (c.quiz && i === c.quiz.ans && !done) await onCompleteLesson(lesson.id, lesson.pts);\n'
    '  };\n'
    '\n'
    '  return (\n'
    '    <div className="lesson-page">\n'
    '      <button className="back-btn" onClick={onBack}><Icon name="arrow_back" size={14} />{mod.title}</button>\n'
    '      {lesson.expertVerified && <div className="expert-box"><Icon name="verified_user" size={16} />This lesson has been verified by an agricultural expert.</div>}\n'
    '      <div className="lesson-hdr">\n'
    "        <h2>{c.heading}</h2>\n"
    "        <div style={{ display: 'flex', gap: 12, fontSize: 12, color: '#555', flexWrap: 'wrap' }}>\n"
    '          <span>Lesson {idx + 1}/{mod.lessons.length}</span>\n'
    "          <span style={{ color: '#f57c00', fontWeight: 700 }}><Icon name=\"star\" size={12} color=\"#f57c00\" /> {lesson.pts} pts</span>\n"
    "          {done && <span style={{ color: '#2e7d32', fontWeight: 700 }}><Icon name=\"check_circle\" size={12} color=\"#2e7d32\" /> Done</span>}\n"
    '        </div>\n'
    '      </div>\n'
    '      <div className="content-block">\n'
    '        {c.sections.map((s, i) => {\n'
    "          if (s.type === 'p')   return <p key={i}>{s.text}</p>;\n"
    "          if (s.type === 'h3')  return <h3 key={i}>{s.text}</h3>;\n"
    '          if (s.type === \'tip\') return <div key={i} className="tip-block"><Icon name="lightbulb" size={16} color="#f9a825" /><span>{s.text}</span></div>;\n'
    "          if (s.type === 'ul')  return <ul key={i}>{s.items.map((it, j) => <li key={j}>{it}</li>)}</ul>;\n"
    '          return null;\n'
    '        })}\n'
    '      </div>\n'
    '      {c.quiz ? (\n'
    '        <div className="quiz-box">\n'
    '          <div className="quiz-q"><Icon name="quiz" size={16} color="#4a148c" />{c.quiz.q}</div>\n'
    '          <div className="quiz-opts">\n'
    "            {c.quiz.opts.map((opt, i) => (\n"
    '              <button key={i} className={`quiz-opt ${ans === i ? (i === c.quiz.ans ? \'correct\' : \'wrong\') : \'\'}`} onClick={() => pick(i)}>{opt}</button>\n'
    '            ))}\n'
    '          </div>\n'
    '          {ans !== null && (\n'
    "            <div className={`quiz-result ${ans === c.quiz.ans ? 'ok' : 'no'}`}>\n"
    '              {ans === c.quiz.ans\n'
    '                ? <><Icon name="check_circle" size={14} />Correct! +{lesson.pts} points!</>\n'
    '                : <><Icon name="cancel" size={14} />Wrong. Answer: {c.quiz.opts[c.quiz.ans]}</>}\n'
    '            </div>\n'
    '          )}\n'
    '        </div>\n'
    '      ) : (\n'
    "        <div className=\"quiz-box\" style={{ background: '#f1f8e9', borderColor: '#c8e6c9' }}>\n"
    "          <div className=\"quiz-q\" style={{ color: '#2e7d32' }}><Icon name=\"check_circle\" size={16} color=\"#2e7d32\" />Mark this lesson as complete to earn {lesson.pts} pts</div>\n"
    '          {done\n'
    '            ? <div className="quiz-result ok"><Icon name="check_circle" size={14} />Already completed! +{lesson.pts} points earned.</div>\n'
    '            : <button className="btn btn-green" style={{ marginTop: 8 }} onClick={async () => { if (!done) await onCompleteLesson(lesson.id, lesson.pts); }}><Icon name="check" size={16} />Mark Complete (+{lesson.pts} pts)</button>\n'
    '          }\n'
    '        </div>\n'
    '      )}\n'
    '      <div className="lesson-footer">\n'
    '        <button className="btn btn-outline" onClick={onBack}><Icon name="arrow_back" size={14} />Back</button>\n'
    '        {idx < mod.lessons.length - 1 && <button className="btn btn-solid" onClick={() => onNext(mod.lessons[idx + 1])}>Next<Icon name="arrow_forward" size={14} /></button>}\n'
    '      </div>\n'
    '    </div>\n'
    '  );\n'
    '}\n'
)

# Replace lines 752-818 (0-indexed: 751-817)
new_lines = lines[:751] + [clean] + lines[818:]
with open(r'c:\Users\aswan\Projects\AgriGrow\AgriGrow.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Done. Total lines:', len(new_lines))
