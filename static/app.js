// Dashboard für die Lern-Tracker-API. Kein Framework, kein Build-Schritt:
// alles läuft über dieselben Endpunkte, die auch in /docs stehen.

const API = "/api/v1";

const state = {
  days: 30,
  chartSubject: "",
  editingId: null,
  filter: { subject: "", start: "", end: "" },
};

const $ = (id) => document.getElementById(id);

// ---------- Hilfsfunktionen ----------

function todayIso() {
  // lokales Datum, nicht UTC, sonst springt es abends auf den nächsten Tag
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

function formatMinutes(total) {
  const h = Math.floor(total / 60);
  const m = total % 60;
  if (!h) return `${m} min`;
  return m ? `${h} h ${m} min` : `${h} h`;
}

function formatDate(iso, opts = { day: "2-digit", month: "2-digit", year: "numeric" }) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString("de-DE", opts);
}

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  Object.assign(node, props);
  for (const child of [].concat(children)) node.append(child);
  return node;
}

let toastTimer;
function toast(message) {
  const box = $("toast");
  box.textContent = message;
  box.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (box.hidden = true), 2500);
}

// FastAPI liefert bei 422 eine Liste von Fehlern, sonst {detail: "..."}
function errorText(body, status) {
  if (Array.isArray(body?.detail)) {
    return body.detail
      .map((e) => `${e.loc?.at(-1) ?? "Feld"}: ${e.msg.replace(/^Value error, /, "")}`)
      .join("\n");
  }
  return body?.detail ?? `Fehler ${status}`;
}

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new Error(errorText(body, res.status));
  return body;
}

// ---------- Kennzahlen und Fächer ----------

async function loadOverview() {
  const data = await api("/stats/overview");

  $("kpi-total").textContent = formatMinutes(data.total_minutes);
  $("kpi-week").textContent = formatMinutes(data.minutes_last_7_days);
  $("kpi-count").textContent = data.total_entries;
  $("kpi-streak").textContent = `${data.streak_days} ${data.streak_days === 1 ? "Tag" : "Tage"}`;

  const list = $("subjects");
  list.replaceChildren();
  if (!data.subjects.length) {
    list.append(el("li", { className: "empty", textContent: "Noch keine Fächer" }));
  }
  const max = Math.max(1, ...data.subjects.map((s) => s.total_minutes));
  for (const s of data.subjects) {
    const share = data.total_minutes ? Math.round((s.total_minutes / data.total_minutes) * 100) : 0;
    const fill = el("div", { className: "fill" });
    fill.style.width = `${(s.total_minutes / max) * 100}%`;
    list.append(
      el("li", {}, [
        el("div", { className: "subject-line" }, [
          el("span", { className: "subject-name", textContent: s.subject }),
          el("span", {
            className: "subject-meta",
            textContent: `${formatMinutes(s.total_minutes)} · ${share} %`,
          }),
        ]),
        el("div", { className: "track" }, fill),
      ]),
    );
  }
}

async function loadSubjects() {
  const subjects = await api("/entries/subjects");
  $("subject-list").replaceChildren(...subjects.map((s) => el("option", { value: s })));

  for (const id of ["chart-subject", "filter-subject"]) {
    const select = $(id);
    const current = select.value;
    select.replaceChildren(
      el("option", { value: "", textContent: "Alle Fächer" }),
      ...subjects.map((s) => el("option", { value: s, textContent: s })),
    );
    select.value = subjects.includes(current) ? current : "";
  }
}

// ---------- Diagramm (SVG von Hand, keine Chart-Bibliothek) ----------

async function loadChart() {
  const params = new URLSearchParams({ days: state.days });
  if (state.chartSubject) params.set("subject", state.chartSubject);
  const data = await api(`/stats/daily?${params}`);
  drawChart(data);
}

