"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const QUESTIONS = [
  {
    id: 1,
    question: "What type of craft do you practice?",
    placeholder: "e.g., Pottery, Weaving, Metalwork, Woodwork...",
    key: "craft_type"
  },
  {
    id: 2,
    question: "How long have you been practicing this craft?",
    placeholder: "e.g., 5 years, 10 years, Since childhood...",
    key: "experience"
  },
  {
    id: 3,
    question: "What is your primary location? (City, State)",
    placeholder: "e.g., Jaipur, Rajasthan",
    key: "location"
  },
  {
    id: 4,
    question: "What products do you typically create?",
    placeholder: "e.g., Decorative plates, Vases, Jewelry boxes...",
    key: "products"
  },
  {
    id: 5,
    question: "What tools or equipment do you currently have?",
    placeholder: "e.g., Potter's wheel, Kiln, Specific tools...",
    key: "tools"
  },
  {
    id: 6,
    question: "What materials or supplies do you need regularly?",
    placeholder: "e.g., Clay, Yarn, Metal sheets, Wood...",
    key: "supplies"
  },
  {
    id: 7,
    question: "What are your main challenges or goals?",
    placeholder: "e.g., Finding suppliers, Marketing, Pricing, Scaling...",
    key: "challenges"
  },
  {
    id: 8,
    question: "Tell us about your craft tradition or technique",
    placeholder: "e.g., Traditional method, Modern approach, Family legacy...",
    key: "tradition"
  }
];

interface QuestionnaireProps {
  onComplete: (answers: Record<string, string>) => void;
}

export function Questionnaire({ onComplete }: QuestionnaireProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [currentAnswer, setCurrentAnswer] = useState("");

  const handleNext = () => {
    if (currentAnswer.trim()) {
      const currentQuestion = QUESTIONS[currentIndex];
      setAnswers({ ...answers, [currentQuestion.key]: currentAnswer });
      
      if (currentIndex < QUESTIONS.length - 1) {
        setCurrentIndex(currentIndex + 1);
        setCurrentAnswer("");
      } else {
        // All questions answered
        const finalAnswers = { ...answers, [currentQuestion.key]: currentAnswer };
        onComplete(finalAnswers);
      }
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      const prevQuestion = QUESTIONS[currentIndex - 1];
      setCurrentAnswer(answers[prevQuestion.key] || "");
    }
  };

  const progress = ((currentIndex + 1) / QUESTIONS.length) * 100;
  const currentQuestion = QUESTIONS[currentIndex];

  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-black"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
          <p className="text-sm text-gray-500 mt-2 text-center">
            Question {currentIndex + 1} of {QUESTIONS.length}
          </p>
        </div>

        {/* Question Card */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentIndex}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="bg-white border-2 border-black p-8 rounded-lg shadow-lg"
          >
            <h2 className="text-2xl font-bold text-black mb-6">
              {currentQuestion.question}
            </h2>
            
            <input
              type="text"
              value={currentAnswer}
              onChange={(e) => setCurrentAnswer(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === "Enter" && currentAnswer.trim()) {
                  handleNext();
                }
              }}
              placeholder={currentQuestion.placeholder}
              className="w-full px-4 py-3 border-2 border-black rounded-lg focus:outline-none focus:ring-2 focus:ring-black text-black placeholder-gray-400"
              autoFocus
            />

            <div className="flex justify-between mt-6">
              <button
                onClick={handlePrevious}
                disabled={currentIndex === 0}
                className={`px-6 py-2 border-2 border-black rounded-lg font-semibold ${
                  currentIndex === 0
                    ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                    : "bg-white text-black hover:bg-black hover:text-white transition-colors"
                }`}
              >
                Previous
              </button>

              <button
                onClick={handleNext}
                disabled={!currentAnswer.trim()}
                className={`px-6 py-2 border-2 border-black rounded-lg font-semibold ${
                  !currentAnswer.trim()
                    ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                    : "bg-black text-white hover:bg-gray-800 transition-colors"
                }`}
              >
                {currentIndex === QUESTIONS.length - 1 ? "Complete" : "Next"}
              </button>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}







