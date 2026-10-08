'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import Image from 'next/image';
import { Activity, AlertTriangle, Database, Globe2, LayoutDashboard, Map, Menu, MessageSquareText, Settings, Waves, X } from 'lucide-react';
import { apiGet, type Alert } from '@/lib/api-client';
import { PlatformFooter } from '@/components/PlatformFooter';
import { RevealObserver } from '@/components/RevealObserver';

const navigation = [
  { name: 'Overview', shortName: 'Overview', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Climate Intelligence', shortName: 'Climate', href: '/dashboard/climate', icon: Globe2 },
  { name: 'Water Resources', shortName: 'Water', href: '/dashboard/water', icon: Waves },
  { name: 'Geospatial Risk Explorer', shortName: 'Map', href: '/dashboard/map', icon: Map },
  { name: 'Water Digital Twin', shortName: 'Twin', href: '/dashboard/twin', icon: Database },
  { name: 'Scenario Simulator', shortName: 'Scenarios', href: '/dashboard/simulator', icon: Activity },
  { name: 'Early Warning Center', shortName: 'Warnings', href: '/dashboard/warnings', icon: AlertTriangle },
  { name: 'AI Copilot', shortName: 'Copilot', href: '/dashboard/copilot', icon: MessageSquareText },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const alerts = useQuery({ queryKey: ['alerts'], queryFn: () => apiGet<{ items: Alert[] }>('/alerts') });
  const alertCount = alerts.data?.data.items.length ?? 0;

  useEffect(() => {
    if (!menuOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') setMenuOpen(false); };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [menuOpen]);

  function links(mobile = false) {
    return navigation.map((item) => {
      const active = pathname === item.href;
      const Icon = item.icon;
      return <Link key={item.href} href={item.href} aria-current={active ? 'page' : undefined} aria-label={mobile ? item.name : undefined} className="dashboard-link" onClick={() => setMenuOpen(false)}>
        <Icon aria-hidden="true" size={15} strokeWidth={1.8} />
        <span>{mobile ? item.name : item.shortName}</span>
        {item.href === '/dashboard/warnings' && alertCount > 0 && <span className="dashboard-alert-count" aria-label={`${alertCount} local alert records`}>{alertCount}</span>}
      </Link>;
    });
  }

  return <div className="dashboard-shell min-h-screen">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <header className="dashboard-nav" aria-label="NeroSentinel navigation">
      <Link href="/dashboard" className="dashboard-brand" aria-label="NeroSentinel overview">
        <Image className="dashboard-brand__mark" src="/nerosentinel-mark.svg" width={40} height={40} alt="" priority />
        <span className="dashboard-brand__name">NeroSentinel</span>
      </Link>
      <nav className="dashboard-links" aria-label="Platform modules">{links()}</nav>
      <div className="dashboard-nav__tools">
        <Link href="/dashboard/settings" className="nav-icon-button" aria-label="Open demo settings" title="Demo settings"><Settings size={18} aria-hidden="true" /></Link>
        <button type="button" className="nav-menu-button" aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'} aria-expanded={menuOpen} aria-controls="dashboard-mobile-menu" onClick={() => setMenuOpen((open) => !open)}>
          {menuOpen ? <X size={19} aria-hidden="true" /> : <Menu size={19} aria-hidden="true" />}
        </button>
      </div>
      <span className="dashboard-nav__pilot">Coimbatore · synthetic pilot</span>
    </header>
    {menuOpen && <nav id="dashboard-mobile-menu" className="dashboard-mobile-menu" aria-label="Platform modules">{links(true)}</nav>}
    <main id="main-content" className="min-w-0">
      <div className="dashboard-content">{children}</div>
    </main>
    <RevealObserver />
    <PlatformFooter />
  </div>;
}
