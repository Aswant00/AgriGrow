with open(r'c:\Users\aswan\Projects\AgriGrow\AgriGrow.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ── Patch 1: replace AdminPanel function body (state + functions) ─────────────
START_MARKER = 'function AdminPanel({ adminUser }) {'
END_MARKER = "  const ROLE_COLOR  = { admin: '#7b1fa2', expert: '#1565c0', farmer: '#2e7d32' };"

start = content.find(START_MARKER)
end   = content.find(END_MARKER, start)
assert start != -1, "START_MARKER not found"
assert end   != -1, "END_MARKER not found"

NEW_HEAD = """function AdminPanel({ adminUser }) {
  const [tab, setTab]           = useState('analytics');
  const [stats, setStats]       = useState(null);
  const [users, setUsers]       = useState([]);
  const [selUser, setSelUser]   = useState(null);
  const [customMods, setCustomMods] = useState([]);
  const [loading, setLoading]   = useState(false);
  const [showAddMod, setShowAddMod] = useState(false);
  const BLANK_FORM = { title: '', category: 'Soil Management', difficulty: 'Beginner', icon: 'eco', iconColor: '#2e7d32', description: '', duration: '30 min', expertVerified: false };
  const [modForm, setModForm]   = useState(BLANK_FORM);
  const [modSaving, setModSaving] = useState(false);
  const [modErr, setModErr]     = useState('');
  const [toast, setToast]       = useState('');
  const [usersLoaded, setUsersLoaded] = useState(false);
  const [modsLoaded, setModsLoaded]   = useState(false);
  const [showEditMod, setShowEditMod]     = useState(false);
  const [editingModId, setEditingModId]   = useState(null);
  const [editModErr, setEditModErr]       = useState('');
  const [editModSaving, setEditModSaving] = useState(false);
  const [managingMod, setManagingMod]     = useState(null);
  const [manageLessons, setManageLessons] = useState([]);
  const [lessonForm, setLessonForm]       = useState({ title: '', subtitle: '', pts: 20, expertVerified: false });
  const [editingLesson, setEditingLesson] = useState(null);
  const [lessonSaving, setLessonSaving]   = useState(false);
  const [lessonErr, setLessonErr]         = useState('');

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000); };

  useEffect(() => {
    apiFetch('/admin/stats').then(d => setStats(d)).catch(() => {});
  }, []);

  useEffect(() => {
    if (tab === 'users' && !usersLoaded) {
      setLoading(true);
      apiFetch('/admin/users').then(d => { setUsers(d.users); setUsersLoaded(true); }).catch(() => {}).finally(() => setLoading(false));
    }
    if (tab === 'content' && !modsLoaded) {
      apiFetch('/admin/modules').then(d => { setCustomMods(d.modules); setModsLoaded(true); }).catch(() => {});
    }
  }, [tab]);

  const openUser = async (userId) => {
    try { const d = await apiFetch(`/admin/users/${userId}`); setSelUser(d); }
    catch (e) { showToast('Failed to load user info'); }
  };

  const submitModule = async () => {
    setModErr('');
    if (!modForm.title.trim() || !modForm.description.trim()) { setModErr('Title and description are required.'); return; }
    setModSaving(true);
    try {
      const d = await apiFetch('/admin/modules', { method: 'POST', body: modForm });
      setCustomMods(m => [d.module, ...m]);
      setShowAddMod(false); setModForm(BLANK_FORM);
      showToast('Module created!');
    } catch (e) { setModErr(e.message); }
    finally { setModSaving(false); }
  };

  const openEditMod = (m) => {
    setModForm({ title: m.title, category: m.category, difficulty: m.difficulty, icon: m.icon || 'eco', iconColor: m.icon_color || '#2e7d32', description: m.description, duration: m.duration, expertVerified: !!m.expert_verified });
    setEditingModId(m.id); setEditModErr(''); setShowEditMod(true);
  };

  const saveEditMod = async () => {
    setEditModErr('');
    if (!modForm.title.trim() || !modForm.description.trim()) { setEditModErr('Title and description are required.'); return; }
    setEditModSaving(true);
    try {
      const d = await apiFetch(`/admin/modules/${editingModId}`, { method: 'PUT', body: modForm });
      setCustomMods(m => m.map(x => x.id === editingModId ? { ...x, ...d.module } : x));
      setShowEditMod(false); showToast('Module updated!');
    } catch (e) { setEditModErr(e.message); }
    finally { setEditModSaving(false); }
  };

  const deleteModule = async (id) => {
    if (!window.confirm('Delete this module?')) return;
    try {
      await apiFetch(`/admin/modules/${id}`, { method: 'DELETE' });
      setCustomMods(m => m.filter(x => x.id !== id));
      showToast('Module deleted.');
    } catch (e) { showToast('Failed to delete.'); }
  };

  const openManageLessons = (m) => {
    setManagingMod(m); setManageLessons(m.lessons || []);
    setLessonForm({ title: '', subtitle: '', pts: 20, expertVerified: false });
    setEditingLesson(null); setLessonErr('');
  };

  const startEditLesson = (l) => {
    setEditingLesson(l);
    setLessonForm({ title: l.title, subtitle: l.subtitle || '', pts: l.pts, expertVerified: !!l.expertVerified });
  };

  const saveLesson = async () => {
    setLessonErr('');
    if (!lessonForm.title.trim()) { setLessonErr('Lesson title is required.'); return; }
    setLessonSaving(true);
    try {
      if (editingLesson) {
        const d = await apiFetch(`/admin/modules/${managingMod.id}/lessons/${editingLesson.id}`, { method: 'PUT', body: lessonForm });
        setManageLessons(ls => ls.map(l => l.id === editingLesson.id ? { ...l, ...d.lesson } : l));
        setEditingLesson(null);
      } else {
        const d = await apiFetch(`/admin/modules/${managingMod.id}/lessons`, { method: 'POST', body: lessonForm });
        setManageLessons(ls => [...ls, d.lesson]);
      }
      setLessonForm({ title: '', subtitle: '', pts: 20, expertVerified: false });
      showToast(editingLesson ? 'Lesson updated!' : 'Lesson added!');
    } catch (e) { setLessonErr(e.message); }
    finally { setLessonSaving(false); }
  };

  const removeLesson = async (lessonId) => {
    if (!window.confirm('Delete this lesson?')) return;
    try {
      await apiFetch(`/admin/modules/${managingMod.id}/lessons/${lessonId}`, { method: 'DELETE' });
      setManageLessons(ls => ls.filter(l => l.id !== lessonId));
      showToast('Lesson deleted.');
    } catch (e) { showToast('Failed to delete lesson.'); }
  };

  const ROLE_COLOR  = { admin: '#7b1fa2', expert: '#1565c0', farmer: '#2e7d32' };"""

content = content[:start] + NEW_HEAD + content[end + len(END_MARKER):]
print("Patch 1 OK: state+functions replaced")

# ── Patch 2: custom modules list - add Edit + Lessons buttons ─────────────────
OLD2_START = "              <button className=\"fp-action\" style={{ color: '#e53935' }} onClick={() => deleteModule(m.id)} title=\"Delete module\">\n                <Icon name=\"delete\" size={15} />\n              </button>\n            </div>\n          ))}"
NEW2 = """              <div style={{ display: 'flex', gap: 4 }}>
                <button className="btn btn-outline" style={{ padding: '4px 8px', fontSize: 12 }} onClick={() => openManageLessons(m)}><Icon name="list" size={13} />Lessons</button>
                <button className="btn btn-outline" style={{ padding: '4px 8px', fontSize: 12 }} onClick={() => openEditMod(m)}><Icon name="edit" size={13} />Edit</button>
                <button className="fp-action" style={{ color: '#e53935' }} onClick={() => deleteModule(m.id)}><Icon name="delete" size={15} /></button>
              </div>
            </div>
          ))}"""

if OLD2_START in content:
    content = content.replace(OLD2_START, NEW2)
    print("Patch 2 OK: edit/lessons buttons added")
else:
    print("Patch 2 WARN: custom module delete button not found, checking alt...")
    alt = "\"Delete module\">"
    idx = content.find(alt, content.find('customMods.map'))
    print(f"Alt search result at index: {idx}")

# ── Patch 3: insert Edit Modal + Manage Lessons modal before toast line ────────
TOAST_LINE = '      {toast && <div className="toast"><Icon name="check_circle" size={15} />{toast}</div>}'
MODALS = """      {/* Edit Module Modal */}
      {showEditMod && (
        <div className="modal-overlay" onClick={() => setShowEditMod(false)}>
          <div className="modal-box" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title"><Icon name="edit" size={20} color="#1565c0" />Edit Module</div>
              <button className="modal-close" onClick={() => setShowEditMod(false)}><Icon name="close" size={16} /></button>
            </div>
            {editModErr && <div className="alert alert-error"><Icon name="error" size={14} />{editModErr}</div>}
            <div className="fg"><label>Module Title *</label><input value={modForm.title} onChange={e => setModForm(f => ({ ...f, title: e.target.value }))} /></div>
            <div className="fg"><label>Category *</label>
              <select value={modForm.category} onChange={e => setModForm(f => ({ ...f, category: e.target.value }))}>
                {['Soil Management','Water Management','Pest Management','Crop Management','Agroforestry','Other'].map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div className="fg"><label>Difficulty</label>
                <select value={modForm.difficulty} onChange={e => setModForm(f => ({ ...f, difficulty: e.target.value }))}>
                  {['Beginner','Intermediate','Advanced'].map(d => <option key={d}>{d}</option>)}
                </select>
              </div>
              <div className="fg"><label>Duration</label><input placeholder="30 min" value={modForm.duration} onChange={e => setModForm(f => ({ ...f, duration: e.target.value }))} /></div>
            </div>
            <div className="fg"><label>Description *</label><textarea rows={3} value={modForm.description} onChange={e => setModForm(f => ({ ...f, description: e.target.value }))} /></div>
            <div className="fg"><label>Icon</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {['eco','water_drop','bug_report','refresh','grain','park','local_florist','agriculture','science','wb_sunny'].map(ic => <button key={ic} onClick={() => setModForm(f => ({ ...f, icon: ic }))} style={{ width: 36, height: 36, borderRadius: 8, border: `2px solid ${modForm.icon===ic?'#1565c0':'#ddd'}`, background: modForm.icon===ic?'#e3f2fd':'#f9f9f9', cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center' }}><Icon name={ic} size={18} color={modForm.icon===ic?'#1565c0':'#aaa'} /></button>)}
              </div>
            </div>
            <div className="fg"><label>Icon Colour</label>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {['#2e7d32','#1565c0','#e65100','#558b2f','#6a1b9a','#4e342e','#f57c00','#00838f'].map(c => <button key={c} onClick={() => setModForm(f => ({ ...f, iconColor: c }))} style={{ width:28, height:28, borderRadius:'50%', border:`3px solid ${modForm.iconColor===c?'#222':'transparent'}`, background:c, cursor:'pointer' }} />)}
              </div>
            </div>
            <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:14 }}>
              <input type="checkbox" id="evEditCheck" checked={modForm.expertVerified} onChange={e => setModForm(f => ({ ...f, expertVerified: e.target.checked }))} />
              <label htmlFor="evEditCheck" style={{ fontSize:13, cursor:'pointer' }}>Mark as Expert Verified</label>
            </div>
            <button className="btn btn-green" onClick={saveEditMod} disabled={editModSaving}>
              {editModSaving ? 'Saving...' : <><Icon name="save" size={16} />Save Changes</>}
            </button>
          </div>
        </div>
      )}

      {/* Manage Lessons Panel */}
      {managingMod && (
        <div className="modal-overlay" onClick={() => setManagingMod(null)}>
          <div className="modal-box" onClick={e => e.stopPropagation()} style={{ maxHeight: '92vh' }}>
            <div className="modal-header">
              <div className="modal-title"><Icon name="list" size={20} color="#1565c0" />Lessons — {managingMod.title}</div>
              <button className="modal-close" onClick={() => setManagingMod(null)}><Icon name="close" size={16} /></button>
            </div>
            {manageLessons.length === 0
              ? <p style={{ fontSize:13, color:'#888', textAlign:'center', padding:'12px 0' }}>No lessons yet.</p>
              : manageLessons.map((l, i) => (
                <div key={l.id} style={{ display:'flex', alignItems:'center', gap:8, padding:'8px 0', borderBottom:'1px solid #eee' }}>
                  <div style={{ width:28, height:28, borderRadius:7, background:'#e3f2fd', display:'flex', alignItems:'center', justifyContent:'center', fontWeight:700, fontSize:12, color:'#1565c0', flexShrink:0 }}>{i+1}</div>
                  <div style={{ flex:1 }}>
                    <div style={{ fontSize:13, fontWeight:600 }}>{l.title}</div>
                    <div style={{ fontSize:11, color:'#888' }}>{l.subtitle||'—'} · {l.pts} pts {l.expertVerified?'· ✓':''}</div>
                  </div>
                  <button className="btn btn-outline" style={{ padding:'4px 8px', fontSize:11 }} onClick={() => startEditLesson(l)}><Icon name="edit" size={13} /></button>
                  <button className="fp-action" style={{ color:'#e53935' }} onClick={() => removeLesson(l.id)}><Icon name="delete" size={14} /></button>
                </div>
              ))
            }
            <div style={{ marginTop:14, background:'#f9f9f9', border:'1px solid #e0e0e0', borderRadius:10, padding:12 }}>
              <div style={{ fontSize:12, fontWeight:700, color:'#555', marginBottom:10 }}>{editingLesson ? 'Edit Lesson' : 'Add New Lesson'}</div>
              {lessonErr && <div className="alert alert-error" style={{ marginBottom:8 }}><Icon name="error" size={13} />{lessonErr}</div>}
              <div className="fg"><label>Lesson Title *</label><input placeholder="e.g. Understanding Soil Biology" value={lessonForm.title} onChange={e => setLessonForm(f => ({ ...f, title: e.target.value }))} /></div>
              <div className="fg"><label>Subtitle / Summary</label><input placeholder="Short description" value={lessonForm.subtitle} onChange={e => setLessonForm(f => ({ ...f, subtitle: e.target.value }))} /></div>
              <div style={{ display:'flex', gap:10, alignItems:'center', marginBottom:10 }}>
                <div className="fg" style={{ flex:1, marginBottom:0 }}><label>Points</label><input type="number" min={5} max={200} value={lessonForm.pts} onChange={e => setLessonForm(f => ({ ...f, pts: parseInt(e.target.value)||20 }))} /></div>
                <div style={{ display:'flex', alignItems:'center', gap:6, paddingTop:18 }}>
                  <input type="checkbox" id="lvCheck" checked={lessonForm.expertVerified} onChange={e => setLessonForm(f => ({ ...f, expertVerified: e.target.checked }))} />
                  <label htmlFor="lvCheck" style={{ fontSize:12 }}>Expert Verified</label>
                </div>
              </div>
              <div style={{ display:'flex', gap:8 }}>
                <button className="btn btn-green" style={{ flex:1 }} onClick={saveLesson} disabled={lessonSaving}>
                  {lessonSaving ? 'Saving...' : <><Icon name="save" size={15} />{editingLesson ? 'Update Lesson' : 'Add Lesson'}</>}
                </button>
                {editingLesson && <button className="btn btn-outline" onClick={() => { setEditingLesson(null); setLessonForm({ title:'', subtitle:'', pts:20, expertVerified:false }); }}>Cancel</button>}
              </div>
            </div>
          </div>
        </div>
      )}

"""

idx3 = content.find(TOAST_LINE, content.find('AdminPanel'))
if idx3 != -1:
    content = content[:idx3] + MODALS + content[idx3:]
    print("Patch 3 OK: modals inserted before toast")
else:
    print("Patch 3 WARN: toast line not found in AdminPanel")

with open(r'c:\Users\aswan\Projects\AgriGrow\AgriGrow.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done! All patches written.")
