import express, { Request, Response } from "express";
import { validateAndExtract, synthesizeResponse } from "../services/aiService";
import { searchQuran } from "../services/quranService";
import { searchHadith } from "../services/hadithService";

const router = express.Router();

router.post("/", async (req: Request, res: Response): Promise<void> => {
  try {
    const { problem, hadithBook = "muslim" } = req.body;

    if (!problem) {
      res.status(400).json({ error: "Problem description is required" });
      return;
    }

    // Step 1: AI Gatekeeper
    const validation = await validateAndExtract(problem);

    if (!validation.isValid) {
      res.status(400).json({ 
        error: "Please enter a genuine life problem seeking Islamic guidance.",
        details: validation.error || "Input validation failed"
      });
      return;
    }

    // Step 2 & 3: Parallel Search
    const [quranResults, hadithResult] = await Promise.all([
      validation.quranKeyword ? searchQuran(validation.quranKeyword) : Promise.resolve([]),
      validation.hadithTopic ? searchHadith(validation.hadithTopic, hadithBook) : Promise.resolve(null)
    ]);

    // Step 4: AI Synthesis
    const advice = await synthesizeResponse(problem, quranResults, hadithResult);

    res.json({
      problem,
      validation,
      sources: {
        quran: quranResults,
        hadith: hadithResult
      },
      advice
    });

  } catch (error) {
    console.error("Guidance API Error:", error);
    res.status(500).json({ error: "Internal Server Error" });
  }
});

export default router;
