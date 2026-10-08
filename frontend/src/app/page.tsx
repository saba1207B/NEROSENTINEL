import type { CSSProperties } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { ArrowDownRight, ArrowUpRight } from 'lucide-react';
import { FloatingClimateArt } from '@/components/FloatingClimateArt';
import { PinnedEvidenceStory } from '@/components/PinnedEvidenceStory';
import { RevealObserver } from '@/components/RevealObserver';

const features = [
  { number: '01', tag: 'Climate signals', title: 'Climate intelligence', body: 'Read the synthetic ENSO screen beside declared rainfall baselines and uncertainty boundaries.', href: '/dashboard/climate', image: '/forest/climate.svg', alt: 'Earth toned rings and a climate signal curve' },
  { number: '02', tag: 'Water accounting', title: 'Water resources', body: 'Inspect modeled reservoir storage, demand, releases and mass-balance diagnostics in MCM.', href: '/dashboard/water', image: '/forest/reservoir.svg', alt: 'Layered sage and forest reservoir illustration' },
  { number: '03', tag: 'Place and context', title: 'Risk explorer', body: 'Explore one explicitly synthetic Coimbatore pilot point with its geometry limitations in view.', href: '/dashboard/map', image: '/forest/field.svg', alt: 'Terraced hills drawn with forest green contour lines' },
  { number: '04', tag: 'Model boundaries', title: 'Water digital twin', body: 'Follow a lumped monthly water balance with visible inflow, demand and storage assumptions.', href: '/dashboard/twin', image: '/forest/reservoir.svg', alt: 'Illustration of layered reservoir storage' },
  { number: '05', tag: 'Sensitivity analysis', title: 'Scenario simulator', body: 'Compare backend-run rainfall and temperature cases. Scenarios are not forecasts or releases.', href: '/dashboard/simulator', image: '/forest/climate.svg', alt: 'Earth toned chart representing alternate climate cases' },
  { number: '06', tag: 'Human review', title: 'Early warnings', body: 'Review local alert records and keep acknowledgement behind authority-scoped access.', href: '/dashboard/warnings', image: '/forest/field.svg', alt: 'Forest green agricultural contour pattern' },
];

function HeadlineLine({ text, line }: { text: string; line: number }) {
  return <span className="home-hero__line" aria-hidden="true">{Array.from(text).map((letter, index) => <span className="home-hero__letter" key={`${letter}-${index}`} style={{ '--letter-index': index, animationDelay: `${line * 0.22 + index * 0.05}s` } as CSSProperties}>{letter === ' ' ? '\u00a0' : letter}</span>)}</span>;
}

export default function Home() {
  return <div className="home-shell">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <header className="site-nav">
      <Link href="/" className="dashboard-brand" aria-label="NeroSentinel home"><Image className="dashboard-brand__mark" src="/nerosentinel-mark.svg" width={40} height={40} alt="" priority /><span className="dashboard-brand__name">— NeroSentinel</span></Link>
      <nav className="site-nav__links" aria-label="Site sections"><Link href="#platform">Platform</Link><Link href="#method">Method</Link><Link href="#limits">Data limits</Link></nav>
      <Link className="site-nav__action" href="/dashboard">Open command center <ArrowUpRight size={14} aria-hidden="true" /></Link>
    </header>

    <main id="main-content">
      <section className="home-hero" aria-labelledby="home-title">
        <div className="home-hero__grid">
          <div className="home-hero__copy">
            <p className="home-hero__eyebrow">Intelligent Water Intelligence &amp; Drought Resilience Platform</p>
            <h1 id="home-title" className="home-hero__title" aria-label="Water. Climate. Intelligence."><HeadlineLine text="Water." line={0} /><HeadlineLine text="Climate." line={1} /><HeadlineLine text="Intelligence." line={2} /></h1>
            <p className="home-hero__description">Trace water-balance scenarios from their assumptions to their limits. NeroSentinel brings climate context, reservoir modeling and evidence review into one careful workspace.</p>
            <div className="home-hero__actions"><Link href="/dashboard">Explore the platform <ArrowUpRight size={15} aria-hidden="true" /></Link><Link href="/dashboard/simulator">Test a scenario <ArrowUpRight size={15} aria-hidden="true" /></Link></div>
          </div>
          <FloatingClimateArt />
        </div>
        <div className="home-hero__footnote"><span>Coimbatore · synthetic research pilot</span><span>Decision support · no automatic operations</span></div>
      </section>

      <section id="platform" className="capabilities" aria-labelledby="capabilities-title">
        <div className="capabilities__inner">
          <div className="capabilities__heading"><div><p className="editorial-label">One connected evidence workflow</p><h2 id="capabilities-title">Read the whole system.</h2></div><Link className="capabilities__all" href="/dashboard" aria-label="Explore all NeroSentinel modules">All modules<br /><ArrowDownRight size={21} aria-hidden="true" /></Link></div>
          <div className="feature-grid">{features.map((feature) => <article className="feature-card" key={feature.number}>
            <div className="feature-card__media"><Image src={feature.image} alt={feature.alt} fill sizes="(max-width: 680px) 90vw, (max-width: 900px) 45vw, 30vw" /><div className="feature-card__overlay"><Link href={feature.href}>Explore module <ArrowUpRight size={14} aria-hidden="true" /></Link></div></div>
            <div className="feature-card__copy"><span>{feature.number} / {feature.tag}</span><h3>{feature.title}</h3><p>{feature.body}</p></div>
          </article>)}</div>
        </div>
      </section>

      <div id="method"><PinnedEvidenceStory /></div>
      <section id="limits" className="home-limits"><p className="editorial-label">Read the evidence with care</p><h2>Every number has a boundary.</h2><p>The bundled pilot observations are synthetic. Scores are screening indices, scenario curves are model outputs, and map geometry is illustrative. There is no live telemetry, calibrated forecast skill, public warning delivery, or automatic water operation.</p><Link href="/dashboard/settings">Inspect sources and demo access <ArrowUpRight size={14} aria-hidden="true" /></Link></section>
    </main>
    <RevealObserver />

    <footer className="home-footer">
      <div className="home-footer__grid">
        <div className="home-footer__about"><h2>NeroSentinel</h2><p>Transparent water accounting and climate context for reviewable decisions. Built around a synthetic pilot and explicit uncertainty.</p></div>
        <div className="home-footer__group"><h3>Platform</h3><Link href="/dashboard">Overview</Link><Link href="/dashboard/climate">Climate intelligence</Link><Link href="/dashboard/water">Water resources</Link><Link href="/dashboard/map">Risk explorer</Link></div>
        <div className="home-footer__group"><h3>Research tools</h3><Link href="/dashboard/twin">Digital twin</Link><Link href="/dashboard/simulator">Scenario simulator</Link><Link href="/dashboard/warnings">Early warnings</Link><Link href="/dashboard/copilot">Evidence assistant</Link></div>
      </div>
      <div className="home-footer__bottom"><span>© NeroSentinel</span><span>Synthetic pilot only · Human review required</span><Link href="/dashboard/settings">Demo settings</Link></div>
    </footer>
  </div>;
}
