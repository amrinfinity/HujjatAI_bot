const API_URL = `${window.API_BASE_URL}/generate-individual-legal`;
const TOTAL_STEPS = 8;

const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const form = document.getElementById("individual-legal-form");
const prevBtn = document.getElementById("prev-btn");
const nextBtn = document.getElementById("next-btn");
const submitBtn = document.getElementById("submit-btn");
const resultDiv = document.getElementById("result");
const stepProgress = document.getElementById("step-progress");

const totalAmount = document.getElementById("total_amount");
const advancePercent = document.getElementById("advance_percent");
const advanceAmount = document.getElementById("advance_amount");
const finalAmount = document.getElementById("final_amount");

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

function updateStepLabels() {
  const isClientLegal = getContractType() === "client_legal";
  const legalRole = isClientLegal ? "Buyurtmachi" : "Ijrochi";
  const individualRole = isClientLegal ? "Ijrochi" : "Buyurtmachi";

  document.getElementById("legal-step-title").textContent =
    `Qadam 2: ${legalRole} (Yuridik shaxs) ma'lumotlari`;
  document.getElementById("legal-step-desc").textContent =
    `${legalRole} — yuridik shaxs sifatida ma'lumotlarni kiriting.`;

  document.getElementById("individual-step-title").textContent =
    `Qadam 3: ${individualRole} (Jismoniy shaxs) ma'lumotlari`;
  document.getElementById("individual-step-desc").textContent =
    `${individualRole} — jismoniy shaxs sifatida ma'lumotlarni kiriting.`;
}

function getContractType() {
  const el = form.querySelector('input[name="contract_type"]:checked');
  return el?.value || "client_legal";
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
}

function validateCurrentStep() {
  const panel = form.querySelector(`.step-panel[data-step="${currentStep}"]`);
  const inputs = panel.querySelectorAll("input, select, textarea");
  for (const input of inputs) {
    if (input.type === "radio" || input.type === "checkbox") continue;
    if (!input.checkValidity()) {
      input.reportValidity();
      return false;
    }
  }

  if (currentStep === 2) {
    const stir = form.elements.legal_stir.value.trim();
    if (!/^\d{9}$/.test(stir)) {
      alert("STIR 9 ta raqamdan iborat bo'lishi kerak.");
      return false;
    }
  }

  if (currentStep === 3) {
    const pinfl = form.elements.ind_pinfl.value.trim();
    if (!/^\d{14}$/.test(pinfl)) {
      alert("JSHSHIR/PINFL 14 ta raqamdan iborat bo'lishi kerak.");
      return false;
    }
  }

  if (currentStep === 6) {
    if (checkedValues("payment_methods").length === 0) {
      alert("Kamida bitta to'lov usulini tanlang.");
      return false;
    }
  }

  return true;
}

function todayISO() {
  return new Date().toISOString().split("T")[0];
}

function recalcPayments() {
  const total = parseFloat(totalAmount.value) || 0;
  const advPct = parseFloat(advancePercent.value) || 0;
  advanceAmount.value = ((total * advPct) / 100).toFixed(2);
  finalAmount.value = (total - parseFloat(advanceAmount.value)).toFixed(2);
}

function val(name) {
  const el = form.elements[name];
  if (!el) return "";
  return typeof el.value === "string" ? el.value.trim() : el.value;
}

function checkedValues(name) {
  return [...form.querySelectorAll(`input[name="${name}"]:checked`)].map((el) => el.value);
}

function radioBool(name) {
  return form.querySelector(`input[name="${name}"]:checked`)?.value === "true";
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
    contract_type: getContractType(),
    legal_entity: {
      org_name: val("legal_org_name"),
      stir: val("legal_stir"),
      mfy: val("legal_mfy"),
      account_number: val("legal_account"),
      bank_name: val("legal_bank"),
      legal_address: val("legal_address"),
      actual_address: val("legal_actual_address"),
      director_name: val("legal_director"),
      director_position: val("legal_director_position") || "Direktor",
      power_of_attorney: val("legal_power_of_attorney"),
      phone: val("legal_phone"),
      email: val("legal_email"),
    },
    individual: {
      full_name: val("ind_full_name"),
      birth_date: val("ind_birth_date"),
      passport: val("ind_passport"),
      pinfl: val("ind_pinfl"),
      address: val("ind_address"),
      phone: val("ind_phone"),
      email: val("ind_email"),
      card_number: val("ind_card"),
      bank_name: val("ind_bank"),
    },
    service_type: val("service_type"),
    service_description: val("service_description"),
    work_scope: val("work_scope"),
    start_date: val("start_date"),
    end_date: val("end_date"),
    duration_days: parseInt(val("duration_days"), 10),
    total_amount: parseFloat(val("total_amount")),
    currency: val("currency"),
    advance_percent: parseFloat(val("advance_percent")) || 50,
    advance_amount: parseFloat(val("advance_amount")) || 0,
    final_amount: parseFloat(val("final_amount")) || 0,
    payment_methods: checkedValues("payment_methods"),
    penalty_percent: parseFloat(val("penalty_percent")) || 0.1,
    nda_required: radioBool("nda_required"),
    nda_years: parseInt(val("nda_years"), 10) || 2,
    warranty_months: parseInt(val("warranty_months"), 10) || 6,
    liability_limit: val("liability_limit"),
    contract_number: val("contract_number"),
    contract_date: val("contract_date"),
    contract_place: val("contract_place"),
  };
}

prevBtn.addEventListener("click", () => {
  if (currentStep > 1) showStep(currentStep - 1);
});

nextBtn.addEventListener("click", () => {
  if (!validateCurrentStep()) return;
  if (currentStep < TOTAL_STEPS) showStep(currentStep + 1);
});

form.querySelectorAll('input[name="contract_type"]').forEach((el) => {
  el.addEventListener("change", updateStepLabels);
});

[totalAmount, advancePercent].forEach((el) => {
  el.addEventListener("input", recalcPayments);
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!validateCurrentStep()) return;

  submitBtn.disabled = true;
  submitBtn.textContent = "Shartnoma tayyorlanmoqda...";
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
      <strong>✅ Shartnoma muvaffaqiyatli yaratildi!</strong><br>
      Fayl: ${result.filename}<br>
      <a href="${result.download_url}" target="_blank" rel="noopener">📥 PDF yuklab olish</a>
    `;
    tg?.HapticFeedback?.notificationOccurred("success");
    resultDiv.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    resultDiv.className = "result error";
    resultDiv.innerHTML = `<strong>❌ Xatolik:</strong> ${err.message}`;
    tg?.HapticFeedback?.notificationOccurred("error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "📄 Shartnomani yaratish";
  }
});

initProgress();
document.getElementById("contract_date").value = todayISO();
document.getElementById("contract_number").value = `JY-${new Date().getFullYear()}-001`;
updateStepLabels();
recalcPayments();
showStep(1);
