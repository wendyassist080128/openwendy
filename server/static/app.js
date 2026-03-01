// ============================================
// OpenWendy v2 — Pipeline Editor
// ============================================
const BASE_PATH = '';

const NODE_DEFS = {
  'input': { icon: '📥', label: 'Input', cls: 'input-type', inputs: 0, outputs: 1,
    fields: [
      { key: 'source', label: 'Source', type: 'select', options: ['ChatApp','App','VR-App'] },
      { key: 'type', label: 'Input Type', type: 'select', options: ['text','voice','image','video'] }
    ]
  },
  'output': { icon: '📤', label: 'Output', cls: 'output-type', inputs: 1, outputs: 0,
    fields: [
      { key: 'target', label: 'Target', type: 'select', options: ['ChatApp','App','VR-App'] },
      { key: 'format', label: 'Format', type: 'select', options: ['text','audio 🎙️','image 🖼️','video 📹','file 📁'] }
    ]
  },
  'wendy': { icon: '🌸', label: 'Wendy', cls: 'wendy-type', inputs: 1, outputs: 1,
    fields: [
      { key: 'role', label: 'Role', type: 'text', default: 'wendy' },
      { key: 'prompt', label: 'Prompt', type: 'textarea', default: '' },
      { key: 'model', label: 'Model', type: 'select', options: ['auto','qwen2.5-72b','qwen2.5-omni','claude-sonnet-4-6','claude-opus-4-6','gpt-4o'] }
    ]
  },
  'avatar': { icon: '👤', label: 'Avatar', cls: 'avatar-type', inputs: 1, outputs: 1,
    fields: [{ key: 'name', label: 'Name', type: 'text', default: 'Wendy' }],
    sections: [{ title: '🌸 Photos', fields: [
      { key: 'avatar', label: 'Avatar', type: 'photo', default: '' },
      { key: 'profile_photo', label: 'Profile Photo', type: 'photo', default: '' }
    ]}]
  },
  'filter': { icon: '🔀', label: 'Filter', cls: 'filter-type', inputs: 1, outputs: 1,
    dynamic_outputs: true,
    fields: [{ key: 'model', label: 'Model', type: 'select', options: ['qwen2.5-72b','claude-sonnet-4-6'] }]
  },
  'prompt': { icon: '📝', label: 'Prompt', cls: 'prompt-type', inputs: 1, outputs: 1,
    fields: [{ key: 'text', label: 'Prompt Text', type: 'textarea', default: '' }]
  },
  'heartbeat': { icon: '💓', label: 'Heartbeat', cls: 'heartbeat-type', inputs: 0, outputs: 1,
    fields: [
      { key: 'interval', label: 'Interval', type: 'select', options: ['30s','1m','5m','15m','30m','1h'] },
      { key: 'prompt', label: 'Check Prompt', type: 'textarea', default: 'Check system status.' },
      { key: 'action', label: 'On Trigger', type: 'select', options: ['notify','run-pipeline','log-only'] }
    ]
  },
  'voice': { icon: '🔊', label: 'Voice TTS', cls: 'voice-type', inputs: 1, outputs: 1,
    fields: [
      { key: 'voice_id', label: 'Voice ID', type: 'text', default: 'zGjIP4SZlMnY9m93k97r' },
      { key: 'tts_model', label: 'TTS Model', type: 'text', default: 'eleven_v3' }
    ]
  },
  'image-gen': { icon: '🖼️', label: 'Image Gen', cls: 'image-gen-type', inputs: 1, outputs: 1,
    fields: [
      { key: 'model', label: 'Model', type: 'select', options: ['T2I','nano-banana-pro','gpt-image-1.5'] },
      { key: 'size', label: 'Size', type: 'select', options: ['1024x1024','1024x1792','1792x1024'] },
      { key: 'prompt', label: 'Extra Prompt', type: 'textarea', default: '' }
    ]
  },
  'video-gen': { icon: '🎬', label: 'Video Gen', cls: 'video-gen-type', inputs: 1, outputs: 1,
    fields: [
      { key: 'model', label: 'Model', type: 'select', options: ['wan2.2','wan2.2-turbo'] },
      { key: 'duration', label: 'Duration (s)', type: 'select', options: ['5','10','15','30'] },
      { key: 'prompt', label: 'Extra Prompt', type: 'textarea', default: '' }
    ]
  },
  'live-vid-stream': { icon: '📹', label: 'Live Vid Stream', cls: 'live-vid-type', inputs: 1, outputs: 1,
    fields: [
      { key: 'model', label: 'Model', type: 'select', options: ['wan2.2-live','svd','stable-video'] },
      { key: 'resolution', label: 'Resolution', type: 'select', options: ['720x480','1280x720','1920x1080'] },
      { key: 'fps', label: 'FPS', type: 'select', options: ['24','30','60'] }
    ]
  }
};

