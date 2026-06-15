const API_URL = `${window.API_BASE_URL}/generate-act`;
const TOTAL_STEPS = 4;
const UNITS = ["dona", "soat", "oy", "komplekt", "xizmat"];

const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const form = document.getElementById("act-form");
const prevBtn = document.getElementById("prev-btn");
const nextBtn = document.getElementById("next-btn");
const submitBtn = document.getElementById("submit-btn");
const resultDiv = document.getElementById("result");
const stepProgress = document.getElementById("step-progress");
const itemsBody = document.getElementById("items-body");
const addRowBtn = document.getElementById("add-row-btn");
const grandTotalDisplay = document.getElementById("grand-total-display");
const grandTotalInput = document.getElementById("grand_total");

let currentStep = 1;

function initProgress() {
  stepProgress.innerHTML = "";
  for (let i = 1; i <= TOTAL_STEPS; i++) {
    const dot = document.createElement("div");
    dot.className = "step-dot";
    dot.dataset.step = i;
    stepProgress.appendChild(dot);
  }
}

function showStep(step) {
  currentStep = step;
  form.querySelectorAll(".step-panel").forEach((panel) => {
    panel.classList.toggle("active", Number(panel.dataset.step) === step);
  });

  stepProgress.querySelectorAll(".step-dot").forEach((dot) => {
    const n = Number(dot.dataset.step);
    dot.classList.toggle("active", n === step);
    dot.classList.toggle("done", n < step);
  });

  prevBtn.disabled = step === 1;
  nextBtn.classList.toggle("hidden", step === TOTAL_STEPS);
  submitBtn.classList.toggle("hidden", step !== TOTAL_STEPS);

  if (step === 4) {
    syncGrandTotalToStep4();
  }
}

function todayISO() {
  return new Date().toISOString().split("T")[0];
}

function formatMoney(amount) {
  const n = Number(amount) || 0;
  return `${n.toLocaleString("uz-UZ", { maximumFractionDigits: 2 })} so'm`;
}

function createRowRow() {
  const tr = document.createElement("tr");
  tr.className = "act-row";
  tr.innerHTML = `
    <td class="row-num">1</td>
    <td><input type="text" class="act-input act-desc" placeholder="Ish tavsifi" required></td>
    <td>
      <select class="act-input act-unit">
        ${UNITS.map((u) => `<option value="${u}">${u}</option>`).join("")}
      </select>
    </td>
    <td><input type="number" class="act-input act-qty" min="0" step="0.01" value="1" required></td>
    <td><input type="number" class="act-input act-price" min="0" step="0.01" value="0" required></td>
    <td><input type="number" class="act-input act-total" readonly tabindex="-1"></td>
    <td><button type="button" class="btn-delete-row" title="O'chirish">🗑️</button></td>
  `;

  tr.querySelector(".act-qty").addEventListener("input", () => recalcRow(tr));
  tr.querySelector(".act-price").addEventListener("input", () => recalcRow(tr));
  tr.querySelector(".btn-delete-row").addEventListener("click", () => removeRow(tr));

  return tr;
}

function recalcRow(tr) {
  const qty = parseFloat(tr.querySelector(".act-qty").value) || 0;
  const price = parseFloat(tr.querySelector(".act-price").value) || 0;
  const total = qty * price;
  tr.querySelector(".act-total").value = total.toFixed(2);
  recalcGrandTotal();
}

function renumberRows() {
  itemsBody.querySelectorAll(".act-row").forEach((tr, idx) => {
    tr.querySelector(".row-num").textContent = String(idx + 1);
  });
}

function addRow() {
  itemsBody.appendChild(createRowRow());
  renumberRows();
  const last = itemsBody.lastElementChild;
  recalcRow(last);
}

function removeRow(tr) {
  const rows = itemsBody.querySelectorAll(".act-row");
  if (rows.length <= 1) {
    alert("Kamida bitta qator bo'lishi kerak.");
    return;
  }
  tr.remove();
  renumberRows();
  recalcGrandTotal();
}

function recalcGrandTotal() {
  let sum = 0;
  itemsBody.querySelectorAll(".act-row").forEach((tr) => {
    sum += parseFloat(tr.querySelector(".act-total").value) || 0;
  });
  grandTotalDisplay.textContent = formatMoney(sum);
  grandTotalInput.value = sum.toFixed(2);
  return sum;
}

function syncGrandTotalToStep4() {
  recalcGrandTotal();
}

function getItems() {
  const items = [];
  itemsBody.querySelectorAll(".act-row").forEach((tr, idx) => {
    items.push({
      number: idx + 1,
      description: tr.querySelector(".act-desc").value.trim(),
      unit: tr.querySelector(".act-unit").value,
      quantity: parseFloat(tr.querySelector(".act-qty").value) || 0,
      price: parseFloat(tr.querySelector(".act-price").value) || 0,
      total: parseFloat(tr.querySelector(".act-total").value) || 0,
    });
  });
  return items;
}

