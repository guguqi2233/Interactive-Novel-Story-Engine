export function countWordsFast(text?: string | null): number {
  const value = text ?? "";
  let count = 0;
  let inWord = false;

  for (let index = 0; index < value.length; index += 1) {
    const code = value.charCodeAt(index);
    const whitespace = code <= 32 || code === 160 || code === 0x3000 || (code >= 0x2000 && code <= 0x200a) || code === 0x2028 || code === 0x2029 || code === 0xfeff;
    if (whitespace) {
      inWord = false;
    } else if (!inWord) {
      count += 1;
      inWord = true;
    }
  }

  return count;
}
