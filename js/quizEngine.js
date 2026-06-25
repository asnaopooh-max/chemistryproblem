const QuizEngine = (function () {
  let allQuestions = [];
  let availableQuestions = [];
  let currentQuestion = null;
  let selectedCategories = [];
  let sessionStats = { attempts: 0, correct: 0 };

  function shuffle(array) {
    const copy = [...array];
    for (let i = copy.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  }

  function createQuizSession(questions) {
    allQuestions = [...questions];
    selectedCategories = [...QuizConstants.categories];
    sessionStats = { attempts: 0, correct: 0 };
    resetAvailableQuestions();
  }

  function resetAvailableQuestions() {
    const filtered = allQuestions.filter((item) => selectedCategories.length === 0 || selectedCategories.includes(item.category));
    availableQuestions = shuffle(filtered);
  }

  function getAvailableCategories() {
    return QuizConstants.categories.filter((category) => allQuestions.some((item) => item.category === category));
  }

  function setCategoryFilter(categories) {
    selectedCategories = categories.length === 0 ? [...QuizConstants.categories] : [...categories];
    resetAvailableQuestions();
  }

  function getCurrentQuestion() {
    return currentQuestion;
  }

  function getNextQuestion() {
    if (availableQuestions.length === 0) {
      resetAvailableQuestions();
    }
    if (availableQuestions.length === 0) {
      currentQuestion = null;
      return null;
    }
    currentQuestion = availableQuestions.shift();
    return currentQuestion;
  }

  function checkAnswer(selectedIndex) {
    if (!currentQuestion) {
      return null;
    }
    const isCorrect = selectedIndex === currentQuestion.answerIndex;
    sessionStats.attempts += 1;
    if (isCorrect) {
      sessionStats.correct += 1;
    }
    return {
      correct: isCorrect,
      selectedIndex,
      answerIndex: currentQuestion.answerIndex,
      explanation: currentQuestion.explanation,
      point: currentQuestion.point || ""
    };
  }

  function getStats() {
    const { attempts, correct } = sessionStats;
    const rate = attempts === 0 ? 0 : Math.round((correct / attempts) * 100);
    return {
      attempts,
      correct,
      rate,
      availableCount: allQuestions.filter((item) => selectedCategories.includes(item.category)).length,
      activeFilterCount: selectedCategories.length
    };
  }

  function resetSession() {
    selectedCategories = [...QuizConstants.categories];
    sessionStats = { attempts: 0, correct: 0 };
    resetAvailableQuestions();
    currentQuestion = null;
  }

  return {
    createQuizSession,
    getAvailableCategories,
    setCategoryFilter,
    getNextQuestion,
    getCurrentQuestion,
    checkAnswer,
    getStats,
    resetSession
  };
})();
