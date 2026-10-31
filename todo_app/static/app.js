const $ = id => document.getElementById(id);
let filter = "all";
const api = (url, method="GET", body) => fetch(url, {method, headers:{"Content-Type":"application/json"}, body: body && JSON.stringify(body)})
  .then(async r => ({ok:r.ok, data:await r.json()}));

async function load() {
  const {data} = await api(`/api/tasks?filter=${filter}&q=${encodeURIComponent($("search").value)}`);
  const list = $("list"); list.innerHTML = "";
  $("empty").hidden = data.tasks.length > 0;
  const today = new Date().toISOString().slice(0, 10);
  data.tasks.forEach(t => {
    const li = document.createElement("li"); li.className = "item" + (t.done ? " done" : "");
    const cb = document.createElement("input"); cb.type = "checkbox"; cb.checked = !!t.done;
    cb.setAttribute("aria-label", "Mark done");
    cb.onchange = async () => { await api(`/api/tasks/${t.id}`, "PATCH", {done: cb.checked}); load(); };
    const body = document.createElement("div"); body.className = "body";
    const name = document.createElement("div"); name.className = "name"; name.textContent = t.title; name.title = "Click to edit";
    name.onclick = () => editTask(t, name);
    const meta = document.createElement("div"); meta.className = "meta";
    const tag = document.createElement("span"); tag.className = "tag " + t.priority; tag.textContent = t.priority;
    meta.append(tag);
    if (t.due_date) {
      const d = document.createElement("span");
      d.textContent = "Due " + t.due_date;
      if (!t.done && t.due_date < today) { d.className = "overdue"; d.textContent += " (overdue)"; }
      meta.append(d);
    }
    body.append(name, meta);
    const del = document.createElement("button"); del.className = "del"; del.textContent = "×"; del.setAttribute("aria-label", "Delete task");
    del.onclick = async () => { await api(`/api/tasks/${t.id}`, "DELETE"); load(); };
    li.append(cb, body, del); list.append(li);
  });
  const pct = data.total ? Math.round(data.done / data.total * 100) : 0;
  $("pct").textContent = pct + "%"; $("bar").style.width = pct + "%";
  $("summary").textContent = data.total ? `${data.done} of ${data.total} completed` : "No tasks yet";
}

function editTask(t, el) {
  const input = document.createElement("input"); input.className = "edit"; input.value = t.title; input.maxLength = 120;
  el.replaceWith(input); input.focus();
  const save = async () => {
    const v = input.value.trim();
    if (v && v !== t.title) await api(`/api/tasks/${t.id}`, "PATCH", {title: v});
    load();
  };
  input.onblur = save;
  input.onkeydown = e => { if (e.key === "Enter") input.blur(); if (e.key === "Escape") { input.onblur = null; load(); } };
}

$("addForm").addEventListener("submit", async e => {
  e.preventDefault();
  const {ok, data} = await api("/api/tasks", "POST", {title: $("title").value, priority: $("priority").value, due_date: $("due").value});
  $("err").textContent = ok ? "" : data.error;
  if (ok) { $("title").value = ""; $("due").value = ""; load(); }
  $("title").focus();
});
$("tabs").addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  filter = b.dataset.f;
  document.querySelectorAll("#tabs button").forEach(x => x.classList.toggle("on", x === b));
  load();
});
$("search").addEventListener("input", load);
$("clear").addEventListener("click", async () => { await api("/api/tasks/completed", "DELETE"); load(); });
load();
