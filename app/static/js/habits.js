document.querySelectorAll(".btn-mark-done").forEach((btn) => {
  btn.addEventListener("click", () => {
    btn.textContent = "Hecho ✓";
    btn.classList.add("is-done");
    setTimeout(() => {
      btn.disabled = true;
    }, 0);
  });
});

const nameInput = document.querySelector("#habit-name");
const counter = document.querySelector("#word-counter");
nameInput?.addEventListener("input", () => {
  const words = nameInput.value.trim().split(/\s+/).filter(Boolean).length;
  if (counter) {
    counter.textContent = `${words} / 8 palabras`;
    counter.classList.toggle("counter-over", words > 8);
  }
});