// y-Achse in ganzen Stunden bzw. halben Stunden, höchstens 5 Linien
function yScale(value) {
  const step = [30, 60, 120, 180, 240, 360].find((s) => value / s <= 5) ?? 480;
  const ticks = Math.max(1, Math.ceil(value / step));
  return { max: ticks * step, ticks };
}

function drawChart(data) {
  const box = $("chart");
  const width = box.clientWidth || 600;
  const height = box.clientHeight || 220;
  const pad = { top: 8, right: 4, bottom: 22, left: 44 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;
  const { max, ticks } = yScale(Math.max(1, ...data.map((d) => d.minutes)));
  const slot = innerW / data.length;
  const barW = Math.max(2, slot * 0.7);

  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

  const add = (tag, attrs, text) => {
    const node = document.createElementNS(ns, tag);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    if (text !== undefined) node.textContent = text;
    svg.append(node);
    return node;
  };

  for (let i = 0; i <= ticks; i++) {
    const value = (max / ticks) * i;
    const y = pad.top + innerH - (value / max) * innerH;
    add("line", { x1: pad.left, x2: width - pad.right, y1: y, y2: y, class: "grid-line" });
    const label = value % 60 === 0 ? `${value / 60} h` : `${(value / 60).toLocaleString("de-DE")} h`;
    add("text", { x: pad.left - 6, y: y + 4, "text-anchor": "end" }, label);
  }

  // x-Beschriftung: höchstens ~8 Labels, damit nichts überlappt
  const labelEvery = Math.ceil(data.length / 8);
  const tooltip = $("chart-tooltip");

  data.forEach((d, i) => {
    const h = d.minutes ? Math.max(2, (d.minutes / max) * innerH) : 2;
    const x = pad.left + i * slot + (slot - barW) / 2;
    const y = pad.top + innerH - h;
    const bar = add("rect", {
      x, y, width: barW, height: h, rx: Math.min(3, barW / 2),
      class: d.minutes ? "bar" : "bar zero",
    });

    bar.addEventListener("mouseenter", () => {
      tooltip.textContent = `${formatDate(d.date, { weekday: "short", day: "2-digit", month: "2-digit" })}: ${formatMinutes(d.minutes)}`;
      tooltip.style.left = `${box.offsetLeft + x + barW / 2}px`;
      tooltip.style.top = `${box.offsetTop + y}px`;
      tooltip.hidden = false;
    });
    bar.addEventListener("mouseleave", () => (tooltip.hidden = true));

    if (i % labelEvery === 0) {
      add(
        "text",
        { x: x + barW / 2, y: height - 6, "text-anchor": "middle" },
        formatDate(d.date, { day: "2-digit", month: "2-digit" }),
      );
    }
  });

  box.replaceChildren(svg);
}

// ---------- Tabelle ----------

async function loadEntries() {
  const { subject, start, end } = state.filter;
  const errorBox = $("filter-error");
  errorBox.hidden = true;

  let entries;
  try {
    if (subject || start || end) {
      const params = new URLSearchParams();
      if (subject) params.set("subject", subject);
      if (start) params.set("start_date", start);
      if (end) params.set("end_date", end);
      entries = await api(`/entries/filter?${params}`);
    } else {
      entries = await api("/entries/?limit=200");
    }
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
    return;
  }

  const body = $("entries");
  body.replaceChildren(...entries.map(entryRow));
  $("empty").hidden = entries.length > 0;
}

function entryRow(entry) {
  const edit = el("button", { type: "button", textContent: "Bearbeiten" });
  edit.addEventListener("click", () => startEdit(entry));

  // Löschen in zwei Klicks statt confirm()-Dialog
  const del = el("button", { type: "button", className: "danger", textContent: "Löschen" });
  del.addEventListener("click", async () => {
    if (!del.classList.contains("confirm")) {
      del.classList.add("confirm");
      del.textContent = "Sicher?";
      setTimeout(() => {
        del.classList.remove("confirm");
        del.textContent = "Löschen";
      }, 3000);
      return;
    }
    try {
      await api(`/entries/${entry.id}`, { method: "DELETE" });
      if (state.editingId === entry.id) resetForm();
      toast("Eintrag gelöscht");
      await refresh();
    } catch (error) {
      toast(error.message);
    }
  });

  const row = el("tr", {}, [
    el("td", { className: "date", textContent: formatDate(entry.date) }),
    el("td", { className: "subject", textContent: entry.subject }),
    el("td", { className: "num", textContent: formatMinutes(entry.duration_in_minutes) }),
    el("td", { className: "desc", textContent: entry.description ?? "" }),
    el("td", { className: "actions" }, [edit, " ", del]),
  ]);
  if (entry.id === state.editingId) row.classList.add("editing");
  return row;
}

// ---------- Formular: Anlegen und Bearbeiten ----------

function startEdit(entry) {
  state.editingId = entry.id;
  $("form-title").textContent = "Eintrag bearbeiten";
  $("submit").textContent = "Änderungen speichern";
  $("cancel-edit").hidden = false;
  $("f-subject").value = entry.subject;
  $("f-minutes").value = entry.duration_in_minutes;
  $("f-date").value = entry.date;
  $("f-description").value = entry.description ?? "";
  $("form-error").hidden = true;
  document.querySelectorAll("#entries tr").forEach((tr) => tr.classList.remove("editing"));
  loadEntries();
  $("f-subject").focus();
}

function resetForm() {
  state.editingId = null;
  $("entry-form").reset();
  $("f-date").value = todayIso();
  $("form-title").textContent = "Neue Lerneinheit";
  $("submit").textContent = "Speichern";
  $("cancel-edit").hidden = true;
  $("form-error").hidden = true;
}

async function submitForm(event) {
  event.preventDefault();
  const description = $("f-description").value.trim();
  const payload = {
    subject: $("f-subject").value,
    duration_in_minutes: Number($("f-minutes").value),
    date: $("f-date").value,
    // Beim Bearbeiten leere Beschreibung explizit entfernen, beim Anlegen weglassen
    description: description || null,
  };

  const submit = $("submit");
  submit.disabled = true;
  try {
    if (state.editingId) {
      await api(`/entries/${state.editingId}`, { method: "PATCH", body: JSON.stringify(payload) });
      toast("Eintrag aktualisiert");
    } else {
      await api("/entries/", { method: "POST", body: JSON.stringify(payload) });
      toast("Lerneinheit gespeichert");
    }
    resetForm();
    await refresh();
  } catch (error) {
    $("form-error").textContent = error.message;
    $("form-error").hidden = false;
  } finally {
    submit.disabled = false;
  }
}

// ---------- Verdrahtung ----------

async function refresh() {
  await Promise.all([loadOverview(), loadSubjects(), loadChart(), loadEntries()]);
}

function bindEvents() {
  $("entry-form").addEventListener("submit", submitForm);
  $("cancel-edit").addEventListener("click", () => {
    resetForm();
    loadEntries();
  });

  document.querySelectorAll(".segmented button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".segmented button").forEach((b) => b.classList.remove("active"));
      button.classList.add("active");
      state.days = Number(button.dataset.days);
      loadChart();
    });
  });

  $("chart-subject").addEventListener("change", (e) => {
    state.chartSubject = e.target.value;
    loadChart();
  });

  const applyFilter = () => {
    state.filter = {
      subject: $("filter-subject").value,
      start: $("filter-start").value,
      end: $("filter-end").value,
    };
    loadEntries();
  };
  for (const id of ["filter-subject", "filter-start", "filter-end"]) {
    $(id).addEventListener("change", applyFilter);
  }
  $("filter-reset").addEventListener("click", () => {
    $("filter-form").reset();
    applyFilter();
  });

  let resizeTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(loadChart, 150);
  });
}

$("f-date").value = todayIso();
$("f-date").max = todayIso();
bindEvents();
refresh().catch((error) => toast(`API nicht erreichbar: ${error.message}`));
