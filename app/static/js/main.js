// ── FleetMS Main JS ──────────────────────────────────────────────────

// Currency
const APP_CURRENCY = window.APP_CURRENCY || 'NGN';

const formatCurrency = (value) => {
  const currencyMap = {
    NGN: { symbol: '₦', locale: 'en-NG' },
    USD: { symbol: '$', locale: 'en-US' },
    EUR: { symbol: '€', locale: 'de-DE' }
  };

  const cfg = currencyMap[APP_CURRENCY] || currencyMap['NGN'];

  return cfg.symbol + Number(value).toLocaleString(cfg.locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  });
};

// Sidebar toggle
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('sidebarOverlay').classList.toggle('open');
}

function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebarOverlay').classList.remove('open');
}

function toggleSidebarCollapse() {
  const collapsed = document.documentElement.classList.toggle('sidebar-collapsed');
  localStorage.setItem('sidebarCollapsed', collapsed ? '1' : '0');
}

// Auto-dismiss flash messages
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    document.querySelectorAll('.flash').forEach(el => {
      el.style.transition = 'opacity 0.5s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    });
  }, 5000);
});

// ── Toast system ─────────────────────────────────────────────────────

const TOAST_ICONS = {
  success: 'fa-circle-check',
  error: 'fa-circle-exclamation',
  warning: 'fa-triangle-exclamation',
  info: 'fa-circle-info',
};

