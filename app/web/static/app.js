document.addEventListener("change", (event) => {
  const form = event.target.closest("form[data-auto-submit]");
  if (!form) return;
  if (event.target.tagName === "SELECT" && event.target.name === "tracking_status" && event.target.value) {
    form.requestSubmit();
  }
});
