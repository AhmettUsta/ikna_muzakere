// JavaScript açıkken soruları tek tek gösterir; kapalıyken form tüm soruları listeler.
(function () {
  const form = document.getElementById("test-formu");
  if (!form) return;

  const questions = Array.from(form.querySelectorAll(".soru"));
  const backButton = document.getElementById("geri");
  const nextButton = document.getElementById("ileri");
  const finishButton = document.getElementById("bitir");
  const progress = document.querySelector(".ilerleme");
  const progressBar = progress.querySelector(".ilerleme-cubuk span");
  const progressText = progress.querySelector(".ilerleme-yazi");
  const total = questions.length;

  const firstUnanswered = () => {
    const index = questions.findIndex((q) => !q.querySelector("input:checked"));
    return index === -1 ? total - 1 : index;
  };

  let current = firstUnanswered();

  const show = (index) => {
    current = Math.max(0, Math.min(index, total - 1));
    questions.forEach((q, i) => { q.hidden = i !== current; });
    const answered = questions.filter((q) => q.querySelector("input:checked")).length;
    progressText.textContent = `${current + 1} / ${total}`;
    progressBar.style.width = `${(answered / total) * 100}%`;
    backButton.hidden = current === 0;
    // Geri dönülen ve zaten cevaplanmış soruda, cevabı değiştirmeden ilerleyebilmek için.
    nextButton.hidden = !(current < total - 1 && questions[current].querySelector("input:checked"));
    finishButton.hidden = !(current === total - 1 && answered === total);
    questions[current].querySelector("legend").focus?.();
  };

  form.classList.add("tek-tek");
  progress.hidden = false;
  questions.forEach((q, i) => {
    q.querySelector("legend").tabIndex = -1;
    q.querySelectorAll("input").forEach((input) => {
      input.addEventListener("change", () => {
        // Seçim görünsün diye kısa bir bekleme sonrası sonraki soruya geçilir.
        window.setTimeout(() => show(i < total - 1 ? i + 1 : i), 180);
      });
    });
  });
  backButton.addEventListener("click", () => show(current - 1));
  nextButton.addEventListener("click", () => show(current + 1));
  show(current);
})();
