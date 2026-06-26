import './globals.css';
import type { Metadata } from 'next';
import { PrivyAppProvider } from '@/components/providers/PrivyAppProvider';

export const metadata: Metadata = {
  title: 'Backstage Pass',
  description: 'Phase 2 Web3-ready prototype frontend for Backstage Pass',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <PrivyAppProvider>{children}</PrivyAppProvider>
      </body>
    </html>
  );
}