/* Бурмалда Finance — клиентская логика (vanilla JS, без зависимостей).
   Общается с REST API через fetch и обновляет интерфейс. */

"use strict";

const API = "/api";

// ---- Небольшой слой работы с API -------------------------------------

async function api(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const message =
      (data && data.error && data.error.message) ||
      (data && data.detail && JSON.stringify(data.detail)) ||
      `Ошибка ${res.status}`;
    throw new Error(message);
  }
  return data;
}

// ---- Утилиты ----------------------------------------------------------

const money = (value) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 2,
  }).format(value || 0);

const MONTHS = [
  "январь", "февраль", "март", "апрель", "май", "июнь",
  "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
];

const $ = (id) => document.getElementById(id);

let categories = [];

function showToast(message, isError = false) {
  const el = $("toast");
  el.textContent = message;
  el.classList.toggle("error", isError);
  el.classList.add("show");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => el.classList.remove("show"), 2600);
}

function currentPeriod() {
  const year = Number($("filter-year").value);
  const monthRaw = $("filter-month").value;
  const month = monthRaw === "" ? null : Number(monthRaw);
  return { year, month };
}

function periodQuery() {
  const { year, month } = currentPeriod();
  let q = `?year=${year}`;
  if (month) q += `&month=${month}`;
  return q;
}

// ---- Инициализация фильтров ------------------------------------------

function initPeriodControls() {
  const now = new Date();
  const yearSel = $("filter-year");
  for (let y = now.getFullYear(); y >= now.getFullYear() - 4; y--) {
    const opt = document.createElement("option");
    opt.value = String(y);
    opt.textContent = String(y);
    yearSel.appendChild(opt);
  }
  const monthSel = $("filter-month");
  MONTHS.forEach((name, idx) => {
    const opt = document.createElement("option");
    opt.value = String(idx + 1);
    opt.textContent = name;
    monthSel.appendChild(opt);
  });
  monthSel.value = String(now.getMonth() + 1);
  // Дата по умолчанию в форме — сегодня.
  $("tx-date").value = now.toISOString().slice(0, 10);

  yearSel.addEventListener("change", refreshAll);
  monthSel.addEventListener("change", refreshAll);
  $("list-type").addEventListener("change", loadTransactions);
}

// ---- Категории --------------------------------------------------------

async function loadCategories() {
  categories = await api("/categories");
  const txType = $("tx-type").value;
  fillCategorySelect(txType);
}

function fillCategorySelect(type) {
  const sel = $("tx-category");
  sel.innerHTML = "";
  const filtered = categories.filter((c) => c.type === type);
  if (filtered.length === 0) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "— сначала создайте категорию —";
    sel.appendChild(opt);
    return;
  }
  filtered.forEach((c) => {
    const opt = document.createElement("option");
    opt.value = String(c.id);
    opt.textContent = c.name;
    sel.appendChild(opt);
  });
}

// ---- Сводка, разбивка, бюджеты, операции ------------------------------

async function loadSummary() {
  const s = await api("/analytics/summary" + periodQuery());
  $("sum-income").textContent = money(s.total_income);
  $("sum-expense").textContent = money(s.total_expense);
  $("sum-balance").textContent = money(s.balance);
}

async function loadBreakdown() {
  const items = await api("/analytics/by-category" + periodQuery() + "&type=expense");
  const list = $("breakdown");
  list.innerHTML = "";
  if (!items.length) {
    list.innerHTML = '<li class="empty">Нет расходов за период.</li>';
    return;
  }
  const max = Math.max(...items.map((i) => i.total));
  items.forEach((i) => {
    const li = document.createElement("li");
    const pct = max > 0 ? Math.round((i.total / max) * 100) : 0;
    li.innerHTML = `
      <div class="breakdown__head">
        <span>${escapeHtml(i.category_name)}</span>
        <span>${money(i.total)}</span>
      </div>
      <div class="breakdown__bar"><div class="breakdown__fill" style="width:${pct}%"></div></div>`;
    list.appendChild(li);
  });
}

