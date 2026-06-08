import type { Theme } from '../themes'

type Service = { name: string; price: string }

type Props = {
  services: Service[]
  theme: Theme
  sectionLabel?: string
}

export default function ServicesSection({ services, theme, sectionLabel = 'Services' }: Props) {
  if (!services || services.length === 0) return null

  return (
    <section
      className="px-6 py-20 md:px-12 md:py-28"
      style={{ borderTop: `1px solid ${theme.border}` }}
    >
      <div className="max-w-5xl mx-auto">
        <p
          className="font-mono text-[10px] tracking-[0.2em] uppercase mb-10"
          style={{ color: theme.labelColor }}
        >
          {sectionLabel}
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-px"
          style={{ background: theme.border }}>
          {services.map((svc, i) => (
            <div
              key={i}
              className="flex items-center justify-between px-5 py-4"
              style={{ background: theme.bg }}
            >
              <span
                className="font-sans text-sm font-medium"
                style={{ color: theme.fore }}
              >
                {svc.name}
              </span>
              <span
                className="font-mono text-[13px] ml-4 shrink-0"
                style={{ color: theme.primary }}
              >
                {svc.price}
              </span>
            </div>
          ))}
        </div>

        <p
          className="font-mono text-[10px] tracking-widest uppercase mt-6"
          style={{ color: theme.foreSecondary }}
        >
          Prices may vary · Call for details
        </p>
      </div>
    </section>
  )
}
