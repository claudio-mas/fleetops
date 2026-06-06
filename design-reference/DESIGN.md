---
name: FleetOps Design System
colors:
  surface: '#f6fafb'
  surface-dim: '#d7dbdc'
  surface-bright: '#f6fafb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f4f5'
  surface-container: '#ebeef0'
  surface-container-high: '#e5e9ea'
  surface-container-highest: '#dfe3e4'
  on-surface: '#181c1d'
  on-surface-variant: '#3e494b'
  inverse-surface: '#2c3132'
  inverse-on-surface: '#edf1f2'
  outline: '#6e797c'
  outline-variant: '#bdc8cb'
  surface-tint: '#006876'
  primary: '#006673'
  on-primary: '#ffffff'
  primary-container: '#008092'
  on-primary-container: '#f8fdff'
  inverse-primary: '#73d4e8'
  secondary: '#655c5c'
  on-secondary: '#ffffff'
  secondary-container: '#e9dddc'
  on-secondary-container: '#696160'
  tertiary: '#5e5f00'
  on-tertiary: '#ffffff'
  tertiary-container: '#787900'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#a1efff'
  primary-fixed-dim: '#73d4e8'
  on-primary-fixed: '#001f25'
  on-primary-fixed-variant: '#004e5a'
  secondary-fixed: '#ece0df'
  secondary-fixed-dim: '#cfc4c3'
  on-secondary-fixed: '#201a1a'
  on-secondary-fixed-variant: '#4d4545'
  tertiary-fixed: '#e8ea41'
  tertiary-fixed-dim: '#cbcd22'
  on-tertiary-fixed: '#1c1d00'
  on-tertiary-fixed-variant: '#494a00'
  background: '#f6fafb'
  on-background: '#181c1d'
  surface-variant: '#dfe3e4'
typography:
  display:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
  body-base:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: '1.4'
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  container-margin: 24px
  gutter: 16px
---

## Brand & Style
The design system is engineered for efficiency and reliability within the Brazilian industrial and logistics sector. It balances an **Industrial-Professional** aesthetic with high-density information architecture, ensuring that fleet managers can oversee complex operations with minimal friction.

The visual narrative is grounded in a "Dark Mode Sidebar" contrast against "Cream Industrial Surfaces," evoking the feel of high-end machinery interfaces. The style leverages **Corporate Modernism** with a slight **Tactile** edge through subtle shadows and deliberate color-coded status indicators. The goal is to feel robust, precise, and utilitarian while maintaining the polished finish of a premium B2B SaaS platform.

## Colors
The palette is built on high-contrast functional zones. 
- **Ink (#0F0A0A)** anchors the system, used for navigation sidebars and primary text to provide an authoritative structure.
- **Cream (#F5EFED)** serves as the canvas, reducing eye strain during long periods of data entry compared to pure white.
- **Teal (#2292A4)** is the action driver, reserved for primary CTAs, active states, and focus indicators.
- **Volt (#BDBF09)** and **Amber (#D96C06)** act as utility accents for status tracking—Volt for active/positive progression and Amber for critical warnings or overdue maintenance alerts.

## Typography
This design system utilizes **Inter** for its neutral, geometric clarity. To maintain a professional hierarchy in data-dense views:
- **Headings:** Use Semibold weight in pure Ink to provide clear section anchors.
- **Body:** Set at 14px with 85% opacity to soften the reading experience and create a subtle visual distinction from headings.
- **Labels:** Small, uppercase, and tracked (0.05em) in Teal. These are used for secondary metadata, table headers, and technical captions.

## Layout & Spacing
The layout follows a **Fixed Grid** model for the main content area, paired with a persistent **Left Sidebar Navigation** (width: 260px). 

The spacing rhythm is **compact** to accommodate the high volume of data inherent in fleet management. 
- **Desktop:** 12-column grid, 16px gutters, 24px outer margins.
- **Tablet:** 8-column grid, 16px gutters.
- **Mobile:** 4-column grid, 12px gutters.

Information density is prioritized; vertical padding in tables and lists is kept to 8px or 12px to maximize "at-a-glance" visibility of equipment status.

## Elevation & Depth
Depth is handled through **Tonal Layering** and **Ambient Shadows**. 
- **Layer 0 (Background):** Cream (#F5EFED).
- **Layer 1 (Cards/Tables):** White surfaces with a very subtle 1px border (#E5E7EB) and a soft shadow (Ink at 5% opacity, 4px blur).
- **Layer 2 (Popovers/Modals):** White surfaces with a more pronounced 12px blur shadow at 8% opacity.
- **Sidebar:** Ink (#0F0A0A) background with no shadow, creating a structural "cut-out" effect on the left side of the screen.

## Shapes
The shape language is strictly **Soft-Industrial**. 
- **Primary Elements:** Buttons, cards, and input fields use a **6px (0.375rem)** corner radius.
- **Secondary Elements:** Badges, tags, and small status indicators use a tighter **4px (0.25rem)** radius to maintain a crisp, technical look even at small scales.
- **Active States:** Focus rings are 2px solid Teal with a 2px offset.

## Components
- **Buttons:** Primary buttons are Solid Teal with White text. Secondary buttons are Ghost style with Ink borders or Amber text for destructive/warning actions.
- **Status Badges:** Compact 4px rounded tags. 
    - *Active:* Volt background, Dark Ink text.
    - *Warning/Overdue:* Amber background, White text.
    - *Completed:* Teal background, White text.
    - *Inactive:* Light Grey (Ink 10% fill), Ink 50% text.
- **Inputs:** Cream background with a subtle border that shifts to Teal on focus. Labels are always positioned above the input field in `label-caps` style.
- **Data Tables:** Highly condensed. Row hover states use a light tint of Teal (5% opacity).
- **Icons:** Lucide icons, 18px stroke width for consistency. Icons in the sidebar are 20px; in-line icons are 16px.
- **Cards:** White fill, 6px radius, subtle shadow. Used to group equipment specs or maintenance logs.