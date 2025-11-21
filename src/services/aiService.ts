import { GoogleGenerativeAI } from "@google/generative-ai";
import dotenv from "dotenv";

dotenv.config();

const apiKey = process.env.GEMINI_API_KEY;
if (!apiKey) {
  console.error("GEMINI_API_KEY is not set in .env file");
}

const genAI = new GoogleGenerativeAI(apiKey || "");
const model = genAI.getGenerativeModel({ model: "gemini-3-pro" });

export interface ValidationResult {
  isValid: boolean;
  quranKeyword?: string;
  hadithTopic?: string;
  error?: string;
}

export const validateAndExtract = async (problem: string): Promise<ValidationResult> => {
  const prompt = `
    Analyze the following user problem: "${problem}".
    
    Task 1: Determine if this is a genuine life problem asking for guidance (e.g., "I have money problems", "I am restless") or irrelevant nonsense (e.g., "How to bake a cake", "Write code for me").
    
    Task 2: If valid, interpret the intent and extract:
    - Quran Keyword: ONE English word best suited for a Quran search (e.g., "jobless" -> "Sustenance" or "Bounty").
    - Hadith Topic: ONE English topic for searching Hadith text (e.g., "sad" -> "Anxiety").
    
    Output JSON ONLY:
    {
      "isValid": boolean,
      "quranKeyword": "string" (or null if invalid),
      "hadithTopic": "string" (or null if invalid),
      "reason": "string" (short explanation if invalid)
    }
  `;

  try {
    const result = await model.generateContent(prompt);
    const response = await result.response;
    const text = response.text();
    // Clean up markdown code blocks if present
    const jsonStr = text.replace(/```json/g, "").replace(/```/g, "").trim();
    return JSON.parse(jsonStr);
  } catch (error) {
    console.error("AI Validation Error:", error);
    return { isValid: false, error: "AI service unavailable" };
  }
};

export const synthesizeResponse = async (problem: string, quranVerses: any[], hadith: any): Promise<string> => {
  const prompt = `
    The user has this problem: '${problem}'.
    
    I found these Quran verses: ${JSON.stringify(quranVerses)}.
    
    And this Hadith: ${JSON.stringify(hadith)}.
    
    Act as a compassionate advisor. Explain HOW these specific texts apply to their situation. Do not just list them; connect the dots.
    Provide a comforting and actionable response.
  `;

  try {
    const result = await model.generateContent(prompt);
    const response = await result.response;
    return response.text();
  } catch (error) {
    console.error("AI Synthesis Error:", error);
    return "I'm sorry, I am unable to generate a response at this time.";
  }
};
