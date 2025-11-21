import axios from "axios";

const getHadithUrls = (bookName: string) => [
  `https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-${bookName}.min.json`,
  `https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-${bookName}.json`,
  `https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions/eng-${bookName}.min.json`
];

export const searchHadith = async (topic: string, hadithBook: string = "muslim") => {
  let hadithData = null;
  const HADITH_URLS = getHadithUrls(hadithBook);

  // Try fetching from URLs in order
  for (const url of HADITH_URLS) {
    try {
      const response = await axios.get(url);
      if (response.data && response.data.hadiths) {
        hadithData = response.data.hadiths;
        break;
      }
    } catch (error) {
      console.warn(`Failed to fetch Hadith from ${url}`, error);
    }
  }

  if (!hadithData) {
    return null;
  }

  // Filter for topic
  const relevantHadiths = hadithData.filter((h: any) => 
    h.text.toLowerCase().includes(topic.toLowerCase())
  );

  // Return a random one from the top matches or the first one
  if (relevantHadiths.length > 0) {
    return relevantHadiths[0]; // Simplified: just take the first one
  }

  return null;
};
