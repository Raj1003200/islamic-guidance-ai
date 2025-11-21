import axios from "axios";

export const searchQuran = async (keyword: string) => {
  try {
    const url = `https://api.alquran.cloud/v1/search/${keyword}/all/en`;
    const response = await axios.get(url);
    
    if (response.data && response.data.data && response.data.data.matches) {
      // Return top 3 matches
      return response.data.data.matches.slice(0, 3).map((match: any) => ({
        text: match.text,
        surah: match.surah.englishName,
        number: match.number,
        numberInSurah: match.numberInSurah
      }));
    }
    return [];
  } catch (error) {
    console.error("Quran Search Error:", error);
    return [];
  }
};
