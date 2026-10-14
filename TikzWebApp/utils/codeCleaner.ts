import { extractTikzCodeFromFull } from './latexBuilder';

export const cleanBoilerplate = (
  code: string,
): { cleanedCode: string; wasRemoved: boolean } => {
  const extracted = extractTikzCodeFromFull(code);
  if (extracted !== code) {
    return { cleanedCode: extracted, wasRemoved: true };
  }
  return { cleanedCode: code, wasRemoved: false };
};