// ============================================
// Init Drawflow
// ============================================
const container = document.getElementById('drawflow');
const editor = new Drawflow(container);
editor.reroute = true;
editor.reroute_fix_curvature = true;
editor.force_first_input = false;
editor.start();

const nodeConfigs = {};
let selectedNodeId = null;

// ============================================
// Drag & Drop
// ============================================
function dragStart(ev) { ev.dataTransfer.setData('nodeType', ev.currentTarget.dataset.type); }
function allowDrop(ev) { ev.preventDefault(); }
function drop(ev) {
  ev.preventDefault();
  const type = ev.dataTransfer.getData('nodeType');
  if (!type || !NODE_DEFS[type]) return;
  addNode(type, ev.clientX, ev.clientY);
}

function addNode(type, posX, posY) {
  const def = NODE_DEFS[type];
  const rect = container.getBoundingClientRect();
  const x = (posX - rect.left - editor.canvas_x) / editor.zoom;
  const y = (posY - rect.top - editor.canvas_y) / editor.zoom;
  const config = {};
  (def.fields || []).forEach(f => { config[f.key] = f.default || (f.options ? f.options[0] : ''); });
  if (def.dynamic_outputs && !config.conditions) config.conditions = [''];
  const html = `<div class="title-box">${def.icon} ${def.label}<span class="node-del-btn" title="Delete node">✕</span></div>${getNodeForm(type, config, '__NID__')}`;
  const outputCount = (def.dynamic_outputs && config.conditions) ? config.conditions.length : def.outputs;
  const nodeId = editor.addNode(type, def.inputs, outputCount, x, y, def.cls, {}, html);
  nodeConfigs[nodeId] = { type, label: def.label, config };
  const nodeEl = document.getElementById(`node-${nodeId}`);
  if (nodeEl) {
    const contentEl = nodeEl.querySelector('.drawflow_content_node');
    if (contentEl) contentEl.innerHTML = contentEl.innerHTML.replace(/__NID__/g, String(nodeId));
    nodeEl.querySelectorAll('textarea.nf-input').forEach(autoResizeTextarea);
  }
}

