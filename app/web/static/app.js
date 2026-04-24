document.addEventListener("change", (event) => {
  const form = event.target.closest("form[data-auto-submit]");
  if (!form) return;
  if (event.target.tagName === "SELECT" && event.target.name === "tracking_status" && event.target.value) {
    form.requestSubmit();
  }
});

document.addEventListener("submit", (event) => {
  const form = event.target;
  if (!(form instanceof HTMLFormElement)) return;
  if (form.dataset.cleanEmptyQuery !== "true") return;
  if ((form.getAttribute("method") || "get").toLowerCase() !== "get") return;

  event.preventDefault();

  const action = form.getAttribute("action") || window.location.pathname;
  const url = new URL(action, window.location.origin);
  const params = new URLSearchParams();

  for (const [key, value] of new FormData(form).entries()) {
    if (typeof value !== "string" || value === "") continue;
    params.append(key, value);
  }

  url.search = params.toString();
  window.location.assign(url.toString());
});
