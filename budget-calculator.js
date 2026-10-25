document.querySelectorAll("[data-budget-calculator]").forEach((calculator, index) => {
  const locale = calculator.dataset.locale || "en-US";
  const currency = calculator.dataset.currency || "USD";
  const fields = {
    budget: calculator.querySelector("[data-budget-total]"),
    days: calculator.querySelector("[data-budget-days]"),
    elapsed: calculator.querySelector("[data-budget-elapsed]"),
    spent: calculator.querySelector("[data-budget-spent]"),
  };
  const output = {
    daily: calculator.querySelector("[data-budget-daily]"),
    expected: calculator.querySelector("[data-budget-expected]"),
    variance: calculator.querySelector("[data-budget-variance]"),
    remaining: calculator.querySelector("[data-budget-remaining]"),
    status: calculator.querySelector("[data-budget-status]"),
    error: calculator.querySelector("[data-budget-error]"),
  };
  const messages = locale === "zh-CN"
    ? {
        invalid: "请完整填写有效金额和整数天数；已过天数不可超过期间天数。",
        ahead: "当前支出高于按日平均进度。先检查原因，再评估后续安排。",
        behind: "当前支出低于按日平均进度。先检查需求、资格和线索质量，不必为追赶进度而花完预算。",
        onPace: "当前支出接近按日平均进度，仍需结合有效询盘和业务结果判断。",
        complete: "所选期间已结束，剩余每日金额不再适用。",
        over: "当前支出已超过批准预算；没有剩余额度，不代表后续可以不受控制地继续花费。",
      }
    : locale === "zh-Hant-HK"
      ? {
        invalid: "請完整填寫有效金額及整數日數；已過日數不可超過期間日數。",
        ahead: "目前支出高於按日平均進度，請檢查原因及餘下每日所需金額。",
        behind: "目前支出低於按日平均進度，先檢查需求、資格及流量質素，再決定是否調整。",
        onPace: "目前支出接近按日平均進度。仍應配合有效查詢及業務結果判斷。",
        complete: "所選期間已完結；剩餘每日金額不再適用。",
        over: "目前支出已超過批准預算；已無餘額，請先檢查及確認後續安排。",
      }
      : {
        invalid: "Complete every amount and whole-day field; elapsed days cannot exceed the period.",
        ahead: "Spend is ahead of the even daily pace. Review the cause and the required remaining daily amount.",
        behind: "Spend is behind the even daily pace. Check demand, eligibility, and traffic quality before adjusting.",
        onPace: "Spend is close to the even daily pace. Continue evaluating qualified outcomes, not spend alone.",
        complete: "The selected period is complete; a remaining daily amount no longer applies.",
        over: "Spend exceeds the approved budget. No budget remains; review and approve the next action before continuing.",
      };
  const fieldList = Object.values(fields);
  if (fieldList.some((field) => !field)) return;
  const results = calculator.querySelector(".budget-calculator-results");
  const fieldset = calculator.querySelector("fieldset");
  const reset = calculator.querySelector('[type="reset"]');
  if (fieldset) fieldset.disabled = false;
  if (reset) reset.disabled = false;
  if (output.error) {
    output.error.id ||= `budget-error-${index + 1}`;
    output.error.textContent = messages.invalid;
    output.error.setAttribute("role", "alert");
    fieldList.forEach((field) => field.setAttribute("aria-describedby", output.error.id));
  }
  const money = new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  });

  const update = () => {
    const budget = fields.budget.valueAsNumber;
    const days = fields.days.valueAsNumber;
    const elapsed = fields.elapsed.valueAsNumber;
    const spent = fields.spent.valueAsNumber;
    const invalidFields = new Set(fieldList.filter((field) =>
      !Number.isFinite(field.valueAsNumber) || !field.validity.valid));
    if (budget <= 0) invalidFields.add(fields.budget);
    if (!Number.isInteger(days) || days <= 0) invalidFields.add(fields.days);
    if (!Number.isInteger(elapsed) || elapsed < 0 || elapsed > days) invalidFields.add(fields.elapsed);
    if (spent < 0) invalidFields.add(fields.spent);
    const invalid = invalidFields.size > 0;
    fieldList.forEach((field) => field.setAttribute("aria-invalid", String(invalidFields.has(field))));

    if (output.error) output.error.hidden = !invalid;
    if (results) results.hidden = invalid;
    if (invalid) {
      for (const key of ["daily", "expected", "variance", "remaining"]) {
        if (output[key]) output[key].textContent = "—";
      }
      if (output.status) output.status.textContent = "";
      return;
    }

    const daily = budget / days;
    const expected = daily * elapsed;
    const variance = spent - expected;
    const remainingDays = days - elapsed;
    const remaining = remainingDays > 0 ? Math.max(0, budget - spent) / remainingDays : 0;
    const tolerance = Math.max(daily, expected * 0.05);

    if (output.daily) output.daily.textContent = money.format(daily);
    if (output.expected) output.expected.textContent = money.format(expected);
    if (output.variance) output.variance.textContent = `${variance >= 0 ? "+" : "-"}${money.format(Math.abs(variance))}`;
    if (output.remaining) output.remaining.textContent = remainingDays > 0 ? money.format(remaining) : "—";
    if (output.status) {
      output.status.textContent = spent > budget ? messages.over
        : remainingDays === 0 ? messages.complete
          : variance > tolerance ? messages.ahead
            : variance < -tolerance ? messages.behind : messages.onPace;
    }
  };

  calculator.addEventListener("input", update);
  calculator.addEventListener("reset", () => setTimeout(update, 0));
  calculator.addEventListener("submit", (event) => event.preventDefault());
  calculator.dataset.budgetReady = "true";
  update();
  const unavailable = calculator.querySelector("[data-budget-unavailable]");
  if (unavailable) unavailable.hidden = true;
});