function getNodeForm(type, config, nodeId) {
  const def = NODE_DEFS[type];
  if (!def) return '';
  let html = '<div class="node-form" onmousedown="event.stopPropagation()" ontouchstart="event.stopPropagation()">';
  (def.fields || []).forEach(f => {
    const val = (config && config[f.key] !== undefined) ? config[f.key] : (f.default || (f.options ? f.options[0] : ''));
    html += `<div class="nf-field"><label class="nf-flabel">${f.label}</label>`;
    if (f.type === 'select') {
      html += `<select class="nf-input" data-nid="${nodeId}" data-key="${f.key}" onchange="onFieldChange(this)">`;
      (f.options || []).forEach(o => { html += `<option value="${escHtml(o)}"${val === o ? ' selected' : ''}>${escHtml(o)}</option>`; });
      html += `</select>`;
    } else if (f.type === 'textarea') {
      html += `<textarea class="nf-input" data-nid="${nodeId}" data-key="${f.key}" rows="2" oninput="onFieldChange(this)">${escHtml(String(val))}</textarea>`;
    } else {
      html += `<input type="text" class="nf-input" data-nid="${nodeId}" data-key="${f.key}" value="${escHtml(String(val))}" oninput="onFieldChange(this)">`;
    }
    html += `</div>`;
  });
  if (def.dynamic_outputs) {
    const conditions = (config && config.conditions) ? config.conditions : [''];
    html += `<div class="filter-outputs" id="filter-outputs-${nodeId}">`;
    conditions.forEach((cond, i) => { html += getFilterOutputRow(nodeId, i, cond); });
    html += `</div><button class="btn-add-output" data-nid="${nodeId}" data-action="add-output">＋ Add Output</button>`;
  }
  if (def.sections) {
    def.sections.forEach(section => {
      html += `<div class="nf-section"><div class="nf-section-header">${escHtml(section.title)}</div>`;
      section.fields.forEach(f => {
        const rawVal = (config && config[f.key] !== undefined) ? config[f.key] : (f.default !== undefined ? f.default : '');
        html += `<div class="nf-field"><label class="nf-flabel">${escHtml(f.label)}</label>`;
        if (f.type === 'photo') {
          const src = typeof rawVal === 'string' ? rawVal : '';
          html += `<div class="nf-photo-wrap"><div class="nf-photo-box" id="photo-box-${nodeId}-${escHtml(f.key)}">${src ? `<img class="nf-photo-preview" src="${escHtml(src)}">` : `<span class="nf-photo-placeholder">📷</span>`}</div><button class="nf-photo-btn" data-nid="${nodeId}" data-key="${escHtml(f.key)}" data-action="pick-photo">Choose</button><input type="file" class="nf-photo-file" id="photo-file-${nodeId}-${escHtml(f.key)}" accept="image/*" data-nid="${nodeId}" data-key="${escHtml(f.key)}" onchange="onPhotoChange(this)" style="display:none"></div>`;
        }
        html += `</div>`;
      });
      html += `</div>`;
    });
  }
  html += '</div>';
  return html;
}

function getFilterOutputRow(nodeId, index, value) {
  return `<div class="filter-out-row" id="filter-row-${nodeId}-${index}"><div class="filter-out-header"><span class="filter-out-label">Output ${index+1}</span><button class="btn-remove-output" data-nid="${nodeId}" data-idx="${index}" data-action="remove-output">✕</button></div><textarea class="nf-input filter-cond" data-nid="${nodeId}" data-key="conditions" data-index="${index}" rows="2" placeholder="condition prompt" oninput="onConditionChange(this)">${escHtml(String(value||''))}</textarea></div>`;
}

function onFieldChange(el) {
  const nid = el.dataset.nid, key = el.dataset.key;
  if (!nid || !key || nid === '__NID__') return;
  if (!nodeConfigs[nid]) nodeConfigs[nid] = { config: {} };
  if (!nodeConfigs[nid].config) nodeConfigs[nid].config = {};
  nodeConfigs[nid].config[key] = el.value;
  if (el.tagName === 'TEXTAREA') autoResizeTextarea(el);
}

function onConditionChange(el) {
  const nid = el.dataset.nid, idx = parseInt(el.dataset.index);
  if (!nid || nid === '__NID__' || !nodeConfigs[nid]) return;
  if (!nodeConfigs[nid].config.conditions) nodeConfigs[nid].config.conditions = [];
  nodeConfigs[nid].config.conditions[idx] = el.value;
  autoResizeTextarea(el);
}

function addFilterOutput(nodeId) {
  if (!nodeConfigs[nodeId]) return;
  const cfg = nodeConfigs[nodeId].config;
  if (!cfg.conditions) cfg.conditions = [''];
  cfg.conditions.push('');
  editor.addNodeOutput(nodeId);
  const cont = document.getElementById(`filter-outputs-${nodeId}`);
  if (cont) {
    const tmp = document.createElement('div');
    tmp.innerHTML = getFilterOutputRow(nodeId, cfg.conditions.length - 1, '');
    cont.appendChild(tmp.firstElementChild);
  }
}

