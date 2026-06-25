const QuestionLoader = (function () {
  function loadQuestions(url) {
    return fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`questions.json の読み込みに失敗しました: ${response.status}`);
        }
        return response.json();
      })
      .then((questions) => {
        const validation = validateQuestions(questions);
        if (!validation.valid) {
          throw new Error(`問題データの形式が不正です: ${validation.errors.join("; ")}`);
        }
        return questions;
      });
  }

  function validateQuestions(questions) {
    const errors = [];
    if (!Array.isArray(questions) || questions.length === 0) {
      errors.push("questions.json が空か配列ではありません");
      return { valid: false, errors };
    }

    questions.forEach((item, index) => {
      if (typeof item !== "object" || item === null) {
        errors.push(`項目 ${index + 1} がオブジェクトではありません`);
        return;
      }
      const required = ["id", "category", "difficulty", "question", "choices", "answerIndex", "explanation"];
      required.forEach((key) => {
        if (item[key] === undefined || item[key] === null || item[key] === "") {
          errors.push(`ID ${item.id || index + 1}: ${key} が指定されていません`);
        }
      });
      if (!Array.isArray(item.choices) || item.choices.length < 5 || item.choices.length > 8) {
        errors.push(`ID ${item.id || index + 1}: choices は 5〜8 個である必要があります`);
      }
      if (typeof item.answerIndex !== "number" || item.answerIndex < 0 || item.answerIndex >= (item.choices || []).length) {
        errors.push(`ID ${item.id || index + 1}: answerIndex が choices の範囲外です`);
      }
      if (!QuizConstants.categories.includes(item.category)) {
        errors.push(`ID ${item.id || index + 1}: category が定義済みの分野と一致しません (${item.category})`);
      }
      if (typeof item.difficulty !== "number" || !(item.difficulty in QuizConstants.difficultyLabels)) {
        errors.push(`ID ${item.id || index + 1}: difficulty が 1〜5 の数値ではありません`);
      }
    });

    if (errors.length > 0) {
      console.error("問題データのバリデーションエラー", errors);
    }
    return { valid: errors.length === 0, errors };
  }

  return {
    loadQuestions,
    validateQuestions
  };
})();
