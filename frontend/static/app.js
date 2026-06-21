/**
 * EletroReverso — Frontend (Vanilla JS)
 * Arquivo: frontend/static/app.js
 *
 * Responsabilidades:
 *   - Navegação entre seções via sidebar
 *   - Preenchimento de <select> dinâmicos via API
 *   - Submissão de formulários de cadastro
 *   - Execução e renderização de consultas
 *   - Feedback visual (toast, spinner, estado vazio)
 */

"use strict";

// ─── Utilitários ──────────────────────────────────────────────────────────────

const BASE = "";   // mesmo origin — Flask serve tudo

async function api(path, { method = "GET", body } = {}) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(BASE + path, opts);
  const data = await res.json();
  return data;
}

// ─── Toast ────────────────────────────────────────────────────────────────────

const toastEl = document.getElementById("toast");
let toastTimer;

function showToast(msg, type = "success") {
  clearTimeout(toastTimer);
  toastEl.textContent = msg;
  toastEl.className = `toast show ${type}`;
  toastTimer = setTimeout(() => toastEl.classList.remove("show"), 4000);
}

// ─── Navegação ────────────────────────────────────────────────────────────────

document.querySelectorAll(".nav-item").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));

    btn.classList.add("active");
    const sec = document.getElementById("section-" + btn.dataset.section);
    if (sec) sec.classList.add("active");
  });
});

// ─── Status de conexão ────────────────────────────────────────────────────────

async function checkStatus() {
  const dot  = document.getElementById("statusDot");
  const text = document.getElementById("statusText");
  try {
    const data = await api("/api/status");
    if (data.ok) {
      dot.className  = "status-dot ok";
      text.textContent = "Banco conectado";
    } else {
      throw new Error(data.error);
    }
  } catch {
    dot.className  = "status-dot err";
    text.textContent = "Sem conexão";
  }
}
checkStatus();

// ─── Selects dinâmicos ────────────────────────────────────────────────────────

function addOption(select, value, label) {
  const opt = document.createElement("option");
  opt.value = value;
  opt.textContent = label;
  select.appendChild(opt);
}

async function carregarPontosColeta() {
  const sel = document.getElementById("lc-ponto");
  const data = await api("/api/dados/pontos-coleta");
  if (!data.ok) return;
  data.rows.forEach(([rua, cidade, cep, estado]) => {
    addOption(sel, JSON.stringify({ rua, cidade, cep, estado }), `${rua} — ${cidade}/${estado}`);
  });
}

async function carregarLotes() {
  const sel = document.getElementById("dl-lote");
  const data = await api("/api/dados/lotes");
  if (!data.ok) return;
  data.rows.forEach(([id, data_col, cidade, estado]) => {
    addOption(sel, id, `#${id} — ${cidade}/${estado} (${data_col})`);
  });
}

async function carregarDispositivos() {
  const sel = document.getElementById("dl-disp");
  const data = await api("/api/dados/dispositivos");
  if (!data.ok) return;
  data.rows.forEach(([nome, peso, cat]) => {
    addOption(sel, nome, `${nome} (${cat}, ${peso} kg)`);
  });
}

async function carregarMateriais() {
  const sel = document.getElementById("rm-material");
  const data = await api("/api/dados/materiais");
  if (!data.ok) return;
  data.rows.forEach(([nome, tipo]) => {
    addOption(sel, nome, `${nome} — ${tipo}`);
  });
}

// Preenche o hidden fields quando o usuário escolhe um ponto de coleta
document.getElementById("lc-ponto").addEventListener("change", function () {
  if (!this.value) return;
  const p = JSON.parse(this.value);
  document.getElementById("lc-rua").value    = p.rua;
  document.getElementById("lc-cidade").value = p.cidade;
  document.getElementById("lc-cep").value    = p.cep;
  document.getElementById("lc-estado").value = p.estado;
});

carregarPontosColeta();
carregarLotes();
carregarDispositivos();
carregarMateriais();

// ─── Helpers de renderização ──────────────────────────────────────────────────

const COLUMN_LABELS = {
  cnpj:            "CNPJ",
  nome:            "Nome",
  cidade:          "Cidade",
  estado:          "Estado",
  cep:             "CEP",
  rua:             "Rua",
  id_lote:         "ID Lote",
  data_coleta:     "Data Coleta",
  cidade_origem:   "Cidade Origem",
  centro_triagem:  "Centro de Triagem",
  chegada_ao_centro: "Chegada ao Centro",
  licenca_ambiental: "Licença Ambiental",
  volume_total:    "Volume (kg)",
  media_dias:      "Média (dias)",
};