function removeFilterOutput(nodeId, index) {
  if (!nodeConfigs[nodeId]) return;
  const cfg = nodeConfigs[nodeId].config;
  if (!cfg.conditions || cfg.conditions.length <= 1) return;
  cfg.conditions.splice(index, 1);
  try { editor.removeNodeOutput(nodeId, `output_${cfg.conditions.length + 1}`); } catch(e) {}
  const cont = document.getElementById(`filter-outputs-${nodeId}`);
  if (cont) cont.innerHTML = cfg.conditions.map((c, i) => getFilterOutputRow(nodeId, i, c)).join('');
}

function autoResizeTextarea(el) { el.style.height = 'auto'; el.style.height = Math.min(el.scrollHeight, 300) + 'px'; }

function onPhotoChange(el) {
  const nid = el.dataset.nid, key = el.dataset.key;
  if (!nid || !key || !el.files || !el.files[0]) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    if (!nodeConfigs[nid]) nodeConfigs[nid] = { config: {} };
    nodeConfigs[nid].config[key] = e.target.result;
    const box = document.getElementById(`photo-box-${nid}-${key}`);
    if (box) box.innerHTML = `<img class="nf-photo-preview" src="${e.target.result}">`;
  };
  reader.readAsDataURL(el.files[0]);
}

// ============================================
// Node events
// ============================================
editor.on('nodeSelected', (nodeId) => { selectedNodeId = nodeId; });
editor.on('nodeRemoved', (nodeId) => { delete nodeConfigs[nodeId]; if (selectedNodeId == nodeId) selectedNodeId = null; });

// Event delegation
container.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-action]');
  if (btn) {
    e.stopPropagation();
    let nid = btn.dataset.nid;
    if (!nid || nid === '__NID__') { const n = btn.closest('.drawflow-node'); if (n) nid = n.id.replace('node-',''); }
    if (btn.dataset.action === 'add-output') addFilterOutput(nid);
    if (btn.dataset.action === 'remove-output') removeFilterOutput(nid, parseInt(btn.dataset.idx));
    if (btn.dataset.action === 'pick-photo') { const fi = document.getElementById(`photo-file-${nid}-${btn.dataset.key}`); if (fi) fi.click(); }
  }
  if (e.target.classList.contains('node-del-btn')) {
    e.stopPropagation();
    const nodeEl = e.target.closest('.drawflow-node');
    if (nodeEl) editor.removeNodeId(nodeEl.id);
  }
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Delete' || e.key === 'Backspace') {
    if (['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)) return;
    if (selectedNodeId) editor.removeNodeId(`node-${selectedNodeId}`);
  }
});