async function loadBudgets() {
  const { year, month } = currentPeriod();
  const list = $("budget-list");
  if (!month) {
    list.innerHTML = '<li class="hint">Выберите месяц, чтобы увидеть бюджеты.</li>';
    return;
  }
  const items = await api(`/budgets/status?year=${year}&month=${month}`);
  list.innerHTML = "";
  if (!items.length) {
    list.innerHTML = '<li class="hint">Бюджеты на этот месяц не заданы.</li>';
    return;
  }
  items.forEach((b) => {
    const pct = Math.min(Math.round(b.used_percent), 100);
    const cls = b.over_budget ? "over" : b.used_percent >= 80 ? "warn" : "";
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="budget__head">
        <span>${escapeHtml(b.category_name)}</span>
        <span>${money(b.spent)} / ${money(b.limit_amount)}</span>
      </div>
      <div class="budget__bar"><div class="budget__fill ${cls}" style="width:${pct}%"></div></div>
      <div class="budget__meta">${b.over_budget
        ? "превышен на " + money(-b.remaining)
        : "осталось " + money(b.remaining)} · ${b.used_percent}%</div>`;
    list.appendChild(li);
  });
}

async function loadTransactions() {
  const { year, month } = currentPeriod();
  const type = $("list-type").value;
  let q = `?year=${year}`;
  if (month) q += `&month=${month}`;
  if (type) q += `&type=${type}`;
  const items = await api("/transactions" + q);
  const tbody = $("tx-tbody");
  const empty = $("tx-empty");
  tbody.innerHTML = "";
  empty.hidden = items.length > 0;
  const catNames = Object.fromEntries(categories.map((c) => [c.id, c.name]));
  items.forEach((t) => {
    const tr = document.createElement("tr");
    const cls = t.type === "income" ? "amount-income" : "amount-expense";
    const sign = t.type === "income" ? "+" : "−";
    tr.innerHTML = `
      <td>${t.occurred_on}</td>
      <td>${escapeHtml(catNames[t.category_id] || "#" + t.category_id)}</td>
      <td>${escapeHtml(t.description || "")}</td>
      <td class="num ${cls}">${sign}${money(t.amount).replace("-", "")}</td>
      <td class="num"><button class="btn--icon" title="Удалить" data-id="${t.id}">✕</button></td>`;
    tr.querySelector("button").addEventListener("click", () => deleteTransaction(t.id));
    tbody.appendChild(tr);
  });
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

// ---- Действия ---------------------------------------------------------

async function deleteTransaction(id) {
  if (!confirm("Удалить операцию?")) return;
  try {
    await api(`/transactions/${id}`, { method: "DELETE" });
    showToast("Операция удалена");
    await refreshData();
  } catch (e) {
    showToast(e.message, true);
  }
}

function bindForms() {
  // Переключение типа операции меняет список категорий.
  $("tx-type").addEventListener("change", (e) => fillCategorySelect(e.target.value));

  $("tx-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    $("tx-error").textContent = "";
    const categoryId = Number($("tx-category").value);
    if (!categoryId) {
      $("tx-error").textContent = "Сначала создайте подходящую категорию.";
      return;
    }
    const payload = {
      amount: Number($("tx-amount").value),
      type: $("tx-type").value,
      category_id: categoryId,
      description: $("tx-description").value,
      occurred_on: $("tx-date").value || null,
    };
    try {
      await api("/transactions", { method: "POST", body: JSON.stringify(payload) });
      $("tx-amount").value = "";
      $("tx-description").value = "";
      showToast("Операция добавлена");
      await refreshData();
    } catch (err) {
      $("tx-error").textContent = err.message;
    }
  });

  $("cat-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    $("cat-error").textContent = "";
    const payload = { name: $("cat-name").value, type: $("cat-type").value };
    try {
      await api("/categories", { method: "POST", body: JSON.stringify(payload) });
      $("cat-name").value = "";
      showToast("Категория добавлена");
      await loadCategories();
      fillCategorySelect($("tx-type").value);
    } catch (err) {
      $("cat-error").textContent = err.message;
    }
  });
}

// ---- Обновление ------------------------------------------------------

async function refreshData() {
  await Promise.all([
    loadSummary(),
    loadBreakdown(),
    loadBudgets(),
    loadTransactions(),
  ]);
}

async function refreshAll() {
  try {
    await refreshData();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function init() {
  initPeriodControls();
  bindForms();
  try {
    await loadCategories();
    await refreshData();
  } catch (e) {
    showToast("Не удалось загрузить данные: " + e.message, true);
  }
}

document.addEventListener("DOMContentLoaded", init);
