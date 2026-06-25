const DOM = {
  categoryFilters: document.getElementById("category-filters"),
  selectAllCategoriesButton: document.getElementById("select-all-categories"),
  startQuizButton: document.getElementById("start-quiz"),
  resetSessionButton: document.getElementById("reset-session"),
  quizPanel: document.getElementById("quiz-panel"),
  questionId: document.getElementById("question-id"),
  questionCategory: document.getElementById("question-category"),
  questionDifficulty: document.getElementById("question-difficulty"),
  questionCount: document.getElementById("question-count"),
  questionText: document.getElementById("question-text"),
  questionExtra: document.getElementById("question-extra"),
  choicesForm: document.getElementById("choices-form"),
  submitAnswerButton: document.getElementById("submit-answer"),
  resultPanel: document.getElementById("result-panel"),
  resultMessage: document.getElementById("result-message"),
  resultAnswer: document.getElementById("result-answer"),
  resultExplanation: document.getElementById("result-explanation"),
  resultPoint: document.getElementById("result-point"),
  nextQuestionButton: document.getElementById("next-question"),
  statsAttempts: document.getElementById("stats-attempts"),
  statsCorrect: document.getElementById("stats-correct"),
  statsRate: document.getElementById("stats-rate"),
  statsAvailable: document.getElementById("stats-available"),
  statsActiveFilters: document.getElementById("stats-active-filters"),
  errorPanel: document.getElementById("error-panel"),
  filterStatus: document.getElementById("filter-status"),
  filterDetails: document.querySelector(".filter-details")
};

let questions = [];
let questionIndex = 0;
let quizStarted = false;

function init() {
  renderCategoryFilters();
  addEventListeners();
  loadQuestionData();
}

function addEventListeners() {
  DOM.selectAllCategoriesButton.addEventListener("click", handleSelectAllCategories);
  DOM.startQuizButton.addEventListener("click", handleStartQuiz);
  DOM.resetSessionButton.addEventListener("click", handleResetSession);
  DOM.submitAnswerButton.addEventListener("click", handleSubmitAnswer);
  DOM.nextQuestionButton.addEventListener("click", handleNextQuestion);
}

function renderCategoryFilters() {
  DOM.categoryFilters.innerHTML = "";
  QuizConstants.categories.forEach((category) => {
    const id = `category-${category.replace(/[^\w\-]/g, "-")}`;
    const wrapper = document.createElement("label");
    wrapper.className = "category-item";
    wrapper.innerHTML = `
      <input type="checkbox" id="${id}" value="${category}" checked />
      <span>${category}</span>
    `;
    const checkbox = wrapper.querySelector("input");
    checkbox.addEventListener("change", handleCategoryChange);
    DOM.categoryFilters.appendChild(wrapper);
  });
  updateFilterStatus();
}

function getSelectedCategories() {
  const inputs = DOM.categoryFilters.querySelectorAll("input[type=checkbox]");
  const selected = Array.from(inputs)
    .filter((input) => input.checked)
    .map((input) => input.value);
  return selected;
}

function handleCategoryChange() {
  updateFilterStatus();
  if (quizStarted) {
    const selectedCategories = getSelectedCategories();
    QuizEngine.setCategoryFilter(selectedCategories);
    renderStats();
  }
}

function handleSelectAllCategories() {
  const inputs = DOM.categoryFilters.querySelectorAll("input[type=checkbox]");
  inputs.forEach((input) => {
    input.checked = true;
  });
  handleCategoryChange();
}

function updateFilterStatus() {
  const selected = getSelectedCategories();
  const label = selected.length === QuizConstants.categories.length || selected.length === 0 ? "全分野" : selected.join("、");
  DOM.statsActiveFilters.textContent = label;
  DOM.filterStatus.textContent = `選択中の分野: ${label}`;
}