// ============================================
// Pipeline Save / Load
// ============================================
async function savePipeline() {
  const name = document.getElementById('pipeline-name').value.trim();
  if (!name) { showStatus('⚠ Enter a pipeline name'); return; }
  const data = buildPipelineJSON(name);
  const res = await fetch(`/api/pipelines/${encodeURIComponent(name)}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
  });
  if (res.ok) showStatus(`Saved "${name}" ✓`);
  else showStatus('⚠ Save failed');
}

async function showLoadModal() {
  const res = await fetch('/api/pipelines');
  const names = await res.json();
  const list = document.getElementById('pipeline-list');
  if (names.length === 0) {
    list.innerHTML = '<div style="color:#666;padding:20px;text-align:center">No saved pipelines</div>';
  } else {
    list.innerHTML = names.map(n => `
      <div class="pipeline-item" onclick="loadPipeline('${n}')">
        <span>${n}</span>
        <button class="del-btn" onclick="deletePipeline('${n}',event)">🗑</button>
      </div>`).join('');
  }
  document.getElementById('load-modal').classList.remove('hidden');
}
function closeLoadModal() { document.getElementById('load-modal').classList.add('hidden'); }

async function loadPipeline(name) {
  closeLoadModal();
  const res = await fetch(`/api/pipelines/${encodeURIComponent(name)}`);
  if (!res.ok) { showStatus('⚠ Load failed'); return; }
  const data = await res.json();
  document.getElementById('pipeline-name').value = data.name || name;
  loadPipelineData(data);
  showStatus(`✅ Loaded "${name}"`);
}

function loadPipelineData(data) {
  if (!data.nodes || data.nodes.length === 0) { showStatus('⚠ No nodes'); return; }
  editor.clear();
  Object.keys(nodeConfigs).forEach(k => delete nodeConfigs[k]);

  const idMap = {};
  const savedConfigs = data.nodeConfigs || {};
  (data.nodes || []).forEach((n, i) => {
    const def = NODE_DEFS[n.type];
    if (!def) return;
    const savedCfg = savedConfigs[n.id];
    const config = savedCfg ? savedCfg.config : (n.config || {});
    const label = savedCfg ? savedCfg.label : (n.label || def.label);
    const posX = n.pos_x !== undefined ? n.pos_x : 100 + (i % 5) * 270;
    const posY = n.pos_y !== undefined ? n.pos_y : 150 + Math.floor(i / 5) * 200;
    const outputCount = (def.dynamic_outputs && config.conditions) ? config.conditions.length : def.outputs;
    const html = `<div class="title-box">${def.icon} ${escHtml(label)}<span class="node-del-btn" title="Delete">✕</span></div>${getNodeForm(n.type, config, '__NID__')}`;
    const nodeId = editor.addNode(n.type, def.inputs, outputCount, posX, posY, def.cls, {}, html);
    nodeConfigs[nodeId] = { type: n.type, label, config };
    idMap[n.id] = nodeId;
    const nodeEl = document.getElementById(`node-${nodeId}`);
    if (nodeEl) {
      const contentEl = nodeEl.querySelector('.drawflow_content_node');
      if (contentEl) contentEl.innerHTML = contentEl.innerHTML.replace(/__NID__/g, String(nodeId));
      nodeEl.querySelectorAll('textarea.nf-input').forEach(autoResizeTextarea);
    }
  });
  (data.edges || []).forEach(e => {
    const from = idMap[e.from], to = idMap[e.to];
    if (from && to) { try { editor.addConnection(from, to, e.from_port || 'output_1', e.to_port || 'input_1'); } catch(err) {} }
  });
}

async function deletePipeline(name, ev) {
  ev.stopPropagation();
  await fetch(`/api/pipelines/${encodeURIComponent(name)}`, { method: 'DELETE' });
  showLoadModal();
}

function buildPipelineJSON(name) {
  const dfExport = editor.export();
  const dfData = dfExport.drawflow.Home.data;
  const nodes = [], edges = [];
  Object.keys(dfData).forEach(id => {
    const node = dfData[id];
    const nc = nodeConfigs[id] || { type: node.name, label: NODE_DEFS[node.name]?.label || node.name, config: {} };
    nodes.push({ id: String(id), type: nc.type, label: nc.label, config: nc.config, pos_x: node.pos_x, pos_y: node.pos_y });
    Object.entries(node.outputs).forEach(([outPort, out]) => {
      out.connections.forEach(conn => {
        edges.push({ from: String(id), to: String(conn.node), from_port: outPort, to_port: conn.output || 'input_1' });
      });
    });
  });
  return { name, nodes, edges, nodeConfigs: { ...nodeConfigs } };
}

// ============================================
// Sidebar
// ============================================
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('collapsed');
}
if (window.innerWidth <= 768) document.getElementById('sidebar').classList.add('collapsed');

// Double-tap to add (mobile)
document.querySelectorAll('.node-item').forEach(item => {
  let lastTap = 0;
  item.addEventListener('touchend', (e) => {
    const now = Date.now();
    if (now - lastTap < 350) {
      e.preventDefault();
      const rect = container.getBoundingClientRect();
      addNode(item.dataset.type, rect.left + rect.width/2, rect.top + rect.height/2);
      if (window.innerWidth <= 768) document.getElementById('sidebar').classList.add('collapsed');
    }
    lastTap = now;
  });
});

// ============================================
// Utilities
// ============================================
function showStatus(msg) {
  const el = document.getElementById('status-msg');
  el.textContent = msg;
  setTimeout(() => { el.textContent = ''; }, 3000);
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
