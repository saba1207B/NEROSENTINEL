import Link from 'next/link';

const modules = [
  ['Overview', '/dashboard'], ['Climate', '/dashboard/climate'], ['Water', '/dashboard/water'],
  ['Risk map', '/dashboard/map'], ['Digital twin', '/dashboard/twin'], ['Scenarios', '/dashboard/simulator'],
  ['Warnings', '/dashboard/warnings'], ['Evidence copilot', '/dashboard/copilot'],
];

export function PlatformFooter() {
  return <footer className="dashboard-footer">
    <div className="dashboard-footer__grid">
      <div className="dashboard-footer__brand">
        <p className="dashboard-footer__title">NeroSentinel · Water and climate intelligence</p>
        <p className="max-w-xl text-sm leading-7">Transparent water-balance scenarios and evidence review for a synthetic Tamil Nadu pilot. Every result stays tied to its assumptions and provenance.</p>
      </div>
      <div className="dashboard-footer__links">
        <p className="dashboard-footer__title">Platform</p>
        {modules.slice(0, 4).map(([name, href]) => <Link key={href} href={href}>{name}</Link>)}
      </div>
      <div className="dashboard-footer__links">
        <p className="dashboard-footer__title">Explore</p>
        {modules.slice(4).map(([name, href]) => <Link key={href} href={href}>{name}</Link>)}
        <Link href="/dashboard/settings">Demo settings</Link>
      </div>
    </div>
    <div className="dashboard-footer__bottom"><span>© NeroSentinel</span><span>Synthetic pilot data · Decision support only · No operating action</span></div>
  </footer>;
}
