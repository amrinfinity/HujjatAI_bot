const API_URL = `${window.API_BASE_URL}/generate-legal-legal`;
const TOTAL_STEPS = 9;

const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

const form = document.getElementById("legal-legal-form");
const prevBtn = document.getElementById("prev-btn");
const nextBtn = document.getElementById("next-btn");
const submitBtn = document.getElementById("submit-btn");
const resultDiv = document.getElementById("result");
const stepProgress = document.getElementById("step-progress");

const totalAmount = document.getElementById("total_amount");
const advancePercent = document.getElementById("advance_percent");
const advanceAmount = document.getElementById("advance_amount");
const finalAmount = document.getElementById("final_amount");
const paymentType = document.getElementById("payment_type");
const stagesCount = document.getElementById("stages_count");
const stagedOptions = document.getElementById("staged-options");
const stagesPreview = document.getElementById("stages-preview");

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
  form.querySelectorAll(".step-panel").forEach((p) => {
    p.classList.toggle("active", Number(p.dataset.step) === step);
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

function val(name) {
  const el = form.elements[name];
  if (!el) return "";
  return typeof el.value === "string" ? el.value.trim() : el.value;
}

function radioBool(name) {
  return form.querySelector(`input[name="${name}"]:checked`)?.value === "true";
}

function checkedValues(name) {
  return [...form.querySelectorAll(`input[name="${name}"]:checked`)].map((el) => el.value);
}

function validateStir(prefix) {
  const stir = val(`${prefix}_stir`);
  if (!/^\d{9}$/.test(stir)) {
    alert(`${prefix === "p1" ? "Birinchi" : "Ikkinchi"} tomon STIR 9 ta raqamdan iborat bo'lishi kerak.`);
    return false;
  }
  return true;
}

function validateCurrentStep() {
  const panel = form.querySelector(`.step-panel[data-step="${currentStep}"]`);
  for (const input of panel.querySelectorAll("input, select, textarea")) {
    if (input.type === "radio" || input.type === "checkbox") continue;
    if (input.offsetParent === null) continue;
    if (!input.checkValidity()) {
      input.reportValidity();
      return false;
    }
  }
  if (currentStep === 1) return validateStir("p1");
  if (currentStep === 2) return validateStir("p2");
  if (currentStep === 5 && checkedValues("payment_methods").length === 0) {
    alert("Kamida bitta to'lov usulini tanlang.");
    return false;
  }
  return true;
}

function buildPaymentStages() {
  const total = parseFloat(totalAmount.value) || 0;
  const type = paymentType.value;
  const advPct = parseFloat(advancePercent.value) || 30;

  if (type === "one_time") {
    return [{
      name: "To'liq to'lov",
      percent: 100,
      amount: total,
      condition: "Shartnoma imzolanganidan so'ng 5 ish kuni ichida.",
    }];
  }

  if (type === "monthly") {
    return [{
      name: "Oylik abonement",
      percent: 100,
      amount: total,
      condition: "Har oy boshida oldindan to'lanadi.",
    }];
  }

  const n = parseInt(stagesCount.value, 10) || 3;
  const finalPct = 40;
  const middleTotal = Math.max(100 - advPct - finalPct, 0);
  const middleCount = Math.max(n - 2, 0);
  const stages = [{
    name: "Avans",
    percent: advPct,
    amount: (total * advPct) / 100,
    condition: "Shartnoma imzolanganidan so'ng 5 ish kuni ichida.",
  }];

  if (middleCount > 0) {
    const eachPct = middleTotal / middleCount;
    for (let i = 0; i < middleCount; i++) {
      stages.push({
        name: `${i + 2}-bosqich`,
        percent: eachPct,
        amount: (total * eachPct) / 100,
        condition: "Oldingi bosqich bajarilgandan so'ng 10 ish kuni ichida.",
      });
    }
  }

  stages.push({
    name: "Yakuniy",
    percent: finalPct,
    amount: (total * finalPct) / 100,
    condition: "Ish qabul qilingandan so'ng 10 ish kuni ichida.",
  });

  return stages;
}

function recalcPayments() {
  const stages = buildPaymentStages();
  const total = parseFloat(totalAmount.value) || 0;

  if (paymentType.value === "staged") {
    advanceAmount.value = stages[0]?.amount.toFixed(2) || "0";
    finalAmount.value = stages[stages.length - 1]?.amount.toFixed(2) || "0";
    stagesPreview.innerHTML = `<label>To'lov bosqichlari</label><div class="checkbox-group">${
      stages.map((s) =>
        `<label style="font-size:13px">${s.name}: ${s.percent.toFixed(1)}% — ${s.amount.toLocaleString()} (${s.condition})</label>`
      ).join("")
    }</div>`;
  } else if (paymentType.value === "one_time") {
    advanceAmount.value = total.toFixed(2);
    finalAmount.value = "0.00";
    stagesPreview.innerHTML = "";
  } else {
    advanceAmount.value = "0.00";
    finalAmount.value = total.toFixed(2);
    stagesPreview.innerHTML = `<p style="font-size:13px;color:#475569">Oylik to'lov: ${total.toLocaleString()} / oy</p>`;
  }
}

function togglePaymentUI() {
  const isStaged = paymentType.value === "staged";
  stagedOptions.classList.toggle("hidden", !isStaged);
  advancePercent.closest(".field-row").classList.toggle("hidden", paymentType.value === "one_time");
  recalcPayments();
}

function readParty(prefix) {
  return {
    org_name: val(`${prefix}_org_name`),
    org_form: val(`${prefix}_org_form`),
    stir: val(`${prefix}_stir`),
    mfy: val(`${prefix}_mfy`),
    oked: val(`${prefix}_oked`),
    account_number: val(`${prefix}_account`),
    bank_name: val(`${prefix}_bank`),
    mfo: val(`${prefix}_mfo`),
    legal_address: val(`${prefix}_legal_address`),
    actual_address: val(`${prefix}_actual_address`),
    director_name: val(`${prefix}_director`),
    director_position: val(`${prefix}_director_position`) || "Direktor",
    power_of_attorney: val(`${prefix}_power`),
    phone: val(`${prefix}_phone`),
    email: val(`${prefix}_email`),
    website: val(`${prefix}_website`),
  };
}

function parseErrorDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => {
      if (item && typeof item === "object") {
        return `${item.loc?.slice(-1)[0] || "maydon"}: ${item.msg}`;
      }
      return String(item);
    }).join("; ");
  }
  return "Xatolik yuz berdi, qayta urinib ko'ring";
}