function validateCurrentStep() {
  const panel = form.querySelector(`.step-panel[data-step="${currentStep}"]`);
  const inputs = panel.querySelectorAll("input, select, textarea");
  for (const input of inputs) {
    if (input.type === "radio" || input.type === "checkbox") continue;
    if (input.closest(".hidden")) continue;
    if (input.readOnly && input.id === "grand_total") continue;
    if (!input.checkValidity()) {
      input.reportValidity();
      return false;
    }
  }

  if (currentStep === 3) {
    const rows = itemsBody.querySelectorAll(".act-row");
    if (rows.length === 0) {
      alert("Kamida bitta ish qatorini kiriting.");
      return false;
    }
    for (const tr of rows) {
      const desc = tr.querySelector(".act-desc").value.trim();
      const qty = parseFloat(tr.querySelector(".act-qty").value);
      const price = parseFloat(tr.querySelector(".act-price").value);
      if (!desc) {
        alert("Har bir qator uchun ish nomi/tavsifini kiriting.");
        tr.querySelector(".act-desc").focus();
        return false;
      }
      if (Number.isNaN(qty) || qty <= 0) {
        alert("Miqdor 0 dan katta bo'lishi kerak.");
        tr.querySelector(".act-qty").focus();
        return false;
      }
      if (Number.isNaN(price) || price < 0) {
        alert("Narx noto'g'ri kiritilgan.");
        tr.querySelector(".act-price").focus();
        return false;
      }
    }
    if (recalcGrandTotal() <= 0) {
      alert("Jami summa 0 dan katta bo'lishi kerak.");
      return false;
    }
  }

  if (currentStep === 4) {
    const hasClaims = form.querySelector('input[name="has_claims"]:checked')?.value;
    if (hasClaims === "Ha" && !form.elements.claims_details.value.trim()) {
      alert("Da'vo tafsilotini kiriting.");
      return false;
    }
  }

  return true;
}

function val(name) {
  const el = form.elements[name];
  if (!el) return "";
  return typeof el.value === "string" ? el.value.trim() : el.value;
}

function parseErrorDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object") {
          const field = item.loc?.slice(-1)[0] || "maydon";
          return `${field}: ${item.msg}`;
        }
        return String(item);
      })
      .join("; ");
  }
  return "Xatolik yuz berdi, qayta urinib ko'ring";
}

function buildPayload() {
  return {
    act_number: val("act_number"),
    date: val("act_date"),
    city: val("city"),
    contract_number: val("contract_number"),
    contract_date: val("contract_date"),
    customer_name: val("customer_name"),
    executor_name: val("executor_name"),
    items: getItems(),
    grand_total: parseFloat(val("grand_total")) || 0,
    grand_total_words: val("grand_total_words"),
    quality_status: form.querySelector('input[name="quality_status"]:checked')?.value || "Muvaffaqiyatli bajarildi",
    has_claims: form.querySelector('input[name="has_claims"]:checked')?.value || "Yo'q",
    claims_details: val("claims_details") || null,
  };
}

prevBtn.addEventListener("click", () => {
  if (currentStep > 1) showStep(currentStep - 1);
});

nextBtn.addEventListener("click", () => {
  if (!validateCurrentStep()) return;
  if (currentStep < TOTAL_STEPS) showStep(currentStep + 1);
});

addRowBtn.addEventListener("click", addRow);

form.querySelectorAll('input[name="has_claims"]').forEach((el) => {
  el.addEventListener("change", () => {
    document.getElementById("claims-details-field").classList.toggle(
      "hidden",
      form.querySelector('input[name="has_claims"]:checked')?.value !== "Ha"
    );
  });
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!validateCurrentStep()) return;

  submitBtn.disabled = true;
  submitBtn.textContent = "Akt tayyorlanmoqda...";
  resultDiv.className = "result hidden";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload()),
    });

    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Backend bilan bog'lanib bo'lmadi. Backend ishga tushirilganini tekshiring.");
      }
      throw new Error(parseErrorDetail(result.detail) || `Server xatosi (${response.status})`);
    }

    resultDiv.className = "result success";
    resultDiv.innerHTML = `
      <strong>✅ Akt muvaffaqiyatli yaratildi!</strong><br>
      Fayl: ${result.filename}<br>
      <a href="${result.download_url}" target="_blank" rel="noopener">📥 PDF yuklab olish</a>
    `;
    tg?.HapticFeedback?.notificationOccurred("success");
    resultDiv.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    resultDiv.className = "result error";
    resultDiv.innerHTML = `<strong>❌ Xatolik:</strong> ${err.message || "Xatolik yuz berdi, qayta urinib ko'ring"}`;
    tg?.HapticFeedback?.notificationOccurred("error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "📄 Aktni yaratish";
  }
});

initProgress();
document.getElementById("act_number").value = `AKT-${new Date().getFullYear()}-001`;
document.getElementById("act_date").value = todayISO();
addRow();
showStep(1);
