'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const items = [
  ['Dashboard', '/dashboard'],
  ['Events', '/events'],
  ['Artists', '/artists'],
  ['Chat', '/chat'],
  ['Wallet', '/wallet'],
  ['Risk', '/risk'],
  ['Marketplace', '/market'],
  ['Support', '/support/enquiry'],
  ['Rewards', '/rewards'],
  ['Profile', '/profile'],
  ['Following', '/artists/following'],
  ['Notifications', '/notifications'],
];

export function AppSidebar() {
  const pathname = usePathname();
  return (
    <aside className="sidebar">
      <div style={{ fontWeight: 800, fontSize: 22, marginBottom: 20 }}>Backstage Pass</div>
      {items.map(([label, href]) => (
        <Link key={href} href={href} className={`nav-item ${pathname.startsWith(href) ? 'active' : ''}`}>
          {label}
        </Link>
      ))}
    </aside>
  );
}