function showToast(message, type = 'success', duration = 5000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <i class="fa-solid ${TOAST_ICONS[type] || TOAST_ICONS.info}"></i>
    <span class="toast-body">${message}</span>
    <button class="toast-close" aria-label="Dismiss">
      <i class="fa-solid fa-xmark"></i>
    </button>`;

  container.appendChild(toast);

  const dismiss = () => {
    toast.classList.add('toast-leaving');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
  };

  toast.querySelector('.toast-close').addEventListener('click', dismiss);
  if (duration > 0) setTimeout(dismiss, duration);
}

// Fire toasts for query-param flash messages on page load
document.addEventListener('DOMContentLoaded', (e) => {
  const flashHeader = e.detail.xhr.getResponseHeader('HX-Flash');
  if (flashHeader) {
    const [type, ...rest] = flashHeader.split(':');
    showToast(rest.join(':').trim(), type);
  }
});

// ── HTMX: toast support for hx-post responses ─────────────────────────

document.addEventListener('htmx:afterRequest', (e) => {
  const flashHeader = e.detail.xhr.getResponseHeader('HX-Flash');
  if (flashHeader) {
    const [type, ...rest] = flashHeader.split(':');
    showToast(rest.join(':').trim(), type);
  }
});

// HX-Trigger: showToast  (HTMX native event trigger)
document.addEventListener('showToast', (e) => {
  const { message, type } = e.detail || {};
  if (message) showToast(message, type || 'success');
});

// ── Theme toggle ─────────────────────────────────────────────────────
function toggleTheme() {
  const isLight = document.documentElement.classList.toggle('light');
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
  updateThemeIcon(isLight);
}

function updateThemeIcon(isLight) {
  document.getElementById('theme-icon-light').style.display = isLight ? '' : 'none';
  document.getElementById('theme-icon-dark').style.display = isLight ? 'none' : '';
}

document.addEventListener('DOMContentLoaded', () => {
  updateThemeIcon(document.documentElement.classList.contains('light'));
});

// ── Searchable select (lightweight combobox) ─────────────────────────
function initSearchableSelect(root) {
  if (root.dataset.ssInit) return;
  root.dataset.ssInit = '1';

  const input = root.querySelector('.ss-input');
  const menu = root.querySelector('.ss-menu');
  const clearBtn = root.querySelector('.ss-clear');
  const options = Array.from(menu.querySelectorAll('.ss-option'));
  const redirectBase = root.dataset.redirectBase;
  const redirectParam = root.dataset.redirectParam || 'value';
  let activeIndex = -1;

  const visibleOptions = () => options.filter(o => o.style.display !== 'none');

  function setActive(index) {
    options.forEach(o => o.classList.remove('active'));
    const vis = visibleOptions();
    activeIndex = index;
    if (vis[index]) {
      vis[index].classList.add('active');
      vis[index].scrollIntoView({ block: 'nearest' });
    }
  }

  function filterOptions() {
    const q = input.value.trim().toLowerCase();
    let matches = 0;
    options.forEach(opt => {
      const show = !q || opt.dataset.label.toLowerCase().includes(q);
      opt.style.display = show ? '' : 'none';
      if (show) matches++;
    });
    menu.querySelectorAll('.ss-empty').forEach(el => el.remove());
    if (!matches) {
      const empty = document.createElement('div');
      empty.className = 'ss-empty';
      empty.textContent = 'No matches';
      menu.appendChild(empty);
    }
    setActive(-1);
  }

  function openMenu() { root.classList.add('open'); filterOptions(); }
  function closeMenu() { root.classList.remove('open'); setActive(-1); }

  function selectOption(opt) {
    input.value = opt.dataset.label;
    if (clearBtn) clearBtn.hidden = !opt.dataset.value;
    closeMenu();
    if (redirectBase) {
      const value = opt.dataset.value;
      window.location = redirectBase + (value ? `?${redirectParam}=${encodeURIComponent(value)}` : '');
    }
  }

  input.addEventListener('focus', openMenu);
  input.addEventListener('click', openMenu);
  input.addEventListener('input', () => {
    if (clearBtn) clearBtn.hidden = !input.value;
    root.classList.add('open');
    filterOptions();
  });
  input.addEventListener('keydown', (e) => {
    const vis = visibleOptions();
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (!root.classList.contains('open')) { openMenu(); return; }
      setActive(Math.min(activeIndex + 1, vis.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive(Math.max(activeIndex - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && vis[activeIndex]) selectOption(vis[activeIndex]);
    } else if (e.key === 'Escape') {
      closeMenu();
      input.blur();
    }
  });

  options.forEach(opt => {
    opt.addEventListener('mousedown', (e) => { e.preventDefault(); selectOption(opt); });
  });

  clearBtn?.addEventListener('click', (e) => {
    e.preventDefault();
    input.value = '';
    clearBtn.hidden = true;
    if (redirectBase) {
      window.location = redirectBase;
    } else {
      filterOptions();
      input.focus();
    }
  });

  document.addEventListener('click', (e) => { if (!root.contains(e.target)) closeMenu(); });
}

function initSearchableSelects(scope = document) {
  scope.querySelectorAll('.searchable-select').forEach(initSearchableSelect);
}

document.addEventListener('DOMContentLoaded', () => initSearchableSelects());
document.addEventListener('htmx:afterSwap', (e) => initSearchableSelects(e.target));


// Confirm delete modals
function confirmDelete(formId, message) {
  if (confirm(message || 'Are you sure you want to delete this? This action cannot be undone.')) {
    document.getElementById(formId).submit();
  }
}

// Chart.js defaults
if (typeof Chart !== 'undefined') {
  Chart.defaults.color = '#8b91a8';
  Chart.defaults.borderColor = '#2a2e3f';
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.font.size = 12;
}

// Initialize charts if data attributes present
document.addEventListener('DOMContentLoaded', () => {
  // Fuel chart
  const fuelChartEl = document.getElementById('fuelChart');
  if (fuelChartEl && fuelChartEl.dataset.chart) {
    const data = JSON.parse(fuelChartEl.dataset.chart);
    new Chart(fuelChartEl, {
      type: 'line',
      data: {
        labels: data.map(d => d.month),
        datasets: [{
          label: 'Fuel Cost',
          data: data.map(d => d.cost),
          borderColor: '#4f7ef8',
          backgroundColor: 'rgba(79,126,248,0.08)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#4f7ef8',
          pointRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#1a1d27',
            borderColor: '#2a2e3f',
            borderWidth: 1,
            callbacks: {
              label: ctx => ` ${formatCurrency(ctx.parsed.y)}`
            }
          }
        },
        scales: {
          x: { grid: { color: '#2a2e3f' } },
          y: {
            grid: { color: '#2a2e3f' },
            ticks: {
              callback: v => formatCurrency(v)
            }
          }
        }
      }
    });
  }

  // Status doughnut chart
  const statusChartEl = document.getElementById('statusChart');
  if (statusChartEl && statusChartEl.dataset.chart) {
    const data = JSON.parse(statusChartEl.dataset.chart);
    new Chart(statusChartEl, {
      type: 'doughnut',
      data: {
        labels: ['Active', 'In Maintenance', 'Out of Service', 'Reserved'],
        datasets: [{
          data: [data.active, data.in_maintenance, data.out_of_service, data.reserved],
          backgroundColor: ['#34d399', '#fbbf24', '#f87171', '#60a5fa'],
          borderWidth: 0,
          hoverOffset: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { padding: 16, usePointStyle: true, pointStyleWidth: 8 }
          }
        }
      }
    });
  }

  // Reports monthly chart
  const monthlyChartEl = document.getElementById('monthlyChart');
  if (monthlyChartEl && monthlyChartEl.dataset.chart) {
    const data = JSON.parse(monthlyChartEl.dataset.chart);
    new Chart(monthlyChartEl, {
      type: 'bar',
      data: {
        labels: data.map(d => d.month),
        datasets: [
          {
            label: 'Fuel',
            data: data.map(d => d.fuel),
            backgroundColor: 'rgba(79,126,248,0.7)',
            borderRadius: 4,
          },
          {
            label: 'Maintenance',
            data: data.map(d => d.maintenance),
            backgroundColor: 'rgba(251,191,36,0.7)',
            borderRadius: 4,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top' },
          tooltip: {
            backgroundColor: '#1a1d27',
            borderColor: '#2a2e3f',
            borderWidth: 1,
            callbacks: {
              label: ctx => ` ${ctx.dataset.label}: ${formatCurrency(ctx.parsed.y)}`
            }
          }
        },
        scales: {
          x: { stacked: false, grid: { display: false } },
          y: {
            grid: { color: '#2a2e3f' },
            ticks: {
              callback: v => formatCurrency(v)
            }
          }
        }
      }
    });
  }
});


// ── Submenu toggle ────────────────────────────────────────────────────

function toggleSubmenu(trigger) {
  const submenu = trigger.nextElementSibling;
  if (!submenu || !submenu.classList.contains('submenu')) return;

  submenu.classList.add('animated');

  const isOpen = trigger.classList.contains('sub-open');

  document.querySelectorAll('.nav-item.has-sub.sub-open').forEach(el => {
    if (el !== trigger) {
      el.classList.remove('sub-open');
      el.nextElementSibling?.classList.remove('sub-open');
    }
  });

  trigger.classList.toggle('sub-open', !isOpen);
  submenu.classList.toggle('sub-open', !isOpen);

  // Persist open state so page reloads keep it open
  const key = trigger.querySelector('span')?.textContent.trim();
  if (key) {
    const open = JSON.parse(localStorage.getItem('openSubmenus') || '[]');
    const updated = isOpen ? open.filter(k => k !== key) : [...new Set([...open, key])];
    localStorage.setItem('openSubmenus', JSON.stringify(updated));
  }
}

// Restore persisted submenu state on load
document.addEventListener('DOMContentLoaded', () => {
  const open = JSON.parse(localStorage.getItem('openSubmenus') || '[]');
  document.querySelectorAll('.nav-item.has-sub').forEach(trigger => {
    const key = trigger.querySelector('span')?.textContent.trim();
    if (key && open.includes(key)) {
      trigger.classList.add('sub-open');
      trigger.nextElementSibling?.classList.add('sub-open');
    }
  });
});


document.querySelectorAll('.nav-item.has-sub').forEach(item => {
  item.addEventListener('mouseenter', () => {
    if (!document.documentElement.classList.contains('sidebar-collapsed')) return;
    const rect = item.getBoundingClientRect();
    item.style.setProperty('--item-top', rect.top + 'px');
    item.style.setProperty('--item-height', rect.height + 'px');
  });
});


function redirectOnSuccess(url, event) {
  if (event.detail.successful) {
    window.location = url;
  }
}

// Redirect HTMX request without swapping
function redirect(url, event) {
  if (event.detail.xhr.status === 200) {
    event.preventDefault();
    window.location.href = url;
  }
}

// Remove empty query params from url before get request
document.body.addEventListener("htmx:configRequest", (event) => {
  if (event.detail.verb !== "get") return;

  for (const [key, value] of Object.entries(event.detail.parameters)) {
    if (value === "") {
      delete event.detail.parameters[key];
    }
  }
});

// Thousands formatting for input fields
function attachThousandsFormatting(input, { allowDecimal = false } = {}) {
  function format(value) {
    const raw = value.replace(/,/g, "").trim();

    if (raw === "" || isNaN(Number(raw))) return value;

    if (allowDecimal) {
      const [intPart, decPart] = raw.split(".");
      const formattedInt = Number(intPart || 0).toLocaleString("en-US");
      return decPart !== undefined
        ? formattedInt + "." + decPart
        : formattedInt;
    }

    return Number(raw).toLocaleString("en-US");
  }

  function unformat(value) {
    return value.replace(/,/g, "");
  }

  input.addEventListener("blur", () => {
    input.value = format(input.value);
  });

  input.addEventListener("focus", () => {
    input.value = unformat(input.value);
  });
}

// Automatically attach to all matching inputs
document.querySelectorAll(".thousands").forEach((input) => {
  attachThousandsFormatting(input, {
    allowDecimal: input.dataset.decimal === "true",
  });
});