function buildPayload() {
  const stages = buildPaymentStages();
  return {
    party_first: readParty("p1"),
    party_second: readParty("p2"),
    service_type: val("service_type"),
    service_description: val("service_description"),
    work_scope: val("work_scope"),
    has_technical_spec: radioBool("has_technical_spec"),
    effective_date: val("effective_date"),
    start_date: val("start_date"),
    end_date: val("end_date"),
    duration_days: parseInt(val("duration_days"), 10),
    contract_term: val("contract_term"),
    total_amount: parseFloat(val("total_amount")),
    currency: val("currency"),
    payment_type: paymentType.value,
    stages_count: parseInt(stagesCount.value, 10) || stages.length,
    payment_stages: stages,
    advance_percent: parseFloat(val("advance_percent")) || 30,
    advance_amount: parseFloat(advanceAmount.value) || 0,
    final_amount: parseFloat(finalAmount.value) || 0,
    payment_methods: checkedValues("payment_methods"),
    penalty_percent: parseFloat(val("penalty_percent")) || 0.1,
    penalty_max_days: parseInt(val("penalty_max_days"), 10) || 30,
    quality_standard: val("quality_standard"),
    acceptance_days: parseInt(val("acceptance_days"), 10) || 10,
    fix_days: parseInt(val("fix_days"), 10) || 5,
    acceptance_act_required: radioBool("acceptance_act_required"),
    liability_limit: val("liability_limit"),
    warranty_months: parseInt(val("warranty_months"), 10) || 12,
    free_fixes: parseInt(val("free_fixes"), 10) || 3,
    insurance_required: radioBool("insurance_required"),
    nda_required: radioBool("nda_required"),
    nda_years: parseInt(val("nda_years"), 10) || 3,
    ip_owner: form.querySelector('input[name="ip_owner"]:checked')?.value || "party_first",
    repository_transfer: radioBool("repository_transfer"),
    contract_number: val("contract_number"),
    contract_date: val("contract_date"),
    contract_place: val("contract_place"),
    copies_count: parseInt(val("copies_count"), 10) || 2,
    electronic_signature: radioBool("electronic_signature"),
  };
}

prevBtn.addEventListener("click", () => { if (currentStep > 1) showStep(currentStep - 1); });
nextBtn.addEventListener("click", () => {
  if (!validateCurrentStep()) return;
  if (currentStep < TOTAL_STEPS) showStep(currentStep + 1);
});

[paymentType, totalAmount, advancePercent, stagesCount].forEach((el) => {
  el.addEventListener("input", () => { togglePaymentUI(); });
  el.addEventListener("change", () => { togglePaymentUI(); });
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

const today = new Date().toISOString().split("T")[0];
document.getElementById("contract_date").value = today;
document.getElementById("contract_number").value = `YY-${new Date().getFullYear()}-001`;
form.elements.effective_date.value = today;
form.elements.start_date.value = today;

initProgress();
togglePaymentUI();
showStep(1);