function loadQuestionData() {
  QuestionLoader.loadQuestions("data/questions.json")
    .then((loaded) => {
      questions = loaded;
      QuizEngine.createQuizSession(questions);
      renderStats();
      clearError();
    })
    .catch((error) => {
      showError(error.message);
      console.error(error);
    });
}

function handleStartQuiz() {
  if (questions.length === 0) {
    showError("問題データが読み込まれていません。ページをリロードして再度お試しください。");
    return;
  }

  quizStarted = true;
  questionIndex = 0;
  DOM.resultPanel.hidden = true;
  DOM.quizPanel.hidden = false;
  DOM.submitAnswerButton.disabled = false;
  DOM.nextQuestionButton.disabled = false;
  const selectedCategories = getSelectedCategories();
  QuizEngine.setCategoryFilter(selectedCategories);
  const nextQuestion = QuizEngine.getNextQuestion();
  if (!nextQuestion) {
    showError("選択した分野に利用できる問題がありません。別の分野を選択してください。");
    DOM.quizPanel.hidden = true;
    return;
  }
  questionIndex += 1;
  if (DOM.filterDetails) {
    DOM.filterDetails.open = false;
  }
  renderQuestion(nextQuestion);
  renderStats();
  clearError();
}

function handleSubmitAnswer() {
  const selectedInput = DOM.choicesForm.querySelector("input[name=choice]:checked");
  if (!selectedInput) {
    showError("選択肢を1つ選んでから送信してください。");
    return;
  }

  clearError();
  const selectedIndex = Number(selectedInput.value);
  const result = QuizEngine.checkAnswer(selectedIndex);
  if (!result) {
    showError("現在の問題を確認できません。もう一度出題開始してください。");
    return;
  }

  DOM.submitAnswerButton.disabled = true;
  DOM.choicesForm.querySelectorAll("input[name=choice]").forEach((input) => {
    input.disabled = true;
  });
  renderResult(result);
  renderStats();
}

function handleNextQuestion() {
  const nextQuestion = QuizEngine.getNextQuestion();
  if (!nextQuestion) {
    showError("これ以上の問題がありません。フィルタを変更するか、リセットしてください。");
    return;
  }
  questionIndex += 1;
  DOM.resultPanel.hidden = true;
  DOM.submitAnswerButton.disabled = false;
  renderQuestion(nextQuestion);
  renderStats();
  clearError();
}

