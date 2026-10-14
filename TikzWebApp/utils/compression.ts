import { deflateSync, inflateSync, strToU8, strFromU8 } from 'fflate';

/**
 * Encodes a Uint8Array to a Base64URL string.
 */
function bytesToBase64Url(bytes: Uint8Array): string {
  const binString = Array.from(bytes, (byte) => String.fromCharCode(byte)).join('');
  const base64 = btoa(binString);
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/**
 * Decodes a Base64URL string to a Uint8Array.
 */
function base64UrlToBytes(base64Url: string): Uint8Array {
  let base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  // Pad with '='
  while (base64.length % 4) {
    base64 += '=';
  }
  const binString = atob(base64);
  const bytes = new Uint8Array(binString.length);
  for (let i = 0; i < binString.length; i++) {
    bytes[i] = binString.charCodeAt(i);
  }
  return bytes;
}

export function compressCode(code: string): string {
  const bytes = strToU8(code);
  const compressed = deflateSync(bytes, { level: 9 });
  return bytesToBase64Url(compressed);
}

export function decompressCode(compressedStr: string): string | null {
  try {
    const bytes = base64UrlToBytes(compressedStr);
    const decompressed = inflateSync(bytes);
    return strFromU8(decompressed);
  } catch (e) {
    console.error("Failed to decompress code with fflate:", e);
    return null;
  }
}
