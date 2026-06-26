'use client';

import { PrivyProvider, usePrivy } from '@privy-io/react-auth';
import { ReactNode, useEffect } from 'react';
import { setPrivyAccessTokenGetter } from '@/lib/auth/privy-token';

type Props = {
  children: ReactNode;
};

function PrivyTokenBridge({ children }: { children: ReactNode }) {
  const { getAccessToken } = usePrivy();

  useEffect(() => {
    setPrivyAccessTokenGetter(async () => {
      const token = await getAccessToken();
      return token ?? null;
    });

    return () => {
      setPrivyAccessTokenGetter(async () => null);
    };
  }, [getAccessToken]);

  return <>{children}</>;
}

export function PrivyAppProvider({ children }: Props) {
  const appId = process.env.NEXT_PUBLIC_PRIVY_APP_ID;

  if (!appId) {
    return <>{children}</>;
  }

  return (
    <PrivyProvider
      appId={appId}
      config={{
        appearance: {
          theme: 'dark',
          accentColor: '#7CFFB2',
          walletChainType: 'ethereum-only',
        },
        loginMethods: ['email', 'wallet'],
        embeddedWallets: {
          ethereum: {
            createOnLogin: 'off',
          },
        },
      }}
    >
      <PrivyTokenBridge>{children}</PrivyTokenBridge>
    </PrivyProvider>
  );
}