function handleResetSession() {
  if (questions.length === 0) {
    return;
  }
  quizStarted = false;
  questionIndex = 0;
  QuizEngine.resetSession();
  DOM.quizPanel.hidden = true;
  DOM.resultPanel.hidden = true;
  DOM.submitAnswerButton.disabled = false;
  DOM.choicesForm.innerHTML = "";
  renderStats();
  clearError();
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatChemText(value) {
  const elementPattern = "H|He|Li|Be|B|C|N|O|F|Ne|Na|Mg|Al|Si|P|S|Cl|Ar|K|Ca|Fe|Cu|Zn|Br|I";
  const formulaPattern = new RegExp(
    `(^|[^A-Za-z0-9])((?:\\d+(?=${elementPattern}))?(?:(?:${elementPattern})\\d*){1,8}(?:\\^?\\d*[+-])?)(?=$|[^A-Za-z0-9])`,
    "g"
  );
  const formulaBodyPattern = new RegExp(`(${elementPattern})(\\d*)`, "g");

  function formatFormulaToken(token) {
    const coefficientMatch = token.match(new RegExp(`^(\\d+)(?=${elementPattern})`));
    const coefficient = coefficientMatch ? coefficientMatch[1] : "";
    const formulaToken = coefficient ? token.slice(coefficient.length) : token;
    const chargeMatch = formulaToken.match(/(\^?\d*[+-])$/);
    const charge = chargeMatch ? chargeMatch[1].replace("^", "") : "";
    const formula = charge ? formulaToken.slice(0, -chargeMatch[1].length) : formulaToken;
    const formattedFormula = formula.replace(formulaBodyPattern, (_, element, count) => {
      return count ? `${element}<sub>${count}</sub>` : element;
    });
    return `${coefficient}<span class="chem">${formattedFormula}${charge ? `<sup>${charge}</sup>` : ""}</span>`;
  }

  return escapeHtml(value)
    .replace(/\^(\d+)([A-Z][a-z]?)/g, "<sup>$1</sup>$2")
    .replace(/10\^(-?\d+)/g, "10<sup>$1</sup>")
    .replace(formulaPattern, (_, prefix, token) => `${prefix}${formatFormulaToken(token)}`);
}

function renderQuestion(question) {
  if (!question) {
    DOM.questionText.textContent = "問題が読み込めません。";
    return;
  }

  DOM.questionId.textContent = question.id;
  DOM.questionCategory.textContent = question.category;
  DOM.questionDifficulty.textContent = QuizConstants.difficultyLabels[question.difficulty] || "";
  DOM.questionCount.textContent = `第 ${questionIndex} 問`; 
  DOM.questionText.innerHTML = formatChemText(question.question);
  DOM.questionExtra.innerHTML = question.extra || "";
  renderChoices(question);
  DOM.resultPanel.hidden = true;
}

function renderChoices(question) {
  DOM.choicesForm.innerHTML = "";
  question.choices.forEach((choice, index) => {
    const choiceId = `choice-${index}`;
    const label = document.createElement("label");
    label.className = "choice-label";
    label.setAttribute("for", choiceId);
    label.innerHTML = `
      <input class="choice-input" type="radio" name="choice" id="${choiceId}" value="${index}" />
      <span>${formatChemText(choice)}</span>
    `;
    DOM.choicesForm.appendChild(label);
    const radio = label.querySelector("input");
    radio.addEventListener("change", () => {
      DOM.choicesForm.querySelectorAll(".choice-label").forEach((item) => item.classList.remove("choice-selected"));
      label.classList.add("choice-selected");
    });
  });
}

function renderResult(result) {
  const question = QuizEngine.getCurrentQuestion();
  if (!question) {
    return;
  }

  DOM.resultPanel.hidden = false;
  DOM.resultMessage.textContent = result.correct ? "正解です！" : "不正解です。";
  DOM.resultMessage.className = `result-message ${result.correct ? "correct" : "incorrect"}`;
  DOM.resultAnswer.innerHTML = `正解: ${formatChemText(question.choices[question.answerIndex])}`;
  DOM.resultExplanation.innerHTML = `解説: ${formatChemText(result.explanation)}`;
  DOM.resultPoint.innerHTML = result.point ? `ポイント: ${formatChemText(result.point)}` : "";

  DOM.choicesForm.querySelectorAll("label.choice-label").forEach((label, index) => {
    const input = label.querySelector("input");
    const choiceIndex = Number(input.value);
    label.classList.remove("choice-correct", "choice-wrong", "choice-selected");
    if (choiceIndex === question.answerIndex) {
      label.classList.add("choice-correct");
    }
    if (!result.correct && choiceIndex === result.selectedIndex) {
      label.classList.add("choice-wrong");
    }
  });
}

function renderStats() {
  const stats = QuizEngine.getStats();
  DOM.statsAttempts.textContent = stats.attempts;
  DOM.statsCorrect.textContent = stats.correct;
  DOM.statsRate.textContent = `${stats.rate}%`;
  DOM.statsAvailable.textContent = stats.availableCount;
  const selected = getSelectedCategories();
  DOM.statsActiveFilters.textContent = selected.length === 0 || selected.length === QuizConstants.categories.length ? "全分野" : selected.join("、");
}

function showError(message) {
  DOM.errorPanel.hidden = false;
  DOM.errorPanel.textContent = message;
}

function clearError() {
  DOM.errorPanel.hidden = true;
  DOM.errorPanel.textContent = "";
}

init();
