export type Theme = {
  bg: string
  primary: string
  primaryHover: string
  primaryShadow: string
  fore: string
  foreSecondary: string
  border: string
  labelColor: string
  /** CSS variable name for the display font (set by layout.tsx) */
  fontVar: string
  /** true for dark-background themes (restaurant/bar) */
  dark: boolean
}

const PALETTE: Record<string, Theme> = {
  // Warm artisan — cafes, gelato, casual food
  cafe: {
    bg: '#FFF7ED',
    primary: '#EA580C',
    primaryHover: '#C2410C',
    primaryShadow: 'rgba(234,88,12,0.25)',
    fore: '#1C0A00',
    foreSecondary: 'rgba(28,10,0,0.55)',
    border: '#FEE2C8',
    labelColor: 'rgba(234,88,12,0.6)',
    fontVar: '--font-artisan',
    dark: false,
  },
  // Rich dark — upscale restaurants, bars
  restaurant: {
    bg: '#1C0A00',
    primary: '#D97706',
    primaryHover: '#B45309',
    primaryShadow: 'rgba(217,119,6,0.35)',
    fore: '#FFF7ED',
    foreSecondary: 'rgba(255,247,237,0.55)',
    border: 'rgba(255,247,237,0.08)',
    labelColor: 'rgba(217,119,6,0.7)',
    fontVar: '--font-serif',
    dark: true,
  },
  // Soft elegance — hair salons, spas
  salon: {
    bg: '#FFF8FA',
    primary: '#BE185D',
    primaryHover: '#9D174D',
    primaryShadow: 'rgba(190,24,93,0.22)',
    fore: '#1A0611',
    foreSecondary: 'rgba(26,6,17,0.55)',
    border: '#FCE7F3',
    labelColor: 'rgba(190,24,93,0.55)',
    fontVar: '--font-elegant',
    dark: false,
  },
  // Quiet luxury — nail spas, beauty studios
  beauty: {
    bg: '#FDFCFF',
    primary: '#7C3AED',
    primaryHover: '#6D28D9',
    primaryShadow: 'rgba(124,58,237,0.22)',
    fore: '#120A1E',
    foreSecondary: 'rgba(18,10,30,0.55)',
    border: '#EDE9FE',
    labelColor: 'rgba(124,58,237,0.55)',
    fontVar: '--font-elegant',
    dark: false,
  },
  // Bold clean — gyms, fitness studios
  fitness: {
    bg: '#F8FAFC',
    primary: '#1E40AF',
    primaryHover: '#1E3A8A',
    primaryShadow: 'rgba(30,64,175,0.22)',
    fore: '#0F172A',
    foreSecondary: 'rgba(15,23,42,0.55)',
    border: '#DBEAFE',
    labelColor: 'rgba(30,64,175,0.55)',
    fontVar: '--font-grotesk',
    dark: false,
  },
  // Editorial natural — retail shops, boutiques
  retail: {
    bg: '#FAFAF8',
    primary: '#166534',
    primaryHover: '#14532D',
    primaryShadow: 'rgba(22,101,52,0.22)',
    fore: '#0D1F0D',
    foreSecondary: 'rgba(13,31,13,0.55)',
    border: '#D1FAE5',
    labelColor: 'rgba(22,101,52,0.55)',
    fontVar: '--font-serif',
    dark: false,
  },
  // Professional trust — service businesses, offices
  services: {
    bg: '#F8FAFF',
    primary: '#1D4ED8',
    primaryHover: '#1E40AF',
    primaryShadow: 'rgba(29,78,216,0.22)',
    fore: '#0D1229',
    foreSecondary: 'rgba(13,18,41,0.55)',
    border: '#DBEAFE',
    labelColor: 'rgba(29,78,216,0.55)',
    fontVar: '--font-grotesk',
    dark: false,
  },
}

// Map every Google/scraper category string to a theme key
const CATEGORY_MAP: Record<string, string> = {
  cafe: 'cafe',
  coffee: 'cafe',
  bakery: 'cafe',
  gelato: 'cafe',
  food: 'cafe',
  restaurant: 'restaurant',
  bar: 'restaurant',
  dining: 'restaurant',
  salon: 'salon',
  hair: 'salon',
  spa: 'salon',
  barbershop: 'salon',
  beauty: 'beauty',
  nail: 'beauty',
  nails: 'beauty',
  skincare: 'beauty',
  fitness: 'fitness',
  gym: 'fitness',
  yoga: 'fitness',
  pilates: 'fitness',
  retail: 'retail',
  shop: 'retail',
  boutique: 'retail',
  store: 'retail',
  vintage: 'retail',
  services: 'services',
  repair: 'services',
  cleaning: 'services',
  auto: 'services',
}

export function getTheme(category: string): Theme {
  const key = CATEGORY_MAP[category?.toLowerCase()] ?? 'services'
  return PALETTE[key]
}

// hero overlay: fade bg color over photo
export function heroOverlay(theme: Theme): string {
  const hex = theme.bg
  return `linear-gradient(to top, ${hex} 0%, ${hex}b3 40%, ${hex}1a 100%)`
}

// no-photo background gradient per category
export const NO_PHOTO_GRADIENTS: Record<string, string> = {
  cafe:       'linear-gradient(135deg, #FEF3C7 0%, #FFF7ED 50%, #FFECD5 100%)',
  restaurant: 'linear-gradient(135deg, #292209 0%, #1C0A00 50%, #2C1002 100%)',
  salon:      'linear-gradient(135deg, #FCE7F3 0%, #FFF8FA 50%, #FDE8F4 100%)',
  beauty:     'linear-gradient(135deg, #EDE9FE 0%, #FDFCFF 50%, #F5F0FF 100%)',
  fitness:    'linear-gradient(135deg, #DBEAFE 0%, #F8FAFC 50%, #E0E7FF 100%)',
  retail:     'linear-gradient(135deg, #D1FAE5 0%, #FAFAF8 50%, #DCFCE7 100%)',
  services:   'linear-gradient(135deg, #DBEAFE 0%, #F8FAFF 50%, #E0E7FF 100%)',
}

export function noPhotoGradient(category: string): string {
  const key = CATEGORY_MAP[category?.toLowerCase()] ?? 'services'
  return NO_PHOTO_GRADIENTS[key]
}
