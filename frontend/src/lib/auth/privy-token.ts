let tokenGetter: (() => Promise<string | null>) | null = null;

export function setPrivyAccessTokenGetter(fn: () => Promise<string | null>) {
  tokenGetter = fn;
}

export async function getPrivyAccessToken(): Promise<string | null> {
  if (!tokenGetter) return null;
  try {
    return await tokenGetter();
  } catch {
    return null;
  }
}