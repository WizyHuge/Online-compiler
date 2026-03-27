let currentFileId = null;
let files = [];

async function loadFiles() {
  const res = await fetch('/api/files');
  if (!res.ok) return;
  files = await res.json();
  renderFileList();
}

function renderFileList() {
  const list = document.getElementById('file-list');
  list.innerHTML = '';

  if (files.length === 0) {
    list.innerHTML = '<li style="color:var(--border);font-size:12px;padding:8px 10px;">Нет файлов</li>';
    return;
  }

  files.forEach(f => {
    const li = document.createElement('li');
    li.textContent = f.name;
    li.dataset.id = f.id;
    if (f.id === currentFileId) li.classList.add('active');
    li.addEventListener('click', () => openFile(f.id));
    list.appendChild(li);
  });
}

async function openFile(fileId) {
  const res = await fetch(`/api/files/${fileId}`);
  if (!res.ok) return;
  const file = await res.json();

  currentFileId = file.id;
  editor.setValue(file.code);
  editor.clearHistory();
  document.getElementById('current-file-name').textContent = file.name;
  renderFileList();
}

document.getElementById('new-file-btn').addEventListener('click', () => {
  document.getElementById('new-file-name').value = '';
  showModal('new-file-modal');
});

document.getElementById('new-file-cancel').addEventListener('click', () => {
  hideModal('new-file-modal');
});

document.getElementById('new-file-confirm').addEventListener('click', async () => {
  const name = document.getElementById('new-file-name').value.trim();
  if (!name) return;

  const res = await fetch('/api/files', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, code: '' }),
  });

  if (res.ok) {
    const file = await res.json();
    hideModal('new-file-modal');
    await loadFiles();
    openFile(file.id);
  }
});

document.getElementById('new-file-name').addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('new-file-confirm').click();
});

async function saveCurrentFile() {
  if (!currentFileId) return;

  const code = editor.getValue();
  const res = await fetch(`/api/files/${currentFileId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  });

  if (res.ok) showSaveIndicator();
}

document.getElementById('save-btn').addEventListener('click', saveCurrentFile);

document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    saveCurrentFile();
  }
});

function showSaveIndicator() {
  const el = document.getElementById('save-indicator');
  el.textContent = 'Сохранено';
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2000);
}

document.getElementById('delete-file-btn').addEventListener('click', async () => {
  if (!currentFileId) return;
  if (!confirm('Удалить файл?')) return;

  const res = await fetch(`/api/files/${currentFileId}`, { method: 'DELETE' });

  if (res.ok) {
    currentFileId = null;
    editor.setValue('');
    document.getElementById('current-file-name').textContent = 'Выбери файл';
    await loadFiles();
  }
});

document.getElementById('publish-btn').addEventListener('click', () => {
  const container = document.getElementById('file-checkboxes');
  container.innerHTML = '';

  if (files.length === 0) {
    container.innerHTML = '<span style="color:var(--muted);font-size:13px;">Нет файлов</span>';
  } else {
    files.forEach(f => {
      const label = document.createElement('label');
      label.innerHTML = `
        <input type="checkbox" value="${f.id}" ${f.id === currentFileId ? 'checked' : ''}/>
        ${f.name}
      `;
      container.appendChild(label);
    });
  }

  showModal('publish-modal');
});

document.getElementById('publish-cancel').addEventListener('click', () => {
  hideModal('publish-modal');
});

document.getElementById('publish-confirm').addEventListener('click', async () => {
  const title = document.getElementById('post-title').value.trim();
  const description = document.getElementById('post-description').value.trim();
  const checked = [...document.querySelectorAll('#file-checkboxes input:checked')];
  const file_ids = checked.map(cb => parseInt(cb.value));

  if (!title) {
    alert('Укажи заголовок');
    return;
  }
  if (file_ids.length === 0) {
    alert('Выбери хотя бы один файл');
    return;
  }

  const res = await fetch('/posts/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description, file_ids }),
  });

  if (res.ok) {
    const data = await res.json();
    hideModal('publish-modal');
    window.location.href = '/';
  } else {
    const err = await res.json();
    alert(err.error || 'Ошибка публикации');
  }
});

function showModal(id) {
  document.getElementById(id).classList.add('show');
}

function hideModal(id) {
  document.getElementById(id).classList.remove('show');
}

document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.classList.remove('show');
  });
});

loadFiles();