function colLabel(key) {
  return COLUMN_LABELS[key] || key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

function renderLoading(containerId) {
  document.getElementById(containerId).innerHTML = `
    <div class="loading">
      <div class="spinner"></div>
      Executando consulta...
    </div>`;
}

function renderResult(containerId, { columns, rows }) {
  const el = document.getElementById(containerId);

  if (!rows || rows.length === 0) {
    el.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24"><path d="M9 13h2v-2H9v2zm0 4h2v-2H9v2zm0-8h2V7H9v2zm4 4h2v-2h-2v2zm0 4h2v-2h-2v2zm0-8h2V7h-2v2zM5 21a2 2 0 0 1-2-2V5c0-1.1.9-2 2-2h11l5 5v11a2 2 0 0 1-2 2H5z"/></svg>
        <p>Nenhum registro encontrado.</p>
      </div>`;
    return;
  }

  const count = `<p class="result-count"><strong>${rows.length}</strong> registro${rows.length > 1 ? "s" : ""} encontrado${rows.length > 1 ? "s" : ""}.</p>`;

  const thead = `<tr>${columns.map(c => `<th>${colLabel(c)}</th>`).join("")}</tr>`;
  const tbody = rows.map(row =>
    `<tr>${row.map(val =>
      val == null
        ? `<td><span class="null-val">—</span></td>`
        : `<td>${val}</td>`
    ).join("")}</tr>`
  ).join("");

  el.innerHTML = `
    ${count}
    <div class="data-table-wrapper">
      <table class="data-table">
        <thead>${thead}</thead>
        <tbody>${tbody}</tbody>
      </table>
    </div>`;
}

function renderError(containerId, msg) {
  document.getElementById(containerId).innerHTML = `
    <div style="padding: 14px 0; color: #b91c1c; font-size: 14px;">
      <strong>Erro:</strong> ${msg}
    </div>`;
}

// ─── Cadastros ────────────────────────────────────────────────────────────────

async function cadastrarPontoColeta() {
  const payload = {
    rua:           document.getElementById("pc-rua").value.trim(),
    cidade:        document.getElementById("pc-cidade").value.trim(),
    estado:        document.getElementById("pc-estado").value.trim(),
    cep:           document.getElementById("pc-cep").value.trim(),
    capacidade_max: document.getElementById("pc-cap").value.trim(),
  };

  const res = await api("/api/cadastro/ponto-coleta", { method: "POST", body: payload });
  if (res.ok) {
    showToast(res.message, "success");
    ["pc-rua", "pc-cidade", "pc-estado", "pc-cep", "pc-cap"].forEach(id => {
      document.getElementById(id).value = "";
    });
    carregarPontosColeta();   // atualiza o select de lotes
  } else {
    showToast(res.error, "error");
  }
}

async function cadastrarLote() {
  const payload = {
    id_lote:    document.getElementById("lc-id").value.trim(),
    rua:        document.getElementById("lc-rua").value,
    cidade:     document.getElementById("lc-cidade").value,
    cep:        document.getElementById("lc-cep").value,
    estado:     document.getElementById("lc-estado").value,
    data_coleta: document.getElementById("lc-data").value,
  };

  if (!payload.rua) { showToast("Selecione um ponto de coleta.", "error"); return; }

  const res = await api("/api/cadastro/lote-coleta", { method: "POST", body: payload });
  if (res.ok) {
    showToast(res.message, "success");
    document.getElementById("lc-id").value = "";
    document.getElementById("lc-data").value = "";
    document.getElementById("lc-ponto").value = "";
    carregarLotes();
  } else {
    showToast(res.error, "error");
  }
}

async function cadastrarDispLote() {
  const payload = {
    id_lote:    document.getElementById("dl-lote").value,
    dispositivo: document.getElementById("dl-disp").value,
    quantidade: document.getElementById("dl-qtd").value,
  };

  if (!payload.id_lote)    { showToast("Selecione um lote.", "error"); return; }
  if (!payload.dispositivo){ showToast("Selecione um dispositivo.", "error"); return; }

  const res = await api("/api/cadastro/dispositivo-lote", { method: "POST", body: payload });
  if (res.ok) {
    showToast(res.message, "success");
    document.getElementById("dl-qtd").value = "";
  } else {
    showToast(res.error, "error");
  }
}

// ─── Consultas ────────────────────────────────────────────────────────────────

async function runDivisao() {
  renderLoading("result-divisao");
  const data = await api("/api/consulta/divisao-relacional");
  if (data.ok) renderResult("result-divisao", data);
  else renderError("result-divisao", data.error);
}

async function runLotesSemTriagem() {
  renderLoading("result-lotes-triagem");
  const data = await api("/api/consulta/lotes-sem-triagem");
  if (data.ok) renderResult("result-lotes-triagem", data);
  else renderError("result-lotes-triagem", data.error);
}

async function runCentrosMedia() {
  renderLoading("result-centros-media");
  const data = await api("/api/consulta/centros-acima-media");
  if (data.ok) renderResult("result-centros-media", data);
  else renderError("result-centros-media", data.error);
}

async function runRastrear() {
  const material = document.getElementById("rm-material").value;
  if (!material) { showToast("Selecione um material.", "error"); return; }
  renderLoading("result-rastrear");
  const data = await api(`/api/consulta/rastrear-por-material?material=${encodeURIComponent(material)}`);
  if (data.ok) renderResult("result-rastrear", data);
  else renderError("result-rastrear", data.error);
}

async function runTempoMedio() {
  renderLoading("result-tempo-medio");
  const data = await api("/api/consulta/tempo-medio-transporte");
  if (data.ok) renderResult("result-tempo-medio", data);
  else renderError("result-tempo-medio", data.error);
}